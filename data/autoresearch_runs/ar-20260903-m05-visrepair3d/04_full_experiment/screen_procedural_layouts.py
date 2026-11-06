from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from formal_benchmark import CORRUPTIONS, formal_corrupt_scene, make_formal_base_scene
from revealrepair_core import evaluate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-start", type=int, default=4000)
    parser.add_argument("--accepted", type=int, default=20)
    parser.add_argument("--max-candidates", type=int, default=100)
    parser.add_argument("--route-samples", type=int, default=36)
    parser.add_argument("--surface-grid", type=int, default=3)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    accepted = []
    rejected = []
    for candidate_index in range(args.max_candidates):
        seed = args.candidate_start + candidate_index
        try:
            base, labels, metadata = make_formal_base_scene(
                seed,
                route_samples=args.route_samples,
                surface_grid=args.surface_grid,
            )
            losses = []
            for severity in (1, 2, 3):
                for corruption_index, corruption in enumerate(CORRUPTIONS):
                    case_seed = (
                        2_700_000
                        + candidate_index * 1000
                        + severity * 100
                        + corruption_index
                    )
                    corrupted, _, _ = formal_corrupt_scene(
                        base, labels, corruption, severity, case_seed
                    )
                    losses.append(evaluate(corrupted, labels).schedule_loss)
        except Exception as exc:
            rejected.append(
                {
                    "seed": seed,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
            print(f"rejected seed={seed}: {type(exc).__name__}: {exc}", flush=True)
            continue
        accepted.append(
            {
                "seed": seed,
                "layout_metadata": metadata,
                "case_seed_base": 2_700_000 + candidate_index * 1000,
                "minimum_corruption_loss": min(losses),
                "maximum_corruption_loss": max(losses),
            }
        )
        print(
            f"accepted {len(accepted)}/{args.accepted}: seed={seed} "
            f"family={metadata['route_family']} exhibits={metadata['exhibit_count']}",
            flush=True,
        )
        if len(accepted) >= args.accepted:
            break
    payload = {
        "selection_rule": (
            "First seeds in ascending order for which the base scene is hard-valid, "
            "a signed schedule is derivable, and all 5 corruption types x 3 severities "
            "are hard-valid and increase schedule loss. Repair outcomes are not run or "
            "consulted during screening."
        ),
        "candidate_start": args.candidate_start,
        "max_candidates": args.max_candidates,
        "requested": args.accepted,
        "accepted": len(accepted),
        "accepted_layouts": accepted,
        "rejected_layouts": rejected,
        "code_sha256": {
            "screen_procedural_layouts.py": hashlib.sha256(
                Path(__file__).read_bytes()
            ).hexdigest(),
            "formal_benchmark.py": hashlib.sha256(
                Path(__file__).with_name("formal_benchmark.py").read_bytes()
            ).hexdigest(),
            "revealrepair_core.py": hashlib.sha256(
                (Path(__file__).resolve().parents[1] / "03_pilot" / "revealrepair_core.py").read_bytes()
            ).hexdigest(),
        },
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload["manifest_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    with (args.output / "procedural_layout_manifest.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    print(
        json.dumps(
            {
                "accepted": len(accepted),
                "rejected": len(rejected),
                "manifest_sha256": payload["manifest_sha256"],
            },
            indent=2,
        )
    )
    if len(accepted) < args.accepted:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
