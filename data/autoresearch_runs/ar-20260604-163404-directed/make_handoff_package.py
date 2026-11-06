#!/usr/bin/env python
"""Build a compact handoff package for collaborators and writing."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "handoff_package"


FILES = [
    "README.md",
    "RUN_INDEX-zh.md",
    "REPRODUCIBILITY-zh.md",
    "experiment-completion-audit-zh.md",
    "paper-claim-evidence-matrix-zh.md",
    "status_dashboard/status_dashboard.md",
    "status_dashboard/status_dashboard.json",
    "package_verification/verification_summary.md",
    "package_verification/verification_summary.json",
    "remote_artifact_inventory/remote_artifact_inventory.md",
    "artifact_manifest/artifact_manifest_summary.json",
    "make_m02_rater_distribution.py",
    "m02_rater_distribution/README-zh.md",
    "m02_rater_distribution/rater_package_summary.json",
    "run_m02_strict_followup.py",
    "m02_strict_followup/strict_m02_followup_status.md",
    "m02_strict_followup/strict_m02_followup_status.json",
    "m03-main100-results-zh.md",
    "m03-pilot30-results-zh.md",
    "m02-proxy-results-zh.md",
    "m02-emoart50-results-zh.md",
    "m02-emoart100-results-zh.md",
    "m02-data-access-and-rubric-zh.md",
    "m02_human_audit_pack/README-zh.md",
    "m02_human_audit_pack/RATER_QUICKSTART-zh.md",
    "m02_human_audit_pack/rater_tracking.csv",
    "m02_human_audit_pack/rater_followup_messages-zh.md",
    "m02_human_audit_pack/annotation_template.csv",
    "m02_human_audit_pack/audit_pack_summary.json",
    "m02_human_audit_pack/rater_exports/README-zh.md",
    "m02_external_steps_pack/README-zh.md",
    "m02_external_steps_pack/artemis_access_request_template-zh.md",
    "m02_external_steps_pack/artemis_access_live_check-zh.md",
    "m02_external_steps_pack/artemis_authorization_record_template-zh.md",
    "m02_external_steps_pack/human_evaluation_protocol-zh.md",
    "m02_external_steps_pack/rater_invitation_template-zh.md",
    "m02_external_steps_pack/rater_consent_template-zh.md",
    "m02_external_steps_pack/rater_metadata_template.csv",
    "m02_external_steps_pack/human_evaluation_ethics_checklist-zh.md",
    "m02_external_steps_pack/post_artemis_data_plan-zh.md",
    "m02_external_steps_pack/external_steps_status.json",
    "m02_external_steps_pack/external_step_checks/external_completion_check.md",
    "m02_external_steps_pack/external_step_checks/external_completion_check.json",
    "make_m02_artemis_access_package.py",
    "m02_artemis_access_package/README-zh.md",
    "m02_artemis_access_package/artemis_access_package_summary.json",
]

DIRS = [
    "final_figures_tables",
]


def copy_file(rel: str) -> dict[str, object]:
    src = ROOT / rel
    dst = OUT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return {"relative_path": rel, "bytes": dst.stat().st_size}


def copy_dir(rel: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    src_dir = ROOT / rel
    for src in sorted(path for path in src_dir.rglob("*") if path.is_file()):
        rel_path = src.relative_to(ROOT).as_posix()
        rows.append(copy_file(rel_path))
    return rows


def write_readme(rows: list[dict[str, object]]) -> None:
    text = """# M03/M02 Handoff Package

This compact package contains the current status dashboard, core experiment reports, claim-evidence matrix, figures/tables, verification summaries, and external-step instructions.

Start with:

1. `status_dashboard/status_dashboard.md`
2. `RUN_INDEX-zh.md`
3. `experiment-completion-audit-zh.md`
4. `paper-claim-evidence-matrix-zh.md`

Important boundary:

- M03 automatic experiments are complete and suitable as the main paper direction.
- M02 automatic/proxy experiments and human-audit materials are complete.
- Strict ArtEmis/WikiArt authorization and real human ratings are still pending external/human actions.

This handoff package does not include all human-audit images or remote mesh outputs. Use the full run directory and `remote_artifact_inventory/remote_artifact_inventory.md` for those.
"""
    (OUT / "HANDOFF_README.md").write_text(text, encoding="utf-8")
    rows.append({"relative_path": "HANDOFF_README.md", "bytes": (OUT / "HANDOFF_README.md").stat().st_size})


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for rel in FILES:
        rows.append(copy_file(rel))
    for rel in DIRS:
        rows.extend(copy_dir(rel))
    write_readme(rows)
    with (OUT / "handoff_manifest.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["relative_path", "bytes"])
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: str(r["relative_path"])))
    summary = {
        "packaged_files": len(rows),
        "total_files_on_disk": len(rows) + 2,
        "bytes": sum(int(row["bytes"]) for row in rows),
        "manifest": "handoff_manifest.csv",
        "omitted_large_artifacts": [
            "m02_human_audit_pack/images/",
            "remote mesh and raw dataset files under /root/autodl-tmp/m03/",
        ],
    }
    (OUT / "handoff_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
