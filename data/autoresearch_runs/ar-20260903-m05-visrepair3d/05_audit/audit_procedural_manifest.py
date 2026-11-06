from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    recorded_hash = manifest["manifest_sha256"]
    unsigned = dict(manifest)
    del unsigned["manifest_sha256"]
    canonical = json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    computed_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    accepted = manifest["accepted_layouts"]
    seeds = [int(item["seed"]) for item in accepted]
    routes = collections.Counter(
        item["layout_metadata"]["route_family"] for item in accepted
    )
    exhibits = collections.Counter(
        str(item["layout_metadata"]["exhibit_count"]) for item in accepted
    )
    checks = {
        "internal_hash_matches": recorded_hash == computed_hash,
        "accepted_count_20": len(accepted) == manifest["accepted"] == manifest["requested"] == 20,
        "accepted_seeds_unique_and_sorted": len(seeds) == len(set(seeds))
        and seeds == sorted(seeds),
        "all_route_families_present": set(routes) == {"straight", "arc", "serpentine"},
        "all_exhibit_counts_present": set(exhibits) == {"3", "4", "5"},
        "all_corruptions_have_positive_loss": all(
            float(item["minimum_corruption_loss"]) > 0.0 for item in accepted
        ),
    }
    report = {
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "accepted_seeds": seeds,
        "rejected_seed_count": len(manifest["rejected_layouts"]),
        "route_family_counts": dict(routes),
        "exhibit_count_counts": dict(exhibits),
        "minimum_corruption_loss": min(
            float(item["minimum_corruption_loss"]) for item in accepted
        ),
        "manifest_file_sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        "manifest_internal_sha256": recorded_hash,
    }
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["all_checks_pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
