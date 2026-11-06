from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


SEEDS = (20260714, 3407)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    return parser.parse_args()


def atomic_json(path: Path, data: object) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def main() -> int:
    args = parse_args()
    sources = sorted(args.work.glob("hunyuan21_results*.json"))
    if not sources:
        raise FileNotFoundError("No Hunyuan result shards found")

    merged: dict[tuple[str, str, int], dict] = {}
    for source in sources:
        rows = json.loads(source.read_text(encoding="utf-8"))
        for row in rows:
            key = (row["object_id"], row["style"], int(row["seed"]))
            current = merged.get(key)
            if current and current.get("status") == "success" and row.get("status") == "success":
                if current.get("mesh_sha256") != row.get("mesh_sha256"):
                    raise ValueError(f"Conflicting successful meshes for {key}")
                continue
            if current is None or row.get("status") == "success":
                merged[key] = row

    with args.manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        manifest = list(csv.DictReader(handle))
    expected = {
        (row["object_id"], row["style"], seed)
        for row in manifest
        for seed in SEEDS
    }
    successful = {
        key
        for key, row in merged.items()
        if row.get("status") == "success" and Path(row["mesh_path"]).exists()
    }
    missing = sorted(expected - successful)
    unexpected = sorted(successful - expected)
    if missing or unexpected:
        raise ValueError(
            f"Hunyuan merge is incomplete: missing={len(missing)}, unexpected={len(unexpected)}"
        )

    rows = [merged[key] for key in sorted(expected)]
    atomic_json(args.work / "hunyuan21_results.json", rows)
    summary = {
        "expected": len(expected),
        "success": len(rows),
        "failed": 0,
        "source_files": [str(path) for path in sources],
        "unique_keys": len(merged),
    }
    atomic_json(args.work / "hunyuan21_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
