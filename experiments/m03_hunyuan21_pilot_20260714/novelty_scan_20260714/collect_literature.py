from __future__ import annotations

import csv
import json
import os
import re
import time
from collections import defaultdict
from pathlib import Path

import requests
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent
S2_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = (
    "paperId,title,abstract,year,authors,venue,publicationTypes,"
    "citationCount,externalIds,url,openAccessPdf,publicationDate"
)
QUERIES = [
    "single image 3D generation image cues robustness",
    "image to 3D stylized input benchmark",
    "single image 3D style perturbation",
    "image to 3D domain shift robustness",
    "image to 3D artistic input reconstruction",
    "sketch to 3D benchmark reconstruction",
    "single image 3D generation evaluation geometry metrics",
    "single image 3D metric reliability Chamfer F-score",
    "image to 3D topology volume watertight",
    "image to 3D cross model comparison benchmark",
    "3D generation asset quality evaluation geometry",
    "single image 3D controlled benchmark ground truth",
    "stylization geometric cues single image 3D",
    "illustration image to 3D benchmark",
]

CORE_TERMS = {
    "image-to-3d": 5,
    "image to 3d": 5,
    "single-image 3d": 5,
    "single image 3d": 5,
    "stylized": 4,
    "stylised": 4,
    "style": 2,
    "artistic": 3,
    "illustration": 3,
    "sketch": 2,
    "robust": 3,
    "perturb": 3,
    "cue": 2,
    "benchmark": 2,
    "evaluation": 1,
    "geometry": 2,
    "volume": 3,
    "topology": 3,
    "watertight": 3,
    "chamfer": 2,
    "f-score": 2,
    "ground truth": 2,
    "cross-model": 3,
    "model-agnostic": 3,
}


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def paper_score(paper: dict) -> int:
    text = f"{paper.get('title') or ''} {paper.get('abstract') or ''}".lower()
    score = sum(weight for term, weight in CORE_TERMS.items() if term in text)
    year = paper.get("year") or 0
    if year >= 2025:
        score += 3
    elif year >= 2023:
        score += 2
    elif year >= 2020:
        score += 1
    return score


def search(query: str, headers: dict[str, str]) -> tuple[int, list[dict]]:
    params = {
        "query": query,
        "limit": 100,
        "year": "2018-2026",
        "fields": FIELDS,
    }
    for attempt in range(6):
        response = requests.get(
            S2_SEARCH_URL,
            params=params,
            headers=headers,
            timeout=60,
        )
        if response.status_code != 429:
            response.raise_for_status()
            payload = response.json()
            return int(payload.get("total", 0)), payload.get("data", [])
        retry_after = float(response.headers.get("Retry-After", 0) or 0)
        time.sleep(max(retry_after, 2.0 * (attempt + 1)))
    response.raise_for_status()
    raise RuntimeError("unreachable")


def main() -> None:
    load_dotenv(Path(__file__).resolve().parents[3] / ".env")
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    if not api_key:
        raise RuntimeError("SEMANTIC_SCHOLAR_API_KEY is not configured")

    headers = {"x-api-key": api_key, "User-Agent": "M03-novelty-scan/1.0"}
    papers: dict[str, dict] = {}
    query_hits: defaultdict[str, set[str]] = defaultdict(set)
    logs: list[dict] = []

    for index, query in enumerate(QUERIES, start=1):
        started = time.time()
        try:
            total, hits = search(query, headers)
            status = "ok"
            error = ""
        except requests.RequestException as exc:
            total, hits = 0, []
            status = "error"
            error = str(exc)

        for paper in hits:
            title = paper.get("title") or ""
            key = paper.get("paperId") or normalize_title(title)
            if not key or not title:
                continue
            papers[key] = paper
            query_hits[key].add(query)

        logs.append(
            {
                "query_id": f"Q{index:02d}",
                "query": query,
                "source": "Semantic Scholar Graph API",
                "year_filter": "2018-2026",
                "reported_total": total,
                "retrieved": len(hits),
                "status": status,
                "error": error,
                "elapsed_seconds": round(time.time() - started, 3),
            }
        )
        time.sleep(1.1)

    rows = []
    for key, paper in papers.items():
        external = paper.get("externalIds") or {}
        authors = "; ".join(a.get("name", "") for a in paper.get("authors") or [])
        open_pdf = (paper.get("openAccessPdf") or {}).get("url", "")
        row = {
            "score": paper_score(paper),
            "paper_id": paper.get("paperId", key),
            "year": paper.get("year", ""),
            "publication_date": paper.get("publicationDate", ""),
            "citation_count": paper.get("citationCount", 0),
            "title": paper.get("title", ""),
            "authors": authors,
            "venue": paper.get("venue", ""),
            "doi": external.get("DOI", ""),
            "arxiv": external.get("ArXiv", ""),
            "corpus_id": external.get("CorpusId", ""),
            "semantic_scholar_url": paper.get("url", ""),
            "open_access_pdf": open_pdf,
            "matched_queries": " | ".join(sorted(query_hits[key])),
            "abstract": re.sub(r"\s+", " ", paper.get("abstract") or "").strip(),
        }
        rows.append(row)

    rows.sort(
        key=lambda row: (
            int(row["score"]),
            int(row["year"] or 0),
            int(row["citation_count"] or 0),
        ),
        reverse=True,
    )

    with (ROOT / "semantic_scholar_candidate_pool.json").open("w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)

    with (ROOT / "semantic_scholar_candidate_pool.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with (ROOT / "search_log.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(logs[0].keys()))
        writer.writeheader()
        writer.writerows(logs)

    summary = {
        "queries": len(QUERIES),
        "successful_queries": sum(log["status"] == "ok" for log in logs),
        "unique_candidates": len(rows),
        "candidates_score_ge_15": sum(int(row["score"]) >= 15 for row in rows),
        "candidates_score_ge_20": sum(int(row["score"]) >= 20 for row in rows),
    }
    (ROOT / "collection_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
