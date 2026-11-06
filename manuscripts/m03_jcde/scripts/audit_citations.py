from __future__ import annotations

import argparse
import json
import os
import re
import time
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from pathlib import Path

import bibtexparser
import requests


USER_AGENT = "M03-JCDE-reference-audit/1.0 (mailto:appamm94@gmail.com)"
ARXIV_NS = {"atom": "http://www.w3.org/2005/Atom"}


def normalise_title(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = re.sub(r"[{}\\]", "", value)
    value = re.sub(r"[^a-z0-9]+", " ", value.lower())
    return " ".join(value.split())


def title_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, normalise_title(left), normalise_title(right)).ratio()


def cited_keys(tex: str) -> list[str]:
    keys: set[str] = set()
    for match in re.finditer(r"\\(?:paren|text|auto|foot|smart)?cite\w*\s*(?:\[[^\]]*\]\s*)*\{([^}]+)\}", tex):
        keys.update(key.strip() for key in match.group(1).split(",") if key.strip())
    return sorted(keys)


def request_json(
    session: requests.Session,
    method: str,
    url: str,
    *,
    attempts: int = 3,
    **kwargs,
):
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            response = session.request(method, url, timeout=40, **kwargs)
            if response.status_code == 429:
                time.sleep(2 ** (attempt + 1))
                continue
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Request failed after {attempts} attempts: {url}: {last_error}")


def fetch_semantic_scholar(
    session: requests.Session, entries: list[dict[str, str]]
) -> dict[str, dict]:
    ids: list[str] = []
    index: dict[str, str] = {}
    for entry in entries:
        key = entry["ID"]
        if entry.get("doi"):
            paper_id = f"DOI:{entry['doi']}"
        elif entry.get("eprint"):
            paper_id = f"ARXIV:{entry['eprint']}"
        else:
            continue
        ids.append(paper_id)
        index[paper_id] = key

    headers = {}
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key
    fields = "title,year,authors,externalIds,venue,url"
    url = f"https://api.semanticscholar.org/graph/v1/paper/batch?fields={fields}"
    payload = request_json(session, "POST", url, json={"ids": ids}, headers=headers)
    results: dict[str, dict] = {}
    for paper_id, paper in zip(ids, payload):
        if paper:
            results[index[paper_id]] = paper
    return results


def fetch_crossref(
    session: requests.Session, entries: list[dict[str, str]]
) -> dict[str, dict]:
    results: dict[str, dict] = {}
    for entry in entries:
        doi = entry.get("doi")
        if not doi:
            continue
        url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
        try:
            payload = request_json(session, "GET", url)
            results[entry["ID"]] = payload["message"]
        except RuntimeError:
            continue
        time.sleep(0.1)
    return results


def fetch_arxiv(
    session: requests.Session, entries: list[dict[str, str]]
) -> dict[str, dict]:
    id_to_key = {
        entry["eprint"]: entry["ID"] for entry in entries if entry.get("eprint")
    }
    if not id_to_key:
        return {}
    url = (
        "https://export.arxiv.org/api/query?id_list="
        + ",".join(id_to_key)
        + f"&max_results={len(id_to_key)}"
    )
    try:
        response = session.get(url, timeout=60)
        response.raise_for_status()
    except requests.RequestException:
        return {}

    root = ET.fromstring(response.text)
    results: dict[str, dict] = {}
    for item in root.findall("atom:entry", ARXIV_NS):
        identifier = (item.findtext("atom:id", default="", namespaces=ARXIV_NS)
                      .rsplit("/", 1)[-1]
                      .split("v", 1)[0])
        key = id_to_key.get(identifier)
        if not key:
            continue
        results[key] = {
            "title": " ".join(
                item.findtext("atom:title", default="", namespaces=ARXIV_NS).split()
            ),
            "published": item.findtext(
                "atom:published", default="", namespaces=ARXIV_NS
            ),
            "id": identifier,
        }
    return results


def source_record(name: str, expected_title: str, title: str, year) -> dict:
    score = title_similarity(expected_title, title)
    return {
        "source": name,
        "title": title,
        "year": year,
        "title_similarity": round(score, 4),
        "title_match": score >= 0.86,
    }


