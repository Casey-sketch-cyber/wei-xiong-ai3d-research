#!/usr/bin/env python3
from __future__ import annotations

import json
import random
from pathlib import Path

import pandas as pd
from PIL import Image


TARGETS = ["Calm", "Excited", "Contentment", "Sad", "Alarmed", "Frustrated", "Happy", "Annoyed"]
COUNTS = {
    "Calm": 16,
    "Excited": 16,
    "Contentment": 16,
    "Sad": 14,
    "Alarmed": 14,
    "Frustrated": 12,
    "Happy": 6,
    "Annoyed": 6,
}


def make_square(src: Path, dst: Path, size: int = 512) -> None:
    image = Image.open(src).convert("RGB")
    image.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (size, size), "white")
    canvas.paste(image, ((size - image.width) // 2, (size - image.height) // 2))
    canvas.save(dst)


def main() -> int:
    base = Path("/root/autodl-tmp/m03/datasets/emoart5k")
    out = Path("/root/autodl-tmp/m03/datasets/emoart5k_m02_sample100")
    img_out = out / "inputs"
    img_out.mkdir(parents=True, exist_ok=True)

    annotations = json.loads((base / "annotation.json").read_text(encoding="utf-8"))
    buckets = {key: [] for key in TARGETS}
    for row in annotations:
        meta = row["description"]["third_section"]
        emotion = meta["dominant_emotion"]
        image_path = base / row["image_path"].replace("\\", "/")
        if emotion in buckets and image_path.exists():
            buckets[emotion].append((row, image_path))

    rng = random.Random(20260604)
    rows = []
    for emotion, count in COUNTS.items():
        values = buckets[emotion]
        rng.shuffle(values)
        if len(values) < count:
            raise RuntimeError(f"Not enough {emotion} samples: need {count}, found {len(values)}")
        for row, image_path in values[:count]:
            safe_id = row["request_id"].replace(" ", "_").replace("/", "_").replace("\\", "_")
            dst = img_out / f"{safe_id}.png"
            make_square(image_path, dst)
            first = row["description"]["first_section"]
            second = row["description"]["second_section"]
            third = row["description"]["third_section"]
            rows.append(
                {
                    "request_id": row["request_id"],
                    "dominant_emotion": emotion,
                    "valence": third.get("emotional_valence"),
                    "arousal": third.get("emotional_arousal_level"),
                    "healing_effects": "|".join(third.get("healing_effects", [])),
                    "image_path": str(image_path),
                    "input_png": str(dst),
                    "description": first.get("description", ""),
                    "emotional_impact": second.get("emotional_impact", ""),
                }
            )

    frame = pd.DataFrame(rows)
    frame.to_csv(out / "sample100_manifest.csv", index=False)
    print("WROTE", out / "sample100_manifest.csv", "rows", len(frame))
    print(frame["dominant_emotion"].value_counts().to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

