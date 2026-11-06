from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent

TASK = (
    "layout", "arrangement", "placement", "rearrangement", "repair",
    "correction", "refinement", "editing", "furnishing",
)
VIEW = (
    "visibility", "visible", "viewability", "occlusion", "line of sight",
    "sightline", "viewpoint", "visual exposure", "viewing frustum",
)
MIN_EDIT = (
    "minimal change", "minimum change", "minimum edit", "minimal edit",
    "edit cost", "repair cost", "local correction", "sparse", "fewest",
    "displacement", "preserve existing", "post-hoc",
)
EXHIBITION = ("museum", "exhibition", "exhibit", "gallery", "artwork", "painting")
CONSTRAINT = (
    "navigation", "navigability", "visitor path", "pathway", "circulation",
    "collision", "accessibility", "spatial relation", "semantic constraint",
)
TEXT3D = (
    "text-conditioned 3d", "text-to-3d", "language-guided", "large language model",
    "vision-language model", "3d scene generation", "3d scene synthesis",
)


def norm(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def term_count(text: str, terms: tuple[str, ...]) -> int:
    return sum(term in text for term in terms)


def score(row: dict[str, Any]) -> tuple[int, dict[str, bool]]:
    title = norm(row.get("title")).lower()
    abstract = norm(row.get("abstract")).lower()
    text = f"{title} {abstract}"
    dims = {
        "task": has_any(text, TASK),
        "view": has_any(text, VIEW),
        "min_edit": has_any(text, MIN_EDIT),
        "exhibition": has_any(text, EXHIBITION),
        "constraint": has_any(text, CONSTRAINT),
        "text3d": has_any(text, TEXT3D),
    }
    value = (
        3 * term_count(title, TASK)
        + 4 * term_count(title, VIEW)
        + 5 * term_count(title, MIN_EDIT)
        + 3 * term_count(title, EXHIBITION)
        + 2 * term_count(title, CONSTRAINT)
        + 3 * term_count(title, TEXT3D)
        + term_count(abstract, TASK)
        + 2 * term_count(abstract, VIEW)
        + 3 * term_count(abstract, MIN_EDIT)
        + term_count(abstract, EXHIBITION)
        + term_count(abstract, CONSTRAINT)
        + term_count(abstract, TEXT3D)
    )
    if dims["task"] and dims["view"]:
        value += 8
    if dims["exhibition"] and dims["view"]:
        value += 7
    if dims["task"] and dims["min_edit"]:
        value += 7
    if dims["text3d"] and dims["task"]:
        value += 5
    return value, dims


def title_key(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", title.lower())


def load_records() -> list[dict[str, Any]]:
    records = json.loads((HERE / "discovery_deduplicated.json").read_text(encoding="utf-8"))
    arxiv_path = HERE / "arxiv_deduplicated.json"
    if arxiv_path.exists():
        for item in json.loads(arxiv_path.read_text(encoding="utf-8")):
            records.append({
                "source": "arxiv",
                "sources": "arxiv",
                "families": "arxiv",
                "queries": " || ".join(item.get("queries") or []),
                "source_id": item.get("arxiv_id", ""),
                "title": item.get("title", ""),
                "abstract": item.get("abstract", ""),
                "year": int(str(item.get("published", ""))[:4]) if str(item.get("published", ""))[:4].isdigit() else None,
                "venue": "arXiv",
                "doi": "",
                "arxiv_id": item.get("arxiv_id", ""),
                "url": item.get("url", ""),
                "citations": None,
                "source_count": 1,
                "query_count": len(item.get("queries") or []),
            })
    return records


def main() -> None:
    dedup: dict[str, dict[str, Any]] = {}
    for row in load_records():
        title = norm(row.get("title"))
        if not title:
            continue
        key = norm(row.get("doi")).lower() or title_key(title)
        current = dedup.get(key)
        if current is None or len(norm(row.get("abstract"))) > len(norm(current.get("abstract"))):
            dedup[key] = row

    screened: list[dict[str, Any]] = []
    for row in dedup.values():
        value, dims = score(row)
        if not (
            (dims["task"] and dims["view"])
            or (dims["exhibition"] and dims["view"])
            or (dims["task"] and dims["min_edit"])
            or (dims["text3d"] and dims["task"])
        ):
            continue
        item = {
            "screen_score": value,
            **dims,
            "year": row.get("year"),
            "title": norm(row.get("title")),
            "venue": norm(row.get("venue")),
            "doi": norm(row.get("doi")),
            "arxiv_id": norm(row.get("arxiv_id")),
            "url": norm(row.get("url")),
            "citations": row.get("citations"),
            "sources": norm(row.get("sources") or row.get("source")),
            "families": norm(row.get("families")),
            "queries": norm(row.get("queries")),
            "abstract": norm(row.get("abstract")),
        }
        screened.append(item)

    screened.sort(
        key=lambda x: (x["screen_score"], int(x["year"] or 0), int(x["citations"] or 0)),
        reverse=True,
    )
    (HERE / "screened_candidates.json").write_text(
        json.dumps(screened, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with (HERE / "screened_candidates.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(screened[0].keys()))
        writer.writeheader()
        writer.writerows(screened)
    print(json.dumps({
        "deduplicated_across_all_sources": len(dedup),
        "screened_candidate_count": len(screened),
        "top_score": screened[0]["screen_score"] if screened else None,
    }, indent=2))


if __name__ == "__main__":
    main()
