#!/usr/bin/env python
"""Check whether M02 external/human steps have become ready.

This script does not request authorization or fill human ratings. It only
detects whether the expected human-provided artifacts are present.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "m02_external_steps_pack" / "external_step_checks"
HUMAN_PACK = ROOT / "m02_human_audit_pack"
RESTRICTED_ARTEMIS = ROOT.parents[1] / "restricted" / "artemis"

SCORE_FIELDS = [
    "emotion_preservation_1_5",
    "visual_evidence_preservation_1_5",
    "style_preservation_1_5",
    "geometry_usability_1_5",
    "multiview_stability_1_5",
    "overall_acceptability_1_5",
]


def is_score(value: str) -> bool:
    try:
        score = float((value or "").strip())
    except ValueError:
        return False
    return 1 <= score <= 5


def inspect_rater_csv(path: Path) -> dict[str, object]:
    rows = list(csv.DictReader(path.open("r", encoding="utf-8-sig", newline="")))
    complete_rows = 0
    partial_rows = 0
    for row in rows:
        scores = [is_score(row.get(field, "")) for field in SCORE_FIELDS]
        if all(scores):
            complete_rows += 1
        elif any(scores):
            partial_rows += 1
    return {
        "file": path.name,
        "rows": len(rows),
        "complete_rows": complete_rows,
        "partial_rows": partial_rows,
        "is_complete": len(rows) == 50 and complete_rows == 50 and partial_rows == 0,
    }


def inspect_human_evaluation() -> dict[str, object]:
    search_dirs = [HUMAN_PACK, HUMAN_PACK / "rater_exports"]
    rater_files = sorted({path for folder in search_dirs for path in folder.glob("annotation_rater*.csv")})
    inspections = [inspect_rater_csv(path) for path in rater_files]
    complete_files = [item for item in inspections if item["is_complete"]]
    status = "ready_for_analysis" if len(complete_files) >= 2 else "pending_human_evaluators"
    return {
        "status": status,
        "minimum_raters": 2,
        "search_dirs": [str(path) for path in search_dirs],
        "rater_files_found": len(rater_files),
        "complete_rater_files": len(complete_files),
        "files": inspections,
        "next_command": (
            "python analyze_annotations.py "
            + " ".join(str(path.relative_to(HUMAN_PACK)) for path, item in zip(rater_files, inspections) if item["is_complete"])
            if status == "ready_for_analysis"
            else None
        ),
    }


def inspect_artemis_authorization() -> dict[str, object]:
    patterns = ["*.csv", "*.json", "*.tsv", "*.txt"]
    files: list[Path] = []
    if RESTRICTED_ARTEMIS.exists():
        for pattern in patterns:
            files.extend(RESTRICTED_ARTEMIS.rglob(pattern))
    candidate_files = [path for path in files if path.is_file() and path.stat().st_size > 1024]
    has_terms_record = any("term" in path.name.lower() or "license" in path.name.lower() or "authorization" in path.name.lower() for path in files)
    status = "ready_for_authorized_experiment" if candidate_files and has_terms_record else "pending_human_action"
    return {
        "status": status,
        "expected_dir": str(RESTRICTED_ARTEMIS),
        "dir_exists": RESTRICTED_ARTEMIS.exists(),
        "candidate_data_files": len(candidate_files),
        "has_terms_or_authorization_record": has_terms_record,
        "sample_files": [str(path) for path in candidate_files[:10]],
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report = {
        "artemis_wikiart_authorization": inspect_artemis_authorization(),
        "human_evaluation": inspect_human_evaluation(),
    }
    report["overall_status"] = (
        "ready_for_strict_m02_followup"
        if report["artemis_wikiart_authorization"]["status"] == "ready_for_authorized_experiment"
        and report["human_evaluation"]["status"] == "ready_for_analysis"
        else "pending_external_or_human_steps"
    )
    (OUT / "external_completion_check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# External Completion Check",
        "",
        f"Overall status: `{report['overall_status']}`",
        "",
        "## ArtEmis/WikiArt Authorization",
        "",
        f"- status: `{report['artemis_wikiart_authorization']['status']}`",
        f"- expected dir: `{report['artemis_wikiart_authorization']['expected_dir']}`",
        f"- dir exists: {report['artemis_wikiart_authorization']['dir_exists']}",
        f"- candidate data files: {report['artemis_wikiart_authorization']['candidate_data_files']}",
        f"- has terms/authorization record: {report['artemis_wikiart_authorization']['has_terms_or_authorization_record']}",
        "",
        "## Human Evaluation",
        "",
        f"- status: `{report['human_evaluation']['status']}`",
        f"- rater files found: {report['human_evaluation']['rater_files_found']}",
        f"- complete rater files: {report['human_evaluation']['complete_rater_files']}",
    ]
    if report["human_evaluation"]["next_command"]:
        lines.extend(["", "Next command:", "", "```powershell", str(report["human_evaluation"]["next_command"]), "```"])
    (OUT / "external_completion_check.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
