from __future__ import annotations

import csv
import json
import os
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from dotenv import load_dotenv


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
load_dotenv(ROOT / ".env")

QUERIES = [
    ("direct", "visibility-aware 3D scene layout repair"),
    ("direct", "viewability-aware object arrangement 3D scene"),
    ("direct", "occlusion-aware object placement 3D scene"),
    ("direct", "minimal-change 3D scene layout optimization"),
    ("direct", "post-hoc 3D scene layout refinement visibility"),
    ("direct", "minimum edit scene rearrangement visibility"),
    ("text3d", "text-to-3D scene layout refinement"),
    ("text3d", "text-conditioned 3D scene layout optimization"),
    ("text3d", "LLM 3D scene layout repair"),
    ("text3d", "3D scene generation layout collision refinement"),
    ("text3d", "3D scene layout semantic physical constraint optimization"),
    ("text3d", "language guided 3D object placement spatial constraints"),
    ("exhibition", "museum exhibition layout optimization visibility"),
    ("exhibition", "virtual museum exhibit placement visual accessibility"),
    ("exhibition", "art gallery layout visibility optimization"),
    ("exhibition", "exhibition design object visibility visitor path"),
    ("exhibition", "museum layout line of sight optimization"),
    ("exhibition", "visitor path exhibit visibility optimization"),
    ("interior", "automatic furniture arrangement visibility circulation"),
    ("interior", "interior layout optimization visual accessibility"),
    ("interior", "3D scene synthesis collision reachability navigation"),
    ("interior", "furniture layout line of sight optimization"),
    ("robotics", "object rearrangement for visibility occlusion removal"),
    ("robotics", "target visibility object rearrangement minimal movement"),
    ("robotics", "occlusion-aware rearrangement planning"),
    ("viewpoint", "viewpoint planning object inspection visibility coverage"),
    ("viewpoint", "art gallery viewpoint planning visibility"),
    ("benchmark", "synthetic corruption benchmark scene layout repair"),
    ("benchmark", "3D scene layout error correction benchmark"),
    ("benchmark", "ray casting visibility object placement optimization"),
]

KEY_TERMS = {
    "visibility": 4,
    "viewability": 5,
    "occlusion": 4,
    "line of sight": 4,
    "layout repair": 6,
    "layout refinement": 4,
    "rearrangement": 3,
    "object placement": 3,
    "minimal change": 5,
    "minimum edit": 5,
    "exhibition": 4,
    "museum": 3,
    "gallery": 3,
    "visitor path": 4,
    "navigation": 2,
    "collision": 2,
    "spatial relation": 2,
    "3d scene": 2,
}


@dataclass
class Paper:
    source: str
    family: str
    query: str
    source_id: str
    title: str
    abstract: str
    year: int | None
    venue: str
    doi: str
    arxiv_id: str
    url: str
    citations: int | None


def clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def inverted_abstract(inv: dict[str, list[int]] | None) -> str:
    if not inv:
        return ""
    positions: list[tuple[int, str]] = []
    for word, idxs in inv.items():
        positions.extend((idx, word) for idx in idxs)
    return " ".join(word for _, word in sorted(positions))


def get_json(client: httpx.Client, url: str, *, params: dict[str, str], headers: dict[str, str] | None = None, attempts: int = 4) -> dict[str, Any]:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            response = client.get(url, params=params, headers=headers)
            if response.status_code == 429:
                time.sleep(2 ** (attempt + 1))
                continue
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            last = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"request failed: {url}") from last


def search_s2(client: httpx.Client, family: str, query: str, limit: int = 20) -> list[Paper]:
    key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "").strip()
    headers = {"x-api-key": key} if key else {}
    fields = "paperId,externalIds,title,abstract,year,venue,citationCount,url"
    body = get_json(
        client,
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params={"query": query, "limit": str(limit), "fields": fields},
        headers=headers,
    )
    out: list[Paper] = []
    for item in body.get("data", []):
        ext = item.get("externalIds") or {}
        out.append(Paper(
            source="semantic_scholar",
            family=family,
            query=query,
            source_id=clean(item.get("paperId")),
            title=clean(item.get("title")),
            abstract=clean(item.get("abstract")),
            year=item.get("year"),
            venue=clean(item.get("venue")),
            doi=clean(ext.get("DOI")),
            arxiv_id=clean(ext.get("ArXiv")),
            url=clean(item.get("url")),
            citations=item.get("citationCount"),
        ))
    return out


def search_openalex(client: httpx.Client, family: str, query: str, limit: int = 25) -> list[Paper]:
    body = get_json(
        client,
        "https://api.openalex.org/works",
        params={"search": query, "per-page": str(limit), "mailto": "xiongwei@guit.edu.cn"},
    )
    out: list[Paper] = []
    for item in body.get("results", []):
        ids = item.get("ids") or {}
        primary = item.get("primary_location") or {}
        source = primary.get("source") or {}
        doi = clean(item.get("doi")).removeprefix("https://doi.org/")
        out.append(Paper(
            source="openalex",
            family=family,
            query=query,
            source_id=clean(item.get("id")).rsplit("/", 1)[-1],
            title=clean(item.get("display_name")),
            abstract=clean(inverted_abstract(item.get("abstract_inverted_index"))),
            year=item.get("publication_year"),
            venue=clean(source.get("display_name")),
            doi=doi,
            arxiv_id="",
            url=clean(primary.get("landing_page_url") or item.get("doi") or item.get("id")),
            citations=item.get("cited_by_count"),
        ))
    return out


