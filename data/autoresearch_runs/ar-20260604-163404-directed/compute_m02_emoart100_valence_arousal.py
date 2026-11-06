#!/usr/bin/env python
"""Compute coarse valence/arousal consistency for the M02 EmoArt-100 run."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
METRICS = ROOT / "m02_emoart100_metrics"

EMOTION_AXES = {
    "Calm": ("Positive", "Low"),
    "Excited": ("Positive", "High"),
    "Contentment": ("Positive", "Low"),
    "Sad": ("Negative", "Low"),
    "Alarmed": ("Negative", "High"),
    "Frustrated": ("Negative", "High"),
    "Happy": ("Positive", "High"),
    "Annoyed": ("Negative", "High"),
}


def axis_for(emotion: str) -> tuple[str, str]:
    if emotion not in EMOTION_AXES:
        raise KeyError(f"Unknown emotion: {emotion}")
    return EMOTION_AXES[emotion]


def main() -> int:
    data = pd.read_csv(METRICS / "emoart100_affect_consistency.csv")
    rows = []
    for row in data.to_dict(orient="records"):
        gt_valence = row["valence"]
        gt_arousal = row["arousal"]
        orig_valence, orig_arousal = axis_for(row["orig_top_emotion"])
        render_valence, render_arousal = axis_for(row["render_top_emotion"])
        rows.append(
            {
                "request_id": row["request_id"],
                "dominant_emotion": row["dominant_emotion"],
                "gt_valence": gt_valence,
                "gt_arousal": gt_arousal,
                "orig_top": row["orig_top_emotion"],
                "render_top": row["render_top_emotion"],
                "orig_valence": orig_valence,
                "orig_arousal": orig_arousal,
                "render_valence": render_valence,
                "render_arousal": render_arousal,
                "orig_valence_match": orig_valence == gt_valence,
                "orig_arousal_match": orig_arousal == gt_arousal,
                "render_valence_match": render_valence == gt_valence,
                "render_arousal_match": render_arousal == gt_arousal,
                "render_orig_valence_match": render_valence == orig_valence,
                "render_orig_arousal_match": render_arousal == orig_arousal,
            }
        )

    frame = pd.DataFrame(rows)
    frame.to_csv(METRICS / "emoart100_valence_arousal_consistency.csv", index=False)
    aggregate = {
        "n": int(len(frame)),
        "orig_valence_match_rate": float(frame["orig_valence_match"].mean()),
        "render_valence_match_rate": float(frame["render_valence_match"].mean()),
        "render_orig_valence_match_rate": float(frame["render_orig_valence_match"].mean()),
        "orig_arousal_match_rate": float(frame["orig_arousal_match"].mean()),
        "render_arousal_match_rate": float(frame["render_arousal_match"].mean()),
        "render_orig_arousal_match_rate": float(frame["render_orig_arousal_match"].mean()),
        "by_emotion": frame.groupby("dominant_emotion")
        .agg(
            n=("request_id", "count"),
            orig_valence_match_rate=("orig_valence_match", "mean"),
            render_valence_match_rate=("render_valence_match", "mean"),
            render_orig_valence_match_rate=("render_orig_valence_match", "mean"),
            orig_arousal_match_rate=("orig_arousal_match", "mean"),
            render_arousal_match_rate=("render_arousal_match", "mean"),
            render_orig_arousal_match_rate=("render_orig_arousal_match", "mean"),
        )
        .reset_index()
        .to_dict(orient="records"),
    }
    (METRICS / "emoart100_valence_arousal_aggregate.json").write_text(
        json.dumps(aggregate, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(aggregate, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

