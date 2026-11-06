from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


MODELS = ("triposr", "instantmesh", "hunyuan21", "trellis")
EXPECTED_EVALUATIONS = {
    "triposr": 1020,
    "instantmesh": 1740,
    "hunyuan21": 1740,
    "trellis": 1740,
}
FIGURES = (
    "figure2_main_quantitative_results",
    "figure3_metric_gap_and_representative_cases",
    "figure4_robustness_and_render_diagnostics",
)
FIGURE_EXTENSIONS = (".svg", ".pdf", ".tiff", ".png")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    return parser.parse_args()


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    args = parse_args()
    checks = []

    def check(name: str, condition: bool, detail: object) -> None:
        checks.append({"name": name, "pass": bool(condition), "detail": detail})

    inference = json.loads((args.root / "inference_validation.json").read_text(encoding="utf-8"))
    check("inference_validation", inference.get("all_pass") is True, inference)

    for model in MODELS:
        summary_path = args.root / "evaluation" / model / "evaluation_summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        expected = EXPECTED_EVALUATIONS[model]
        check(
            f"evaluation_{model}",
            summary.get("success") == expected and summary.get("failed") == 0,
            summary,
        )
        calibration = json.loads(
            (args.root / "evaluation" / model / "calibration.json").read_text(encoding="utf-8")
        )
        check(
            f"calibration_{model}",
            calibration.get("calibration_objects")
            == [f"gso_{index:03d}" for index in range(1, 11)],
            calibration.get("calibration_objects"),
        )

    render_summary = json.loads(
        (args.root / "render_diagnostics/render_diagnostics_summary.json").read_text(
            encoding="utf-8"
        )
    )
    check(
        "render_diagnostics",
        render_summary.get("success") == 5040 and render_summary.get("failed") == 0,
        render_summary,
    )

    primary = load_csv(args.root / "analysis/primary_sketch_tests.csv")
    primary_finite = all(
        math.isfinite(float(row[column]))
        for row in primary
        for column in ("mean", "ci99_low", "ci99_high", "p_holm")
    )
    check(
        "primary_table",
        len(primary) == 4
        and {row["model"] for row in primary} == set(MODELS)
        and all(int(row["n_objects"]) == 120 for row in primary)
        and primary_finite,
        primary,
    )

    gate = json.loads(
        (args.root / "analysis/publication_evidence_gate.json").read_text(encoding="utf-8")
    )
    check("publication_gate", gate.get("n_main_objects") == 120, gate)

    selections = load_csv(args.root / "figures/representative_case_selection.csv")
    check(
        "representative_cases",
        len(selections) == 3
        and {row["case_label"] for row in selections} == {"P1", "P2", "L1"}
        and len({row["object_id"] for row in selections}) == 3,
        selections,
    )

    for stem in FIGURES:
        paths = [args.root / "figures" / f"{stem}{extension}" for extension in FIGURE_EXTENSIONS]
        check(
            f"figure_{stem}",
            all(path.exists() and path.stat().st_size > 1000 for path in paths),
            {str(path): path.stat().st_size if path.exists() else 0 for path in paths},
        )

    failures = [row for row in checks if not row["pass"]]
    output = {"all_pass": not failures, "checks": checks, "failures": failures}
    (args.root / "final_validation.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

