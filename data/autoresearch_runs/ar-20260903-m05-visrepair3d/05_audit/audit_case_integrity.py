from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any


PILOT_DIR = Path(__file__).resolve().parents[1] / "03_pilot"
if str(PILOT_DIR) not in sys.path:
    sys.path.insert(0, str(PILOT_DIR))
FORMAL_DIR = Path(__file__).resolve().parents[1] / "04_full_experiment"
if str(FORMAL_DIR) not in sys.path:
    sys.path.insert(0, str(FORMAL_DIR))

from revealrepair_core import Action, Box, Scene, apply_actions, evaluate, wrap_angle
from formal_benchmark import FORMAL_ROTATION_DEGREES, FORMAL_TRANSLATION_STEPS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-cases", type=int)
    return parser.parse_args()


def scene_from_dict(value: dict[str, Any]) -> Scene:
    return Scene(
        scene_id=str(value["scene_id"]),
        room=[float(item) for item in value["room"]],
        route=[[float(item) for item in point] for point in value["route"]],
        objects=[Box(**item) for item in value["objects"]],
        exhibit_order=[str(item) for item in value["exhibit_order"]],
        protected_order=[str(item) for item in value["protected_order"]],
        surface_grid=int(value.get("surface_grid", 3)),
        path_check_step=float(value.get("path_check_step", 0.18)),
    )


def scene_matches(first: Scene, second: Scene, tolerance: float = 1e-9) -> bool:
    if first.room != second.room or first.exhibit_order != second.exhibit_order:
        return False
    first_objects = first.object_map()
    second_objects = second.object_map()
    if set(first_objects) != set(second_objects):
        return False
    for object_id in first_objects:
        a = first_objects[object_id]
        b = second_objects[object_id]
        if any(abs(x - y) > tolerance for x, y in zip(a.center, b.center, strict=True)):
            return False
        if any(abs(x - y) > tolerance for x, y in zip(a.size, b.size, strict=True)):
            return False
        if abs(wrap_angle(a.yaw - b.yaw)) > tolerance:
            return False
    return True


def action_is_on_search_grid(action: Action) -> bool:
    components = [
        ("translation", action.dx),
        ("translation", action.dy),
        ("rotation", action.dyaw),
    ]
    nonzero = [(kind, value) for kind, value in components if abs(value) > 1e-9]
    if len(nonzero) != 1:
        return False
    kind, value = nonzero[0]
    if kind == "translation":
        return any(
            math.isclose(abs(value), step, rel_tol=0.0, abs_tol=1e-9)
            for step in FORMAL_TRANSLATION_STEPS
        )
    degrees = abs(math.degrees(value))
    return any(
        math.isclose(degrees, step, rel_tol=0.0, abs_tol=1e-9)
        for step in FORMAL_ROTATION_DEGREES
    )


