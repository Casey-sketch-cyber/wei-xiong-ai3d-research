#!/usr/bin/env python
"""Resume strict M02 follow-up after external artifacts arrive."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "m02_strict_followup"
EXTERNAL_JSON = ROOT / "m02_external_steps_pack" / "external_step_checks" / "external_completion_check.json"
HUMAN_PACK = ROOT / "m02_human_audit_pack"
HUMAN_SUMMARY = HUMAN_PACK / "analysis_outputs" / "human_annotation_summary.json"


def run(cmd: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_report(report: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "strict_m02_followup_status.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        "# Strict M02 Follow-Up Status",
        "",
        f"Generated UTC: `{report['generated_at_utc']}`",
        "",
        f"Overall status: `{report['overall_status']}`",
        "",
        "## Human Evaluation",
        "",
        f"- status: `{report['human_evaluation']['status']}`",
        f"- rater files found: {report['human_evaluation'].get('rater_files_found', 0)}",
        f"- complete rater files: {report['human_evaluation'].get('complete_rater_files', 0)}",
        f"- analysis status: `{report['human_analysis'].get('status')}`",
        "",
        "## ArtEmis/WikiArt Authorization",
        "",
        f"- status: `{report['artemis_wikiart_authorization']['status']}`",
        f"- expected dir: `{report['artemis_wikiart_authorization'].get('expected_dir')}`",
        f"- candidate data files: {report['artemis_wikiart_authorization'].get('candidate_data_files', 0)}",
        f"- has terms/authorization record: {report['artemis_wikiart_authorization'].get('has_terms_or_authorization_record')}",
        "",
        "## Next Actions",
        "",
    ]
    for item in report["next_actions"]:
        lines.append(f"- {item}")
    (OUT / "strict_m02_followup_status.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    check = run([sys.executable, str(ROOT / "check_external_steps.py")])
    if check.returncode != 0:
        report = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "overall_status": "check_failed",
            "human_evaluation": {"status": "unknown"},
            "human_analysis": {"status": "not_run"},
            "artemis_wikiart_authorization": {"status": "unknown"},
            "check_stdout": check.stdout,
            "check_stderr": check.stderr,
            "next_actions": ["Fix check_external_steps.py failure before strict M02 follow-up."],
        }
        write_report(report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    external = load_json(EXTERNAL_JSON)
    human = external["human_evaluation"]
    artemis = external["artemis_wikiart_authorization"]
    human_analysis: dict[str, object] = {"status": "not_run"}
    next_actions: list[str] = []

    if human["status"] == "ready_for_analysis":
        command = str(human["next_command"]).split()
        analysis = run(command, cwd=HUMAN_PACK)
        human_analysis = {
            "status": "pass" if analysis.returncode == 0 else "failed",
            "command": " ".join(command),
            "stdout_tail": analysis.stdout[-4000:],
            "stderr_tail": analysis.stderr[-4000:],
            "summary_path": str(HUMAN_SUMMARY),
            "summary_exists": HUMAN_SUMMARY.exists(),
        }
        if analysis.returncode == 0:
            next_actions.append("Human ratings are analyzed; inspect m02_human_audit_pack/analysis_outputs/ before manuscript integration.")
        else:
            next_actions.append("Human rating files were detected, but analysis failed; inspect strict_m02_followup_status.json.")
    else:
        next_actions.append("Collect at least 2 complete rater CSV files under m02_human_audit_pack/rater_exports/.")

    if artemis["status"] == "ready_for_authorized_experiment":
        next_actions.append("Authorized ArtEmis/WikiArt files are present; run the formal ArtEmis subset experiment described in m02_external_steps_pack/post_artemis_data_plan-zh.md.")
    else:
        next_actions.append("Complete ArtEmis/WikiArt authorization and place data plus Terms/authorization record under D:/AutoResearch/data/restricted/artemis/.")

    overall_status = "pending_external_or_human_steps"
    if human["status"] == "ready_for_analysis" and human_analysis.get("status") == "pass" and artemis["status"] == "ready_for_authorized_experiment":
        overall_status = "ready_for_authorized_artemis_experiment"
    elif human["status"] == "ready_for_analysis" and human_analysis.get("status") == "pass":
        overall_status = "human_analysis_complete_pending_artemis"
    elif artemis["status"] == "ready_for_authorized_experiment":
        overall_status = "artemis_ready_pending_human_analysis"

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall_status,
        "human_evaluation": human,
        "human_analysis": human_analysis,
        "artemis_wikiart_authorization": artemis,
        "next_actions": next_actions,
    }
    write_report(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

