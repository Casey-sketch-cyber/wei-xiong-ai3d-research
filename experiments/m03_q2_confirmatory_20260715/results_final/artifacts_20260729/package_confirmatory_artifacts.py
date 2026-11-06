from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


ROOT_FILES = (
    "CONFIRMATORY_PROTOCOL.md",
    "CONFIRMATORY_IMPLEMENTATION_ADDENDUM.md",
    "CONFIRMATORY_TRANSFORM_QA_AMENDMENT.md",
    "CONFIRMATORY_EVALUATION_IMPLEMENTATION.md",
    "FIGURE_CONTRACT.md",
    "REPRESENTATIVE_CASE_RULE.md",
    "c120_manifest.csv",
    "c120_summary.json",
    "c120_audit.json",
    "confirmatory_inputs_manifest.csv",
    "confirmatory_inputs_summary.json",
    "input_validation.json",
    "input_qa_four_objects.png",
    "input_smoke_contact_sheet.png",
    "inference_schedule_deterministic.csv",
    "inference_schedule_stochastic.csv",
    "inference_schedule_summary.json",
    "calibration_d30_schedule.csv",
    "calibration_d30_schedule.summary.json",
    "trellis_smoke_provenance.json",
    "inference_stage_status.tsv",
    "postprocess_stage_status.tsv",
    "inference_validation.json",
    "final_validation.json",
)
ROOT_PATTERNS = ("*.py", "*.sh")
TREE_PATTERNS = (
    "dataset/*.csv",
    "dataset/*.json",
    "inputs/*.csv",
    "inputs/*.json",
    "inference/*/*.json",
    "calibration/trellis/*.json",
    "evaluation/*/calibration.json",
    "evaluation/*/evaluation_summary.json",
    "evaluation/*/evaluation_results.csv",
    "render_diagnostics/render_diagnostics.csv",
    "render_diagnostics/render_diagnostics_summary.json",
    "analysis/*",
    "figures/*",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def collect(root: Path) -> list[Path]:
    files = []
    for relative in ROOT_FILES:
        path = root / relative
        if path.exists() and path.is_file():
            files.append(path)
    for pattern in ROOT_PATTERNS:
        files.extend(path for path in root.glob(pattern) if path.is_file())
    for pattern in TREE_PATTERNS:
        files.extend(path for path in root.glob(pattern) if path.is_file())
    return sorted(set(files), key=lambda path: path.relative_to(root).as_posix())


def main() -> int:
    args = parse_args()
    files = collect(args.root)
    manifest = [
        {
            "path": path.relative_to(args.root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in files
    ]
    manifest_path = args.root / "ARTIFACT_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    files.append(manifest_path)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        args.output, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
    ) as archive:
        for path in files:
            archive.write(path, path.relative_to(args.root).as_posix())
    summary = {
        "archive": str(args.output),
        "archive_bytes": args.output.stat().st_size,
        "archive_sha256": sha256(args.output),
        "file_count": len(files),
        "raw_meshes_included": False,
    }
    (args.output.with_suffix(args.output.suffix + ".summary.json")).write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