def audit_case(case: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    base = scene_from_dict(case["base"])
    corrupted = scene_from_dict(case["corrupted"])
    labels = {
        key: [int(value) for value in values]
        for key, values in case["labels"].items()
    }
    inverse = [Action(**value) for value in case["known_inverse"]]
    recovered = apply_actions(corrupted, inverse)
    base_eval = evaluate(base, labels)
    corrupt_eval = evaluate(corrupted, labels)
    recovered_eval = evaluate(recovered, labels)

    if set(labels) != set(base.exhibit_order):
        errors.append("label_target_set_mismatch")
    if any(len(values) != len(base.route) for values in labels.values()):
        errors.append("label_route_length_mismatch")
    if not base_eval.hard_valid:
        errors.append("base_not_hard_valid")
    if base_eval.schedule_loss > 1e-12:
        errors.append("base_schedule_loss_nonzero")
    if not corrupt_eval.hard_valid:
        errors.append("corruption_not_hard_valid")
    if corrupt_eval.schedule_loss <= base_eval.schedule_loss + 1e-6:
        errors.append("corruption_did_not_increase_loss")
    metadata_all_components_off_grid = bool(
        case.get("corruption_metadata", {}).get("off_grid")
    )
    inverse_grid_flags = [action_is_on_search_grid(action) for action in inverse]
    complete_inverse_on_grid = bool(inverse_grid_flags) and all(inverse_grid_flags)
    if case["corruption"] != "compound" and not metadata_all_components_off_grid:
        errors.append("single_fault_corruption_has_grid_overlap")
    if complete_inverse_on_grid:
        errors.append("complete_known_inverse_available_in_search_grid")
    if not scene_matches(base, recovered):
        errors.append("known_inverse_did_not_restore_state")
    if not recovered_eval.hard_valid:
        errors.append("recovered_state_not_hard_valid")
    if not math.isclose(
        recovered_eval.schedule_loss,
        base_eval.schedule_loss,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        errors.append("known_inverse_did_not_restore_loss")
    return errors, {
        "metadata_all_components_off_grid": metadata_all_components_off_grid,
        "inverse_action_on_grid": inverse_grid_flags,
        "complete_inverse_on_grid": complete_inverse_on_grid,
    }


def main() -> None:
    args = parse_args()
    with args.cases.open("r", encoding="utf-8") as handle:
        all_cases = json.load(handle)
    cases = all_cases[: args.max_cases] if args.max_cases is not None else all_cases
    failures = []
    partial_grid_overlap_cases = []
    complete_inverse_on_grid_cases = []
    strata = Counter()
    layout_ids = set()
    for index, case in enumerate(cases, start=1):
        metadata = case["layout_metadata"]
        source = str(metadata["source"])
        layout_id = str(metadata["layout_id"])
        strata[(source, str(case["corruption"]), int(case["severity"]))] += 1
        layout_ids.add((source, layout_id))
        errors, diagnostics = audit_case(case)
        if not diagnostics["metadata_all_components_off_grid"]:
            partial_grid_overlap_cases.append(
                {
                    "case_id": case["case_id"],
                    "corruption": case["corruption"],
                    "severity": case["severity"],
                    "inverse_action_on_grid": diagnostics["inverse_action_on_grid"],
                }
            )
        if diagnostics["complete_inverse_on_grid"]:
            complete_inverse_on_grid_cases.append(case["case_id"])
        if errors:
            failures.append({"case_id": case["case_id"], "errors": errors})
        if index % 50 == 0 or index == len(cases):
            print(f"audited {index}/{len(cases)} cases", flush=True)

    case_ids = [str(case["case_id"]) for case in cases]
    source_layout_counts = Counter(source for source, _ in layout_ids)
    corruptions = (
        "premature_reveal",
        "missed_reveal",
        "back_facing",
        "target_displacement",
        "compound",
    )
    checks = {
        "all_case_ids_unique": len(case_ids) == len(set(case_ids)),
        "every_case_passes_geometry_and_inverse_checks": not failures,
        "all_single_fault_corruptions_fully_off_grid": not any(
            item["corruption"] != "compound" for item in partial_grid_overlap_cases
        ),
        "no_complete_known_inverse_available_in_search_grid": not complete_inverse_on_grid_cases,
    }
    if args.max_cases is None:
        checks["all_fifteen_source_strata_present"] = all(
            all((source, corruption, severity) in strata for corruption in corruptions
                for severity in (1, 2, 3))
            for source in {key[0] for key in strata}
        )
        checks["strata_balanced_with_source_layout_counts"] = all(
            strata[(source, corruption, severity)] == layout_count
            for source, layout_count in source_layout_counts.items()
            for corruption in corruptions
            for severity in (1, 2, 3)
        )
    report = {
        "input_sha256": hashlib.sha256(args.cases.read_bytes()).hexdigest(),
        "audited_cases": len(cases),
        "source_layout_count": dict(
            source_layout_counts
        ),
        "strata_counts": {
            f"{source}|{corruption}|s{severity}": count
            for (source, corruption, severity), count in sorted(strata.items())
        },
        "checks": checks,
        "failure_count": len(failures),
        "failures": failures,
        "partial_grid_overlap_count": len(partial_grid_overlap_cases),
        "partial_grid_overlap_cases": partial_grid_overlap_cases,
        "complete_inverse_on_grid_count": len(complete_inverse_on_grid_cases),
        "complete_inverse_on_grid_cases": complete_inverse_on_grid_cases,
        "all_checks_pass": all(checks.values()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    if not report["all_checks_pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
