#!/usr/bin/env python
"""Generate checksums for the local M03/M02 evidence package."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "artifact_manifest"


INCLUDE_ROOT_FILES = [
    "*.md",
    "*.yaml",
    "*.json",
    "generate_final_figures.py",
    "verify_experiment_package.py",
    "generate_artifact_manifest.py",
    "colorize_hunyuan21_shapes.py",
    "run_m02_strict_followup.py",
    "make_m02_rater_distribution.py",
    "make_m02_artemis_access_package.py",
]

INCLUDE_DIRS = [
    "m03_remote_metrics",
    "m03_main100_metrics",
    "m03_res128_metrics",
    "m02_proxy_metrics",
    "m02_emoart50_metrics",
    "m02_external_steps_pack",
    "m02_strict_followup",
    "m02_rater_distribution",
    "m02_artemis_access_package",
    "m02_hunyuan21_rerun",
    "final_figures_tables",
    "m02_human_audit_pack",
    "package_verification",
]

EXCLUDE_DIR_NAMES = {
    "__pycache__",
}

EXCLUDE_SUFFIXES = {
    ".tmp",
    ".log",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def should_include(path: Path) -> bool:
    if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
        return False
    if path.suffix.lower() in EXCLUDE_SUFFIXES:
        return False
    if not path.is_file():
        return False
    return True


def collect_files() -> list[Path]:
    files: set[Path] = set()
    for pattern in INCLUDE_ROOT_FILES:
        files.update(path for path in ROOT.glob(pattern) if should_include(path))
    for dirname in INCLUDE_DIRS:
        base = ROOT / dirname
        if not base.exists():
            continue
        files.update(path for path in base.rglob("*") if should_include(path))
    # Avoid recursively including old manifest outputs inside the manifest itself.
    files = {path for path in files if not path.is_relative_to(OUT)}
    return sorted(files, key=lambda p: p.relative_to(ROOT).as_posix())


def category_for(path: Path) -> str:
    rel = path.relative_to(ROOT)
    first = rel.parts[0]
    if first.startswith("m03_") or path.name.startswith("m03-"):
        return "m03"
    if first.startswith("m02_") or path.name.startswith("m02-"):
        return "m02"
    if first == "final_figures_tables":
        return "figures_tables"
    if first == "m02_human_audit_pack":
        return "human_audit"
    if first == "package_verification" or path.name.startswith("verify_"):
        return "verification"
    if path.name.startswith("paper-claim"):
        return "claim_evidence"
    return "run_metadata"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in collect_files():
        rel = path.relative_to(ROOT).as_posix()
        rows.append(
            {
                "relative_path": rel,
                "category": category_for(path),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    csv_path = OUT / "artifact_manifest_sha256.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["relative_path", "category", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(rows)

    by_category: dict[str, dict[str, int]] = {}
    for row in rows:
        cat = str(row["category"])
        by_category.setdefault(cat, {"files": 0, "bytes": 0})
        by_category[cat]["files"] += 1
        by_category[cat]["bytes"] += int(row["bytes"])

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(ROOT),
        "manifest_csv": str(csv_path),
        "total_files": len(rows),
        "total_bytes": sum(int(row["bytes"]) for row in rows),
        "by_category": by_category,
    }
    (OUT / "artifact_manifest_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