def search_crossref(client: httpx.Client, family: str, query: str, limit: int = 20) -> list[Paper]:
    body = get_json(
        client,
        "https://api.crossref.org/works",
        params={"query.bibliographic": query, "rows": str(limit), "select": "DOI,title,abstract,published,container-title,URL,is-referenced-by-count"},
        headers={"User-Agent": "M05NoveltyScan/1.0 (mailto:xiongwei@guit.edu.cn)"},
    )
    out: list[Paper] = []
    for item in (body.get("message") or {}).get("items", []):
        dates = ((item.get("published") or {}).get("date-parts") or [[]])[0]
        year = dates[0] if dates and isinstance(dates[0], int) else None
        title = (item.get("title") or [""])[0]
        venue = (item.get("container-title") or [""])[0]
        abstract = re.sub(r"<[^>]+>", " ", clean(item.get("abstract")))
        doi = clean(item.get("DOI"))
        out.append(Paper(
            source="crossref",
            family=family,
            query=query,
            source_id=doi,
            title=clean(title),
            abstract=clean(abstract),
            year=year,
            venue=clean(venue),
            doi=doi,
            arxiv_id="",
            url=clean(item.get("URL")),
            citations=item.get("is-referenced-by-count"),
        ))
    return out


def title_key(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", title.lower())


def relevance(paper: Paper) -> int:
    text = f"{paper.title} {paper.abstract}".lower()
    score = sum(weight for term, weight in KEY_TERMS.items() if term in text)
    title = paper.title.lower()
    score += sum(weight for term, weight in KEY_TERMS.items() if term in title)
    if any(term in text for term in ("layout", "arrangement", "placement", "rearrangement")):
        score += 2
    return score


def merge(rows: list[Paper]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Paper]] = {}
    for row in rows:
        if not row.title:
            continue
        key = row.doi.lower() if row.doi else title_key(row.title)
        grouped.setdefault(key, []).append(row)

    merged: list[dict[str, Any]] = []
    for group in grouped.values():
        base = max(group, key=lambda p: (len(p.abstract), p.citations or 0))
        sources = sorted({p.source for p in group})
        families = sorted({p.family for p in group})
        queries = sorted({p.query for p in group})
        dois = [p.doi for p in group if p.doi]
        arxiv = [p.arxiv_id for p in group if p.arxiv_id]
        urls = [p.url for p in group if p.url]
        citations = [p.citations for p in group if p.citations is not None]
        item = asdict(base)
        item.update({
            "sources": ";".join(sources),
            "families": ";".join(families),
            "queries": " || ".join(queries),
            "doi": sorted(dois, key=len)[0] if dois else base.doi,
            "arxiv_id": sorted(arxiv, key=len)[0] if arxiv else base.arxiv_id,
            "url": urls[0] if urls else base.url,
            "citations": max(citations) if citations else None,
            "relevance_score": relevance(base),
            "source_count": len(sources),
            "query_count": len(queries),
        })
        merged.append(item)
    return sorted(
        merged,
        key=lambda x: (x["relevance_score"], x["query_count"], x["citations"] or 0),
        reverse=True,
    )


def main() -> None:
    client = httpx.Client(timeout=40.0, follow_redirects=True)
    rows: list[Paper] = []
    failures: list[dict[str, str]] = []
    for index, (family, query) in enumerate(QUERIES, start=1):
        print(f"[{index:02d}/{len(QUERIES)}] {family}: {query}", flush=True)
        for source, fn in (("semantic_scholar", search_s2), ("openalex", search_openalex), ("crossref", search_crossref)):
            try:
                found = fn(client, family, query)
                rows.extend(found)
                print(f"  {source}: {len(found)}", flush=True)
            except Exception as exc:  # preserve failures without aborting other sources
                failures.append({"source": source, "family": family, "query": query, "error": repr(exc)})
                print(f"  {source}: FAILED {exc!r}", flush=True)
        time.sleep(1.05)
    client.close()

    raw_path = HERE / "discovery_raw.json"
    raw_path.write_text(json.dumps([asdict(row) for row in rows], ensure_ascii=False, indent=2), encoding="utf-8")
    (HERE / "discovery_failures.json").write_text(json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8")

    merged = merge(rows)
    json_path = HERE / "discovery_deduplicated.json"
    json_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    csv_path = HERE / "discovery_deduplicated.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(merged[0].keys()))
        writer.writeheader()
        writer.writerows(merged)

    summary = {
        "snapshot_date": "2026-09-03",
        "query_count": len(QUERIES),
        "raw_record_count": len(rows),
        "deduplicated_paper_count": len(merged),
        "failure_count": len(failures),
        "top_100_cutoff_score": merged[min(99, len(merged) - 1)]["relevance_score"] if merged else None,
    }
    (HERE / "discovery_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
