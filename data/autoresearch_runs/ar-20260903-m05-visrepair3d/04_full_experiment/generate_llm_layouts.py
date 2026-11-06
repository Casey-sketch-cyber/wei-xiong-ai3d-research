from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import sys
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from formal_benchmark import make_formal_base_scene


SYSTEM_PROMPT = """You are a computational exhibition-layout planner. Produce one diverse, plausible parameter specification for a single-room exhibition. The specification will be checked automatically for route clearance, collisions, visibility schedules, and bounds. Return a single JSON object and no markdown or commentary."""

USER_PROMPT = """Create exhibition layout proposal number {index}.

For balanced scientific sampling, route_family MUST be {required_route_family}
and exhibit_count MUST be {required_exhibit_count}. You still choose all other
values and the exhibition theme.

Return exactly these fields:
- theme: a short English exhibition theme, 4 to 12 words
- room_width: number from 15.5 to 20.5 metres
- room_depth: number from 9.5 to 12.5 metres
- route_family: exactly one of straight, arc, serpentine
- route_amplitude: number from 0.08 to 0.55 metres
- exhibit_count: integer 3, 4, or 5
- exhibit_scale: number from 0.82 to 1.18
- screen_depth: number from 2.20 to 2.85 metres
- screen_offset_x: number from 1.15 to 1.55 metres
- screen_offset_y: number from 2.00 to 2.60 metres

Vary the geometry and theme across proposals. Output JSON only."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--accepted", type=int, default=12)
    parser.add_argument("--max-attempts", type=int, default=36)
    parser.add_argument("--seed", type=int, default=20260904)
    parser.add_argument("--max-new-tokens", type=int, default=240)
    parser.add_argument("--local-files-only", action="store_true")
    return parser.parse_args()


def extract_json(text: str) -> dict[str, Any]:
    start = text.find("{")
    if start < 0:
        raise ValueError("response contains no JSON object")
    value, _ = json.JSONDecoder().raw_decode(text[start:])
    if not isinstance(value, dict):
        raise ValueError("response JSON is not an object")
    return value


def require_number(value: Any, low: float, high: float, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} is not numeric")
    numeric = float(value)
    if not low <= numeric <= high:
        raise ValueError(f"{field} is outside [{low}, {high}]")
    return numeric


def validate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    required = {
        "theme",
        "room_width",
        "room_depth",
        "route_family",
        "route_amplitude",
        "exhibit_count",
        "exhibit_scale",
        "screen_depth",
        "screen_offset_x",
        "screen_offset_y",
    }
    if set(candidate) != required:
        missing = sorted(required - set(candidate))
        extra = sorted(set(candidate) - required)
        raise ValueError(f"field mismatch; missing={missing}, extra={extra}")
    theme = str(candidate["theme"]).strip()
    if not 4 <= len(theme.split()) <= 12:
        raise ValueError("theme must contain 4 to 12 words")
    route_family = str(candidate["route_family"]).strip().lower()
    if route_family not in {"straight", "arc", "serpentine"}:
        raise ValueError("route_family is invalid")
    exhibit_value = candidate["exhibit_count"]
    if isinstance(exhibit_value, bool) or int(exhibit_value) != float(exhibit_value):
        raise ValueError("exhibit_count is not an integer")
    exhibit_count = int(exhibit_value)
    if exhibit_count not in {3, 4, 5}:
        raise ValueError("exhibit_count is invalid")
    return {
        "theme": theme,
        "room_width": require_number(candidate["room_width"], 15.5, 20.5, "room_width"),
        "room_depth": require_number(candidate["room_depth"], 9.5, 12.5, "room_depth"),
        "route_family": route_family,
        "route_amplitude": require_number(
            candidate["route_amplitude"], 0.08, 0.55, "route_amplitude"
        ),
        "exhibit_count": exhibit_count,
        "exhibit_scale": require_number(
            candidate["exhibit_scale"], 0.82, 1.18, "exhibit_scale"
        ),
        "screen_depth": require_number(
            candidate["screen_depth"], 2.20, 2.85, "screen_depth"
        ),
        "screen_offset_x": require_number(
            candidate["screen_offset_x"], 1.15, 1.55, "screen_offset_x"
        ),
        "screen_offset_y": require_number(
            candidate["screen_offset_y"], 2.00, 2.60, "screen_offset_y"
        ),
    }


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    tokenizer = AutoTokenizer.from_pretrained(
        args.model, local_files_only=args.local_files_only
    )
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
        local_files_only=args.local_files_only,
    ).to("cuda")
    model.eval()

    raw_path = args.output / "raw_generations.jsonl"
    rejection_path = args.output / "rejections.jsonl"
    accepted: list[dict[str, Any]] = []
    seen: set[str] = set()
    for attempt in range(args.max_attempts):
        stratum_index = len(accepted)
        required_route_family = ["straight", "arc", "serpentine"][stratum_index % 3]
        required_exhibit_count = 3 + (
            (stratum_index % 3 + stratum_index // 3) % 3
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT.format(
                    index=attempt + 1,
                    required_route_family=required_route_family,
                    required_exhibit_count=required_exhibit_count,
                ),
            },
        ]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        torch.manual_seed(args.seed + attempt)
        torch.cuda.manual_seed_all(args.seed + attempt)
        with torch.inference_mode():
            generated = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=True,
                temperature=0.85,
                top_p=0.92,
                repetition_penalty=1.03,
                pad_token_id=tokenizer.eos_token_id,
            )
        response = tokenizer.decode(
            generated[0, inputs["input_ids"].shape[1] :], skip_special_tokens=True
        ).strip()
        raw_record = {
            "attempt": attempt,
            "generation_seed": args.seed + attempt,
            "response": response,
            "response_sha256": hashlib.sha256(response.encode("utf-8")).hexdigest(),
        }
        append_jsonl(raw_path, raw_record)
        try:
            candidate = validate_candidate(extract_json(response))
            if candidate["route_family"] != required_route_family:
                raise ValueError(
                    f"route_family did not match stratum {required_route_family}"
                )
            if candidate["exhibit_count"] != required_exhibit_count:
                raise ValueError(
                    f"exhibit_count did not match stratum {required_exhibit_count}"
                )
            signature = json.dumps(candidate, sort_keys=True, separators=(",", ":"))
            if signature in seen:
                raise ValueError("duplicate layout proposal")
            layout_seed = 9000 + attempt
            layout_id = f"qwen25_7b_{len(accepted):03d}"
            candidate.update(
                {
                    "layout_id": layout_id,
                    "source": "llm",
                    "seed": layout_seed,
                    "raw_attempt": attempt,
                    "raw_response_sha256": raw_record["response_sha256"],
                }
            )
            _, _, geometry_metadata = make_formal_base_scene(
                layout_seed,
                source="llm",
                overrides=candidate,
                route_samples=36,
                surface_grid=3,
            )
            candidate["geometry_generation_attempt"] = geometry_metadata[
                "generation_attempt"
            ]
        except Exception as exc:
            append_jsonl(
                rejection_path,
                {
                    "attempt": attempt,
                    "response_sha256": raw_record["response_sha256"],
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
            print(f"rejected attempt={attempt}: {type(exc).__name__}: {exc}", flush=True)
            continue
        seen.add(signature)
        accepted.append(candidate)
        print(
            f"accepted {len(accepted)}/{args.accepted}: {layout_id} "
            f"family={candidate['route_family']} exhibits={candidate['exhibit_count']}",
            flush=True,
        )
        if len(accepted) >= args.accepted:
            break

    manifest = {
        "model": args.model,
        "model_commit": getattr(model.config, "_commit_hash", None),
        "generation_seed": args.seed,
        "sampling_design": "balanced cyclic route_family x exhibit_count strata",
        "system_prompt": SYSTEM_PROMPT,
        "user_prompt_template": USER_PROMPT,
        "requested": args.accepted,
        "accepted": len(accepted),
        "attempted": min(args.max_attempts, attempt + 1),
        "accepted_layouts": accepted,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "torch": torch.__version__,
            "transformers": __import__("transformers").__version__,
            "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0),
        },
    }
    with (args.output / "llm_layout_manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
    print(json.dumps({"accepted": len(accepted), "attempted": manifest["attempted"]}), flush=True)
    if len(accepted) < args.accepted:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
