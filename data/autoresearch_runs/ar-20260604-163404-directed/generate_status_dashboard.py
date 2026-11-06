#!/usr/bin/env python
"""Generate a compact status dashboard for the M03/M02 run."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "status_dashboard"


def read_json(path: Path):
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    verification = read_json(ROOT / "package_verification" / "verification_summary.json")
    external = read_json(ROOT / "m02_external_steps_pack" / "external_step_checks" / "external_completion_check.json")
    experiments = read_csv(ROOT / "final_figures_tables" / "experiment_summary_table.csv")
    artifact = read_json(ROOT / "artifact_manifest" / "artifact_manifest_summary.json")
    hunyuan_shape = read_json(
        ROOT
        / "m02_hunyuan21_rerun"
        / "remote_hunyuan21_shape_smoke_results"
        / "outputs"
        / "hunyuan21_shape_smoke"
        / "shape_smoke_summary.json"
    )
    hunyuan_color = read_json(
        ROOT
        / "m02_hunyuan21_rerun"
        / "colorized_projection_results"
        / "colorized_projection_summary.json"
    )

    dashboard = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": "ar-20260604-163404-directed",
        "overall": {
            "automatic_package_status": verification["status"],
            "required_checks": verification["required_checks"],
            "required_passed": verification["required_passed"],
            "boundary_checks": verification["boundary_checks"],
            "boundary_passed": verification["boundary_passed"],
            "external_status": external["overall_status"],
        },
        "m03": {
            "status": "complete_for_mainline_draft",
            "main_experiment": "M03 main100",
            "robustness": "M03 res128 robustness",
            "recommended_role": "main paper direction",
            "key_claim": "Style-induced geometry collapse and metric paradox in image-to-3D reconstruction.",
        },
        "m02": {
            "status": "automatic_experiments_complete_hunyuan_shape_smoke_not_viable_pending_human_steps",
            "completed_automatic_experiments": ["M02 proxy", "M02 EmoArt-5k", "M02 EmoArt-100 robustness"],
            "hunyuan21_shape_smoke": {
                "n": hunyuan_shape["n"],
                "success": hunyuan_shape["success"],
                "failed": hunyuan_shape["failed"],
                "texture_status": hunyuan_shape["texture_status"],
                "interpretation": "shape rerun succeeded technically but did not make original-vs-render human emotional scoring viable",
            },
            "hunyuan21_colorized_projection": {
                "n": hunyuan_color["n"],
                "success": hunyuan_color["success"],
                "texture_status": hunyuan_color["texture_status"],
                "interpretation": "front-view projected vertex colors improve visual readability but are not official PBR texture",
            },
            "human_evaluation": external["human_evaluation"]["status"],
            "artemis_wikiart_authorization": external["artemis_wikiart_authorization"]["status"],
            "recommended_role": "supplement/discussion or future SSCI/AHCI extension",
        },
        "experiments": experiments,
        "remaining_human_or_external_steps": verification["human_or_external_steps_remaining"],
        "artifact_manifest": {
            "total_files": artifact["total_files"],
            "total_bytes": artifact["total_bytes"],
            "manifest_csv": artifact["manifest_csv"],
        },
        "entry_points": {
            "run_index": "RUN_INDEX-zh.md",
            "completion_audit": "experiment-completion-audit-zh.md",
            "claim_matrix": "paper-claim-evidence-matrix-zh.md",
            "reproducibility": "REPRODUCIBILITY-zh.md",
            "verification": "package_verification/verification_summary.md",
        },
    }
    (OUT / "status_dashboard.json").write_text(json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# M03/M02 Status Dashboard",
        "",
        f"Generated UTC: `{dashboard['generated_at_utc']}`",
        "",
        "## Overall",
        "",
        f"- automatic package status: `{dashboard['overall']['automatic_package_status']}`",
        f"- required checks: {dashboard['overall']['required_passed']} / {dashboard['overall']['required_checks']}",
        f"- boundary checks: {dashboard['overall']['boundary_passed']} / {dashboard['overall']['boundary_checks']}",
        f"- external status: `{dashboard['overall']['external_status']}`",
        "",
        "## M03",
        "",
        f"- status: `{dashboard['m03']['status']}`",
        f"- role: {dashboard['m03']['recommended_role']}",
        f"- key claim: {dashboard['m03']['key_claim']}",
        "",
        "## M02",
        "",
        f"- status: `{dashboard['m02']['status']}`",
        f"- role: {dashboard['m02']['recommended_role']}",
        f"- Hunyuan3D 2.1 shape smoke: {hunyuan_shape['success']} / {hunyuan_shape['n']} succeeded; texture status `{hunyuan_shape['texture_status']}`",
        f"- Hunyuan3D 2.1 colorized projection: {hunyuan_color['success']} / {hunyuan_color['n']} succeeded; texture status `{hunyuan_color['texture_status']}`",
        f"- human evaluation: `{dashboard['m02']['human_evaluation']}`",
        f"- ArtEmis/WikiArt authorization: `{dashboard['m02']['artemis_wikiart_authorization']}`",
        "",
        "## Completed Automatic Experiments",
        "",
        "| experiment | scale | completed outputs | key finding |",
        "|---|---|---:|---|",
    ]
    for row in experiments:
        lines.append(
            f"| {row['experiment']} | {row['scale']} | {row['completed_outputs']} | {row['key_finding']} |"
        )
    lines.extend(["", "## Remaining Human Or External Steps", ""])
    for item in dashboard["remaining_human_or_external_steps"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Entry Points",
            "",
            "| purpose | file |",
            "|---|---|",
        ]
    )
    for key, value in dashboard["entry_points"].items():
        lines.append(f"| {key} | `{value}` |")
    (OUT / "status_dashboard.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": "ok", "output": str(OUT), "required_checks": dashboard["overall"]["required_checks"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
