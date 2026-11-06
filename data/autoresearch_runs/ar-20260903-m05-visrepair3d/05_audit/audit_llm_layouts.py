from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
FULL_DIR = PROJECT / "04_full_experiment"
if str(FULL_DIR) not in sys.path:
    sys.path.insert(0, str(FULL_DIR))

from formal_benchmark import make_formal_base_scene
from revealrepair_core import evaluate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--layout-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with (args.layout_dir / "llm_layout_manifest.json").open(
        "r", encoding="utf-8"
    ) as handle:
        manifest = json.load(handle)
    raw_records = [
        json.loads(line)
        for line in (args.layout_dir / "raw_generations.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    raw_hashes = {record["response_sha256"] for record in raw_records}
    accepted = manifest["accepted_layouts"]
    geometry_checks = []
    for layout in accepted:
        scene, labels, _ = make_formal_base_scene(
            int(layout["seed"]),
            source="llm",
            overrides=layout,
            route_samples=36,
            surface_grid=3,
        )
        result = evaluate(scene, labels)
        geometry_checks.append(result.hard_valid and result.schedule_loss <= 1e-12)
    routes = collections.Counter(layout["route_family"] for layout in accepted)
    exhibit_counts = collections.Counter(str(layout["exhibit_count"]) for layout in accepted)
    linked_hashes = [layout["raw_response_sha256"] for layout in accepted]
    checks = {
        "accepted_count_matches": len(accepted) == manifest["accepted"] == manifest["requested"],
        "raw_count_matches_attempted": len(raw_records) == manifest["attempted"],
        "accepted_hashes_link_to_raw": all(value in raw_hashes for value in linked_hashes),
        "accepted_hashes_unique": len(linked_hashes) == len(set(linked_hashes)),
        "balanced_route_families": set(routes.values()) == {4}
        and set(routes) == {"straight", "arc", "serpentine"},
        "balanced_exhibit_counts": set(exhibit_counts.values()) == {4}
        and set(exhibit_counts) == {"3", "4", "5"},
        "geometry_and_schedule_replay": all(geometry_checks),
    }
    report = {
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "route_family_counts": dict(routes),
        "exhibit_count_counts": dict(exhibit_counts),
        "manifest_sha256": hashlib.sha256(
            (args.layout_dir / "llm_layout_manifest.json").read_bytes()
        ).hexdigest(),
        "raw_generations_sha256": hashlib.sha256(
            (args.layout_dir / "raw_generations.jsonl").read_bytes()
        ).hexdigest(),
    }
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["all_checks_pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
