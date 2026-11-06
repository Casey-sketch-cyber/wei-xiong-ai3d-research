#!/usr/bin/env python
"""Verify the M03/M02 experiment evidence package.

The verifier checks local artifacts only. It does not claim that external
human-scoring or ArtEmis/WikiArt authorization steps are complete.
"""

from __future__ import annotations

import csv
import json
import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "package_verification"


def read_json(path: Path):
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def count_csv(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def check_file(path: Path, min_bytes: int = 1) -> dict[str, object]:
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    return {
        "path": str(path.relative_to(ROOT)),
        "exists": exists,
        "bytes": size,
        "ok": exists and size >= min_bytes,
    }


def ok_item(name: str, ok: bool, evidence: object, severity: str = "required") -> dict[str, object]:
    return {"name": name, "ok": bool(ok), "severity": severity, "evidence": evidence}


def verify_core_metrics() -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    checks.append(ok_item("m03_main100_relative_rows", len(read_json(ROOT / "m03_main100_metrics" / "eval_gt_relative_to_photo.json")) == 5, "5 non-photo styles"))
    checks.append(ok_item("m03_res128_relative_rows", len(read_json(ROOT / "m03_res128_metrics" / "eval_gt_relative_to_photo.json")) == 5, "5 non-photo styles"))
    proxy = read_json(ROOT / "m02_proxy_metrics" / "clip_affect_aggregate.json")
    checks.append(ok_item("m02_proxy_rows", len(proxy) == 5, "5 non-photo styles"))
    emo = read_json(ROOT / "m02_emoart50_metrics" / "emoart50_affect_aggregate.json")
    checks.append(ok_item("m02_emoart_n50_render_ok", emo.get("n") == 50 and emo.get("render_ok") == 50, {"n": emo.get("n"), "render_ok": emo.get("render_ok")}))
    va = read_json(ROOT / "m02_emoart50_metrics" / "emoart50_valence_arousal_aggregate.json")
    checks.append(ok_item("m02_emoart_va_n50", va.get("n") == 50, {"n": va.get("n")}))
    emo100 = read_json(ROOT / "m02_emoart100_metrics" / "emoart100_affect_aggregate.json")
    checks.append(ok_item("m02_emoart100_render_ok", emo100.get("n") == 100 and emo100.get("render_ok") == 100, {"n": emo100.get("n"), "render_ok": emo100.get("render_ok")}))
    va100 = read_json(ROOT / "m02_emoart100_metrics" / "emoart100_valence_arousal_aggregate.json")
    checks.append(ok_item("m02_emoart100_va_n100", va100.get("n") == 100, {"n": va100.get("n")}))
    return checks


def verify_figures_tables() -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    ft = ROOT / "final_figures_tables"
    manifest = read_json(ft / "manifest.json")
    expected_tables = {
        "experiment_summary_table.csv": 5,
        "figure_caption_table.csv": 6,
        "m02_emoart100_by_emotion.csv": 8,
        "m02_emoart100_summary.csv": 1,
        "m02_emoart100_va.csv": 1,
        "m02_emoart_by_emotion.csv": 8,
        "m02_emoart_summary.csv": 1,
        "m02_emoart_va.csv": 1,
        "m02_proxy.csv": 5,
        "m03_main100.csv": 5,
        "m03_res128.csv": 5,
    }
    for table, rows in expected_tables.items():
        path = ft / table
        actual = count_csv(path) if path.exists() else -1
        checks.append(ok_item(f"table_{table}", actual == rows, {"expected_rows": rows, "actual_rows": actual}))
    for fig in manifest.get("figures", []):
        path = ft / fig
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        checks.append(
            ok_item(
                f"figure_{fig}",
                path.exists() and "<svg" in text and "</svg>" in text and len(text) > 500,
                {"exists": path.exists(), "bytes": path.stat().st_size if path.exists() else 0},
            )
        )
    captions = csv_rows(ft / "figure_caption_table.csv")
    for row in captions:
        fig_path = ft / row["figure"]
        checks.append(ok_item(f"caption_target_{row['figure']}", fig_path.exists(), {"claim_link": row.get("claim_link", "")}))
    return checks


def verify_human_audit_pack() -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    pack = ROOT / "m02_human_audit_pack"
    dist = ROOT / "m02_rater_distribution"
    summary = read_json(pack / "audit_pack_summary.json")
    checks.append(ok_item("human_audit_items", summary.get("n_items") == 50, {"n_items": summary.get("n_items")}))
    checks.append(ok_item("human_audit_image_pairs", summary.get("image_pairs_present") == 50 and summary.get("image_pngs") == 100, {"image_pairs_present": summary.get("image_pairs_present"), "image_pngs": summary.get("image_pngs")}))
    checks.append(ok_item("human_audit_status_pending", summary.get("human_scoring_status") == "pending_human_evaluators", summary.get("human_scoring_status"), severity="boundary"))
    html = pack / "annotation_web.html"
    html_text = html.read_text(encoding="utf-8") if html.exists() else ""
    checks.append(ok_item("human_audit_html_blocks", len(re.findall(r'<section class="item"', html_text)) == 50, "50 item sections"))
    rating_tool = pack / "rating_tool.html"
    rating_text = rating_tool.read_text(encoding="utf-8") if rating_tool.exists() else ""
    checks.append(ok_item("human_audit_rating_tool_exists", rating_tool.exists() and rating_tool.stat().st_size > 1000, check_file(rating_tool)))
    checks.append(ok_item("human_audit_rating_tool_core_features", "Export CSV" in rating_text and "localStorage" in rating_text and "emotion_preservation_1_5" in rating_text, "rating tool has export/localStorage/score fields"))
    checks.append(ok_item("human_audit_template_rows", count_csv(pack / "annotation_template.csv") == 50, "50 rows"))
    checks.append(ok_item("human_audit_analysis_script", (pack / "analyze_annotations.py").exists(), "script exists"))
    checks.append(ok_item("human_audit_rating_tool_generator", (pack / "generate_rating_tool.py").exists(), "generator exists"))
    checks.append(ok_item("human_audit_rater_quickstart", (pack / "RATER_QUICKSTART-zh.md").exists() and (pack / "RATER_QUICKSTART-zh.md").stat().st_size > 300, check_file(pack / "RATER_QUICKSTART-zh.md")))
    checks.append(ok_item("human_audit_rater_exports_readme", (pack / "rater_exports" / "README-zh.md").exists() and (pack / "rater_exports" / "README-zh.md").stat().st_size > 300, check_file(pack / "rater_exports" / "README-zh.md")))
    checks.append(ok_item("human_audit_rater_tracking", count_csv(pack / "rater_tracking.csv") >= 2, {"rows": count_csv(pack / "rater_tracking.csv") if (pack / "rater_tracking.csv").exists() else -1}))
    checks.append(ok_item("human_audit_rater_followup_messages", (pack / "rater_followup_messages-zh.md").exists() and (pack / "rater_followup_messages-zh.md").stat().st_size > 300, check_file(pack / "rater_followup_messages-zh.md")))
    checks.append(ok_item("human_audit_rating_tool_summary", summary.get("validation", {}).get("rating_tool_items") == 50 and summary.get("validation", {}).get("rating_tool_js_syntax") == "pass", summary.get("validation", {})))
    empty_summary = read_json(pack / "analysis_outputs" / "human_annotation_summary.json")
    checks.append(ok_item("human_audit_empty_template_no_fake_scores", empty_summary.get("status") == "no_completed_scores", empty_summary.get("status")))
    dist_summary_path = dist / "rater_package_summary.json"
    zip_path = dist / "M02_rater_package.zip"
    checks.append(ok_item("rater_distribution_summary_exists", dist_summary_path.exists() and dist_summary_path.stat().st_size > 100, check_file(dist_summary_path)))
    checks.append(ok_item("rater_distribution_zip_exists", zip_path.exists() and zip_path.stat().st_size > 1_000_000, check_file(zip_path)))
    if dist_summary_path.exists() and zip_path.exists():
        dist_summary = read_json(dist_summary_path)
        with zipfile.ZipFile(zip_path) as archive:
            names = [entry.filename for entry in archive.infolist()]
        checks.append(
            ok_item(
                "rater_distribution_zip_contents",
                dist_summary.get("files_in_zip") == len(names) == 108
                and dist_summary.get("image_pngs") == 100
                and len(names) == len(set(names)),
                {
                    "summary_files": dist_summary.get("files_in_zip"),
                    "zip_entries": len(names),
                    "image_pngs": dist_summary.get("image_pngs"),
                    "duplicate_names": len(names) - len(set(names)),
                },
            )
        )
    return checks


def verify_m02_hunyuan21_smoke() -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    rerun = ROOT / "m02_hunyuan21_rerun"
    report = ROOT / "m02-hunyuan21-smoke-results-zh.md"
    local_summary_path = rerun / "hunyuan21_smoke_summary.json"
    shape_summary_path = (
        rerun
        / "remote_hunyuan21_shape_smoke_results"
        / "outputs"
        / "hunyuan21_shape_smoke"
        / "shape_smoke_summary.json"
    )
    contact_sheet = (
        rerun
        / "remote_hunyuan21_shape_smoke_results"
        / "outputs"
        / "hunyuan21_shape_smoke"
        / "previews"
        / "hunyuan21_shape_contact_sheet.png"
    )
    zip_path = rerun / "hunyuan21_shape_smoke_results.zip"
    shape_root = rerun / "remote_hunyuan21_shape_smoke_results" / "outputs" / "hunyuan21_shape_smoke"

    checks.append(ok_item("m02_hunyuan21_report_exists", report.exists() and report.stat().st_size > 1000, check_file(report)))
    checks.append(ok_item("m02_hunyuan21_local_summary_exists", local_summary_path.exists() and local_summary_path.stat().st_size > 100, check_file(local_summary_path)))
    checks.append(ok_item("m02_hunyuan21_shape_summary_exists", shape_summary_path.exists() and shape_summary_path.stat().st_size > 100, check_file(shape_summary_path)))
    checks.append(ok_item("m02_hunyuan21_contact_sheet_exists", contact_sheet.exists() and contact_sheet.stat().st_size > 100_000, check_file(contact_sheet)))
    checks.append(ok_item("m02_hunyuan21_results_zip_exists", zip_path.exists() and zip_path.stat().st_size > 1_000_000, check_file(zip_path)))

    if local_summary_path.exists():
        local_summary = read_json(local_summary_path)
        checks.append(
            ok_item(
                "m02_hunyuan21_local_sample_count",
                local_summary.get("n_samples") == 8 and local_summary.get("model_target") == "Hunyuan3D 2.1",
                {"n_samples": local_summary.get("n_samples"), "model_target": local_summary.get("model_target")},
            )
        )
    if shape_summary_path.exists():
        shape_summary = read_json(shape_summary_path)
        checks.append(
            ok_item(
                "m02_hunyuan21_shape_success_8",
                shape_summary.get("n") == 8 and shape_summary.get("success") == 8 and shape_summary.get("failed") == 0,
                {"n": shape_summary.get("n"), "success": shape_summary.get("success"), "failed": shape_summary.get("failed")},
            )
        )
        checks.append(
            ok_item(
                "m02_hunyuan21_texture_boundary",
                str(shape_summary.get("texture_status", "")).startswith("not_run"),
                shape_summary.get("texture_status"),
                severity="boundary",
            )
        )
    if shape_root.exists():
        shape_glbs = list(shape_root.glob("*/shape.glb"))
        panels = list(shape_root.glob("*/comparison_panel.png"))
        checks.append(ok_item("m02_hunyuan21_shape_glb_count", len(shape_glbs) == 8, {"shape_glbs": len(shape_glbs)}))
        checks.append(ok_item("m02_hunyuan21_comparison_panel_count", len(panels) == 8, {"comparison_panels": len(panels)}))
    color_dir = rerun / "colorized_projection_results"
    color_report = ROOT / "m02-hunyuan21-colorized-projection-results-zh.md"
    color_summary_path = color_dir / "colorized_projection_summary.json"
    color_sheet = color_dir / "previews" / "hunyuan21_colorized_projection_contact_sheet.png"
    color_zip = rerun / "hunyuan21_colorized_projection_results.zip"
    checks.append(ok_item("m02_hunyuan21_color_report_exists", color_report.exists() and color_report.stat().st_size > 1000, check_file(color_report)))
    checks.append(ok_item("m02_hunyuan21_color_script_exists", (ROOT / "colorize_hunyuan21_shapes.py").exists() and (ROOT / "colorize_hunyuan21_shapes.py").stat().st_size > 1000, check_file(ROOT / "colorize_hunyuan21_shapes.py")))
    checks.append(ok_item("m02_hunyuan21_color_summary_exists", color_summary_path.exists() and color_summary_path.stat().st_size > 100, check_file(color_summary_path)))
    checks.append(ok_item("m02_hunyuan21_color_contact_sheet_exists", color_sheet.exists() and color_sheet.stat().st_size > 100_000, check_file(color_sheet)))
    checks.append(ok_item("m02_hunyuan21_color_results_zip_exists", color_zip.exists() and color_zip.stat().st_size > 1_000_000, check_file(color_zip)))
    if color_summary_path.exists():
        color_summary = read_json(color_summary_path)
        checks.append(
            ok_item(
                "m02_hunyuan21_color_success_8",
                color_summary.get("n") == 8 and color_summary.get("success") == 8,
                {"n": color_summary.get("n"), "success": color_summary.get("success")},
            )
        )
        checks.append(
            ok_item(
                "m02_hunyuan21_color_not_official_pbr_boundary",
                color_summary.get("texture_status") == "not_official_pbr_front_view_vertex_color_projection",
                color_summary.get("texture_status"),
                severity="boundary",
            )
        )
    if color_dir.exists():
        color_glbs = list(color_dir.glob("*/colorized_shape.glb"))
        color_panels = list(color_dir.glob("*/colorized_comparison_panel.png"))
        checks.append(ok_item("m02_hunyuan21_color_glb_count", len(color_glbs) == 8, {"colorized_glbs": len(color_glbs)}))
        checks.append(ok_item("m02_hunyuan21_color_panel_count", len(color_panels) == 8, {"colorized_panels": len(color_panels)}))
    return checks


def verify_claim_package() -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    readme_path = ROOT / "README.md"
    index_path = ROOT / "RUN_INDEX-zh.md"
    repro_path = ROOT / "REPRODUCIBILITY-zh.md"
    dashboard_path = ROOT / "status_dashboard" / "status_dashboard.md"
    dashboard_json_path = ROOT / "status_dashboard" / "status_dashboard.json"
    claim_path = ROOT / "paper-claim-evidence-matrix-zh.md"
    readme_text = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    index_text = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    repro_text = repro_path.read_text(encoding="utf-8") if repro_path.exists() else ""
    text = claim_path.read_text(encoding="utf-8")
    checks.append(ok_item("run_readme_exists", readme_path.exists() and readme_path.stat().st_size > 500, check_file(readme_path)))
    checks.append(ok_item("run_index_exists", index_path.exists() and index_path.stat().st_size > 1000, check_file(index_path)))
    checks.append(ok_item("reproducibility_checklist_exists", repro_path.exists() and repro_path.stat().st_size > 1000, check_file(repro_path)))
    checks.append(ok_item("status_dashboard_md_exists", dashboard_path.exists() and dashboard_path.stat().st_size > 500, check_file(dashboard_path)))
    checks.append(ok_item("status_dashboard_json_exists", dashboard_json_path.exists() and dashboard_json_path.stat().st_size > 500, check_file(dashboard_json_path)))
    checks.append(ok_item("readme_points_to_run_index", "RUN_INDEX-zh.md" in readme_text, "README links run index"))
    checks.append(ok_item("readme_points_to_status_dashboard", "status_dashboard" in readme_text, "README links status dashboard"))
    checks.append(ok_item("readme_points_to_reproducibility", "REPRODUCIBILITY-zh.md" in readme_text, "README links reproducibility checklist"))
    checks.append(ok_item("run_index_has_verify_command", "verify_experiment_package.py" in index_text, "run index includes verifier command"))
    checks.append(ok_item("run_index_points_to_status_dashboard", "status_dashboard" in index_text, "run index links status dashboard"))
    checks.append(ok_item("run_index_points_to_reproducibility", "REPRODUCIBILITY-zh.md" in index_text, "run index links reproducibility checklist"))
    checks.append(ok_item("readme_points_to_hunyuan21_smoke", "m02_hunyuan21_rerun" in readme_text, "README links Hunyuan3D 2.1 smoke rerun"))
    checks.append(ok_item("run_index_points_to_hunyuan21_smoke", "m02-hunyuan21-smoke-results-zh.md" in index_text, "run index links Hunyuan3D 2.1 smoke report"))
    checks.append(ok_item("run_index_points_to_hunyuan21_colorized", "m02-hunyuan21-colorized-projection-results-zh.md" in index_text, "run index links Hunyuan3D 2.1 colorized report"))
    checks.append(ok_item("reproducibility_has_core_commands", "generate_final_figures.py" in repro_text and "generate_remote_inventory.py" in repro_text and "analyze_annotations.py" in repro_text, "repro checklist includes core commands"))
    checks.append(ok_item("reproducibility_mentions_hunyuan_texture_boundary", "Hunyuan3D 2.1" in repro_text and "PBR texture" in repro_text, "repro checklist states Hunyuan texture boundary"))
    if dashboard_json_path.exists():
        dashboard = read_json(dashboard_json_path)
        checks.append(ok_item("status_dashboard_values", dashboard.get("overall", {}).get("automatic_package_status") == "pass" and dashboard.get("m03", {}).get("status") == "complete_for_mainline_draft", {"overall": dashboard.get("overall", {}), "m03": dashboard.get("m03", {})}))
    safe_claims = len(re.findall(r"\| C-M0[23]-", text))
    unsafe_claims = len(re.findall(r"\| U-", text))
    checks.append(ok_item("claim_matrix_exists", claim_path.exists() and claim_path.stat().st_size > 1000, check_file(claim_path)))
    checks.append(ok_item("safe_claim_count", safe_claims >= 8, {"safe_claims": safe_claims}))
    checks.append(ok_item("unsafe_claim_count", unsafe_claims >= 5, {"unsafe_claims": unsafe_claims}))
    checks.append(ok_item("completion_audit_exists", (ROOT / "experiment-completion-audit-zh.md").exists(), check_file(ROOT / "experiment-completion-audit-zh.md")))
    return checks


def verify_artifact_manifest() -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    manifest_dir = ROOT / "artifact_manifest"
    csv_path = manifest_dir / "artifact_manifest_sha256.csv"
    summary_path = manifest_dir / "artifact_manifest_summary.json"
    checks.append(ok_item("artifact_manifest_csv_exists", csv_path.exists() and csv_path.stat().st_size > 1000, check_file(csv_path)))
    checks.append(ok_item("artifact_manifest_summary_exists", summary_path.exists() and summary_path.stat().st_size > 100, check_file(summary_path)))
    if csv_path.exists() and summary_path.exists():
        rows = csv_rows(csv_path)
        summary = read_json(summary_path)
        checks.append(
            ok_item(
                "artifact_manifest_counts_match",
                len(rows) == summary.get("total_files") and summary.get("total_files", 0) >= 100,
                {"csv_rows": len(rows), "summary_total": summary.get("total_files")},
            )
        )
    return checks


def verify_remote_inventory() -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    inv_dir = ROOT / "remote_artifact_inventory"
    json_path = inv_dir / "remote_artifact_inventory.json"
    md_path = inv_dir / "remote_artifact_inventory.md"
    checks.append(ok_item("remote_inventory_json_exists", json_path.exists() and json_path.stat().st_size > 1000, check_file(json_path)))
    checks.append(ok_item("remote_inventory_md_exists", md_path.exists() and md_path.stat().st_size > 1000, check_file(md_path)))
    if json_path.exists():
        data = read_json(json_path)
        items = data.get("items", [])
        checks.append(
            ok_item(
                "remote_inventory_items_exist",
                len(items) == 11 and all(item.get("exists") for item in items),
                {
                    "items": len(items),
                    "existing_items": sum(1 for item in items if item.get("exists")),
                    "total_files": sum(int(item.get("files", 0)) for item in items),
                    "total_bytes": sum(int(item.get("bytes", 0)) for item in items),
                },
            )
        )
    return checks


def verify_external_steps_pack() -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    pack = ROOT / "m02_external_steps_pack"
    artemis_pack = ROOT / "m02_artemis_access_package"
    strict_script = ROOT / "run_m02_strict_followup.py"
    strict_status_json = ROOT / "m02_strict_followup" / "strict_m02_followup_status.json"
    strict_status_md = ROOT / "m02_strict_followup" / "strict_m02_followup_status.md"
    external_check_script = ROOT / "check_external_steps.py"
    external_check_json = pack / "external_step_checks" / "external_completion_check.json"
    external_check_md = pack / "external_step_checks" / "external_completion_check.md"
    required_files = [
        "README-zh.md",
        "artemis_access_request_template-zh.md",
        "artemis_access_live_check-zh.md",
        "artemis_authorization_record_template-zh.md",
        "human_evaluation_protocol-zh.md",
        "rater_invitation_template-zh.md",
        "rater_consent_template-zh.md",
        "rater_metadata_template.csv",
        "human_evaluation_ethics_checklist-zh.md",
        "post_artemis_data_plan-zh.md",
        "external_steps_status.json",
    ]
    checks.append(ok_item("external_completion_check_script", external_check_script.exists() and external_check_script.stat().st_size > 1000, check_file(external_check_script)))
    checks.append(ok_item("strict_m02_followup_script", strict_script.exists() and strict_script.stat().st_size > 1000, check_file(strict_script)))
    checks.append(ok_item("strict_m02_followup_status_json", strict_status_json.exists() and strict_status_json.stat().st_size > 100, check_file(strict_status_json)))
    checks.append(ok_item("strict_m02_followup_status_md", strict_status_md.exists() and strict_status_md.stat().st_size > 100, check_file(strict_status_md)))
    for name in required_files:
        path = pack / name
        checks.append(ok_item(f"external_steps_{name}", path.exists() and path.stat().st_size > 100, check_file(path)))
    checks.append(ok_item("external_completion_check_json", external_check_json.exists() and external_check_json.stat().st_size > 100, check_file(external_check_json)))
    checks.append(ok_item("external_completion_check_md", external_check_md.exists() and external_check_md.stat().st_size > 100, check_file(external_check_md)))
    checks.append(ok_item("artemis_access_package_script", (ROOT / "make_m02_artemis_access_package.py").exists() and (ROOT / "make_m02_artemis_access_package.py").stat().st_size > 1000, check_file(ROOT / "make_m02_artemis_access_package.py")))
    artemis_summary_path = artemis_pack / "artemis_access_package_summary.json"
    artemis_zip_path = artemis_pack / "M02_ArtEmis_access_package.zip"
    checks.append(ok_item("artemis_access_package_summary", artemis_summary_path.exists() and artemis_summary_path.stat().st_size > 100, check_file(artemis_summary_path)))
    checks.append(ok_item("artemis_access_package_zip", artemis_zip_path.exists() and artemis_zip_path.stat().st_size > 1000, check_file(artemis_zip_path)))
    if artemis_summary_path.exists() and artemis_zip_path.exists():
        artemis_summary = read_json(artemis_summary_path)
        with zipfile.ZipFile(artemis_zip_path) as archive:
            names = [entry.filename for entry in archive.infolist()]
        checks.append(
            ok_item(
                "artemis_access_package_contents",
                artemis_summary.get("files_in_zip") == len(names) == 7
                and artemis_summary.get("contains_restricted_data") is False
                and len(names) == len(set(names)),
                {
                    "summary_files": artemis_summary.get("files_in_zip"),
                    "zip_entries": len(names),
                    "contains_restricted_data": artemis_summary.get("contains_restricted_data"),
                    "duplicate_names": len(names) - len(set(names)),
                },
            )
        )
    status_path = pack / "external_steps_status.json"
    if status_path.exists():
        status = read_json(status_path)
        checks.append(
            ok_item(
                "external_steps_artemis_pending",
                status.get("artemis_wikiart_authorization", {}).get("status") == "pending_human_action",
                status.get("artemis_wikiart_authorization", {}).get("status"),
                severity="boundary",
            )
        )
        checks.append(
            ok_item(
                "external_steps_human_eval_pending",
                status.get("human_evaluation", {}).get("status") == "pending_human_evaluators",
                status.get("human_evaluation", {}).get("status"),
                severity="boundary",
            )
        )
    readme_path = pack / "README-zh.md"
    if readme_path.exists():
        readme = readme_path.read_text(encoding="utf-8")
        checks.append(
            ok_item(
                "external_steps_readme_references_ethics_materials",
                "rater_consent_template-zh.md" in readme
                and "rater_metadata_template.csv" in readme
                and "human_evaluation_ethics_checklist-zh.md" in readme
                and "artemis_access_live_check-zh.md" in readme,
                "README references consent, metadata, ethics checklist, and live access check",
            )
        )
    if external_check_json.exists():
        external_check = read_json(external_check_json)
        checks.append(
            ok_item(
                "external_completion_check_pending",
                external_check.get("overall_status") == "pending_external_or_human_steps",
                external_check.get("overall_status"),
                severity="boundary",
            )
        )
    if strict_status_json.exists():
        strict_status = read_json(strict_status_json)
        checks.append(
            ok_item(
                "strict_m02_followup_pending_or_ready",
                strict_status.get("overall_status")
                in {
                    "pending_external_or_human_steps",
                    "human_analysis_complete_pending_artemis",
                    "artemis_ready_pending_human_analysis",
                    "ready_for_authorized_artemis_experiment",
                },
                strict_status.get("overall_status"),
                severity="boundary",
            )
        )
    return checks


def verify_handoff_package() -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    package = ROOT / "handoff_package"
    summary_path = package / "handoff_summary.json"
    manifest_path = package / "handoff_manifest.csv"
    required_files = [
        "HANDOFF_README.md",
        "status_dashboard/status_dashboard.md",
        "RUN_INDEX-zh.md",
        "experiment-completion-audit-zh.md",
        "paper-claim-evidence-matrix-zh.md",
        "final_figures_tables/m03_main100_metric_paradox.svg",
        "m02_external_steps_pack/artemis_access_request_template-zh.md",
        "make_m02_artemis_access_package.py",
        "m02_artemis_access_package/artemis_access_package_summary.json",
        "make_m02_rater_distribution.py",
        "m02_rater_distribution/rater_package_summary.json",
        "m02_human_audit_pack/rater_tracking.csv",
        "m02_human_audit_pack/rater_followup_messages-zh.md",
        "run_m02_strict_followup.py",
        "m02_strict_followup/strict_m02_followup_status.md",
        "m02-emoart100-results-zh.md",
        "final_figures_tables/m02_emoart100_affect_summary.svg",
    ]
    checks.append(ok_item("handoff_summary_exists", summary_path.exists() and summary_path.stat().st_size > 100, check_file(summary_path)))
    checks.append(ok_item("handoff_manifest_exists", manifest_path.exists() and manifest_path.stat().st_size > 100, check_file(manifest_path)))
    for rel in required_files:
        path = package / rel
        checks.append(ok_item(f"handoff_file_{rel}", path.exists() and path.stat().st_size > 100, check_file(path)))
    if summary_path.exists() and manifest_path.exists():
        summary = read_json(summary_path)
        manifest_rows = count_csv(manifest_path)
        actual_files = sum(1 for path in package.rglob("*") if path.is_file())
        checks.append(
            ok_item(
                "handoff_counts_match",
                summary.get("packaged_files") == manifest_rows and summary.get("total_files_on_disk") == actual_files,
                {
                    "packaged_files": summary.get("packaged_files"),
                    "manifest_rows": manifest_rows,
                    "total_files_on_disk": summary.get("total_files_on_disk"),
                    "actual_files": actual_files,
                },
            )
        )
    return checks


def write_reports(checks: list[dict[str, object]]) -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    required = [c for c in checks if c["severity"] == "required"]
    boundary = [c for c in checks if c["severity"] == "boundary"]
    summary = {
        "status": "pass" if all(c["ok"] for c in required) else "fail",
        "required_checks": len(required),
        "required_passed": sum(1 for c in required if c["ok"]),
        "boundary_checks": len(boundary),
        "boundary_passed": sum(1 for c in boundary if c["ok"]),
        "human_or_external_steps_remaining": [
            "ArtEmis/WikiArt authorization and formal data use",
            "Human evaluators filling annotation CSV files",
        ],
        "checks": checks,
    }
    (OUT / "verification_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Experiment Package Verification",
        "",
        f"Status: {summary['status']}",
        f"Required checks: {summary['required_passed']} / {summary['required_checks']}",
        f"Boundary checks: {summary['boundary_passed']} / {summary['boundary_checks']}",
        "",
        "## Remaining Human Or External Steps",
        "",
    ]
    for item in summary["human_or_external_steps_remaining"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Checks", ""])
    for check in checks:
        mark = "PASS" if check["ok"] else "FAIL"
        lines.append(f"- {mark} [{check['severity']}] {check['name']}: `{check['evidence']}`")
    (OUT / "verification_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    checks: list[dict[str, object]] = []
    checks.extend(verify_core_metrics())
    checks.extend(verify_figures_tables())
    checks.extend(verify_human_audit_pack())
    checks.extend(verify_m02_hunyuan21_smoke())
    checks.extend(verify_claim_package())
    checks.extend(verify_artifact_manifest())
    checks.extend(verify_remote_inventory())
    checks.extend(verify_external_steps_pack())
    checks.extend(verify_handoff_package())
    summary = write_reports(checks)
    print(json.dumps({k: v for k, v in summary.items() if k != "checks"}, ensure_ascii=False, indent=2))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