def audit(tex_path: Path, bib_path: Path) -> dict:
    tex = tex_path.read_text(encoding="utf-8")
    keys = cited_keys(tex)
    with bib_path.open(encoding="utf-8") as handle:
        database = bibtexparser.load(handle)
    all_entries = {entry["ID"]: entry for entry in database.entries}
    missing = [key for key in keys if key not in all_entries]
    entries = [all_entries[key] for key in keys if key in all_entries]

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})

    errors: dict[str, str] = {}
    try:
        s2 = fetch_semantic_scholar(session, entries)
    except RuntimeError as exc:
        s2 = {}
        errors["semantic_scholar"] = str(exc)
    crossref = fetch_crossref(session, entries)
    arxiv = fetch_arxiv(session, entries)

    records: list[dict] = []
    for entry in entries:
        key = entry["ID"]
        expected_title = entry.get("title", "")
        sources: list[dict] = []

        if key in s2:
            paper = s2[key]
            sources.append(
                source_record(
                    "Semantic Scholar",
                    expected_title,
                    paper.get("title", ""),
                    paper.get("year"),
                )
            )
        if key in crossref:
            item = crossref[key]
            title = (item.get("title") or [""])[0]
            year_parts = (
                item.get("published-print", item.get("published-online", {}))
                .get("date-parts", [[None]])
            )
            year = year_parts[0][0] if year_parts and year_parts[0] else None
            sources.append(source_record("Crossref", expected_title, title, year))
        if key in arxiv:
            item = arxiv[key]
            year = item["published"][:4] if item["published"] else None
            sources.append(
                source_record("arXiv", expected_title, item["title"], year)
            )

        matching_sources = [source for source in sources if source["title_match"]]
        if len(matching_sources) >= 2:
            status = "verified_two_sources"
        elif len(matching_sources) == 1:
            status = "verified_one_source"
        else:
            status = "manual_review"

        records.append(
            {
                "key": key,
                "bib_title": expected_title,
                "bib_year": entry.get("year"),
                "doi": entry.get("doi"),
                "arxiv": entry.get("eprint"),
                "status": status,
                "sources": sources,
            }
        )

    return {
        "tex": str(tex_path),
        "bib": str(bib_path),
        "cited_key_count": len(keys),
        "bibliography_entry_count": len(all_entries),
        "missing_bib_keys": missing,
        "uncited_bib_keys": sorted(set(all_entries) - set(keys)),
        "semantic_scholar_api_key_configured": bool(
            os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        ),
        "source_errors": errors,
        "status_counts": {
            status: sum(record["status"] == status for record in records)
            for status in (
                "verified_two_sources",
                "verified_one_source",
                "manual_review",
            )
        },
        "records": records,
    }


def write_markdown(report: dict, path: Path) -> None:
    lines = [
        "# M03 JCDE citation audit",
        "",
        f"- In-text citation keys: {report['cited_key_count']}",
        f"- Bibliography entries: {report['bibliography_entry_count']}",
        f"- Missing BibTeX keys: {len(report['missing_bib_keys'])}",
        f"- Verified by two sources: {report['status_counts']['verified_two_sources']}",
        f"- Verified by one source: {report['status_counts']['verified_one_source']}",
        f"- Manual review: {report['status_counts']['manual_review']}",
        f"- Semantic Scholar key configured in this process: {report['semantic_scholar_api_key_configured']}",
        "",
        "| Key | Status | Sources | Minimum title match |",
        "|---|---|---|---:|",
    ]
    for record in report["records"]:
        sources = ", ".join(source["source"] for source in record["sources"]) or "none"
        similarities = [
            source["title_similarity"] for source in record["sources"]
        ]
        minimum = min(similarities) if similarities else 0.0
        lines.append(
            f"| `{record['key']}` | {record['status']} | {sources} | {minimum:.3f} |"
        )
    if report["source_errors"]:
        lines.extend(["", "## Source errors", ""])
        for source, error in report["source_errors"].items():
            lines.append(f"- {source}: {error}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tex", type=Path, required=True)
    parser.add_argument("--bib", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()

    report = audit(args.tex, args.bib)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(report, args.markdown)
    print(json.dumps(report["status_counts"], sort_keys=True))
    if report["missing_bib_keys"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
