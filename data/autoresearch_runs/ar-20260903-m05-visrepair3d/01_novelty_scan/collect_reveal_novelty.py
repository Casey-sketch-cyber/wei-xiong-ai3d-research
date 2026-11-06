from __future__ import annotations

import csv
import json
import time
from dataclasses import asdict
from pathlib import Path

import httpx

from collect_literature import Paper, merge, search_crossref, search_openalex, search_s2


HERE = Path(__file__).resolve().parent

QUERIES = [
    ("direct", "narrative visibility schedule 3D exhibition layout"),
    ("direct", "progressive reveal museum layout optimization"),
    ("direct", "controlled reveal 3D scene layout optimization"),
    ("direct", "visibility profile along visitor path optimization"),
    ("direct", "minimal edit narrative visibility repair 3D scene"),
    ("museum", "visual exposure sequence museum exhibits visitor route"),
    ("museum", "view sequencing exhibition design optimization"),
    ("museum", "spatial narrative museum path visibility"),
    ("museum", "story-driven virtual exhibition layout"),
    ("architecture", "sequential visibility reveal architectural layout optimization"),
    ("architecture", "serial vision route visibility computational design"),
    ("graphics", "occlusion choreography 3D scene layout"),
    ("graphics", "narrative reveal order virtual environment layout"),
    ("cinematography", "object visibility schedule virtual cinematography staging"),
    ("games", "progressive reveal level design visibility optimization"),
    ("robotics", "trajectory conditioned object visibility profile optimization"),
]


def main() -> None:
    rows: list[Paper] = []
    failures: list[dict[str, str]] = []
    with httpx.Client(timeout=40.0, follow_redirects=True) as client:
        for index, (family, query) in enumerate(QUERIES, start=1):
            print(f"[{index:02d}/{len(QUERIES)}] {family}: {query}", flush=True)
            for source, fn in (
                ("semantic_scholar", search_s2),
                ("openalex", search_openalex),
                ("crossref", search_crossref),
            ):
                try:
                    found = fn(client, family, query)
                    rows.extend(found)
                    print(f"  {source}: {len(found)}", flush=True)
                except Exception as exc:
                    failures.append({
                        "source": source,
                        "family": family,
                        "query": query,
                        "error": repr(exc),
                    })
                    print(f"  {source}: FAILED {exc!r}", flush=True)
            time.sleep(1.1)

    raw = [asdict(row) for row in rows]
    deduped = merge(rows)
    (HERE / "reveal_discovery_raw.json").write_text(
        json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (HERE / "reveal_discovery_deduplicated.json").write_text(
        json.dumps(deduped, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (HERE / "reveal_discovery_failures.json").write_text(
        json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with (HERE / "reveal_discovery_deduplicated.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(deduped[0].keys()))
        writer.writeheader()
        writer.writerows(deduped)
    print(json.dumps({
        "query_count": len(QUERIES),
        "raw_record_count": len(raw),
        "deduplicated_paper_count": len(deduped),
        "failure_count": len(failures),
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
