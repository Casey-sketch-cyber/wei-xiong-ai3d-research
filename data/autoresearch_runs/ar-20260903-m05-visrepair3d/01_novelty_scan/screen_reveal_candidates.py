from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent

TERMS = {
    "reveal": {
        "progressive reveal": 8,
        "controlled reveal": 8,
        "visual reveal": 7,
        "reveal": 5,
        "disclosure": 4,
        "unfolding": 3,
    },
    "trajectory": {
        "visitor path": 7,
        "visitor route": 7,
        "view sequence": 7,
        "view sequencing": 7,
        "visibility profile": 8,
        "visibility schedule": 9,
        "trajectory-conditioned": 8,
        "trajectory conditioned": 8,
        "along a path": 5,
        "serial vision": 6,
        "sequential visibility": 7,
    },
    "narrative": {
        "narrative": 4,
        "story-driven": 5,
        "storytelling": 4,
        "curatorial intent": 4,
        "exhibition sequence": 6,
    },
    "visibility": {
        "visibility": 3,
        "visible": 2,
        "occlusion": 3,
        "line of sight": 4,
        "sightline": 4,
        "visual exposure": 4,
        "viewpoint": 2,
    },
    "layout": {
        "layout": 3,
        "placement": 3,
        "arrangement": 3,
        "staging": 3,
        "spatial design": 2,
        "optimization": 2,
        "repair": 4,
        "refinement": 3,
    },
    "domain": {
        "museum": 3,
        "exhibition": 3,
        "exhibit": 3,
        "gallery": 3,
        "virtual environment": 2,
        "3d scene": 2,
        "cinematography": 2,
        "level design": 2,
    },
}


def normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def main() -> None:
    rows = json.loads(
        (HERE / "reveal_discovery_deduplicated.json").read_text(encoding="utf-8")
    )
    selected: list[dict[str, Any]] = []
    for row in rows:
        title = normalize(row.get("title")).lower()
        abstract = normalize(row.get("abstract")).lower()
        text = f"{title} {abstract}"
        dimensions: dict[str, int] = {}
        total = 0
        for dimension, weighted_terms in TERMS.items():
            value = 0
            for term, weight in weighted_terms.items():
                if term in text:
                    value += weight
                if term in title:
                    value += weight
            dimensions[dimension] = value
            total += value
        if dimensions["visibility"] == 0:
            continue
        if dimensions["layout"] == 0 and dimensions["trajectory"] == 0:
            continue
        if dimensions["domain"] == 0 and dimensions["narrative"] == 0:
            continue
        if dimensions["reveal"] and dimensions["trajectory"]:
            total += 12
        if dimensions["narrative"] and dimensions["trajectory"]:
            total += 8
        if dimensions["visibility"] and dimensions["layout"]:
            total += 6
        selected.append({
            "screen_score": total,
            **dimensions,
            "year": row.get("year"),
            "title": normalize(row.get("title")),
            "venue": normalize(row.get("venue")),
            "doi": normalize(row.get("doi")),
            "arxiv_id": normalize(row.get("arxiv_id")),
            "url": normalize(row.get("url")),
            "citations": row.get("citations"),
            "sources": normalize(row.get("sources") or row.get("source")),
            "families": normalize(row.get("families")),
            "queries": normalize(row.get("queries")),
            "abstract": normalize(row.get("abstract")),
        })
    selected.sort(
        key=lambda x: (x["screen_score"], int(x["year"] or 0), int(x["citations"] or 0)),
        reverse=True,
    )
    (HERE / "reveal_screened_candidates.json").write_text(
        json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with (HERE / "reveal_screened_candidates.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(selected[0].keys()))
        writer.writeheader()
        writer.writerows(selected)
    print(json.dumps({"screened_count": len(selected), "top_score": selected[0]["screen_score"]}, indent=2))


if __name__ == "__main__":
    main()
