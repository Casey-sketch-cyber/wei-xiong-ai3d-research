#!/usr/bin/env python3
"""Figure 2 (method pipeline), drawn under the FigGenie contract and checked with its check.py.

    FIGGENIE=<path to skills/figgenie-paper-diagram> python3 make_fig2.py   # writes spec.json and fig.svg here
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "fig1"))
import make_fig1 as F  # noqa: E402  (shared helpers, palette and fonts)

W, H = 495, 144
INPUT_TINT, INPUT_EDGE = "#FFF8E1", "#D6B656"
PIXEL_TINT, PIXEL_EDGE = "#EDEDED", "#A6A6A6"
SW, GAP = 75, 9
OUT = ' data-label="outside"'
TOP, BOT = 19, 134


def museum(cx, cy):
    """A plain museum glyph: pediment, three columns, base."""
    return (f'<g data-symbol="museum"><path d="M{cx - 7:.2f} {cy - 3:.2f} L{cx:.2f} {cy - 7.5:.2f} '
            f'L{cx + 7:.2f} {cy - 3:.2f} Z" fill="none" stroke="{F.MUTED}" stroke-width="0.6" stroke-linejoin="round"/>'
            + "".join(f'<rect x="{cx + dx - 0.8:.2f}" y="{cy - 2:.2f}" width="1.6" height="6.5" fill="{F.MUTED}"/>'
                      for dx in (-4.5, 0, 4.5))
            + f'<rect x="{cx - 7:.2f}" y="{cy + 5:.2f}" width="14" height="1.3" fill="{F.MUTED}"/></g>')


def lock(cx, cy):
    return (f'<g data-symbol="lock"><path d="M{cx - 1.9:.2f} {cy - 1:.2f} V{cy - 2.6:.2f} '
            f'A1.9 1.9 0 0 1 {cx + 1.9:.2f} {cy - 2.6:.2f} V{cy - 1:.2f}" fill="none" stroke="{F.MUTED}" '
            f'stroke-width="0.6"/><rect x="{cx - 2.9:.2f}" y="{cy - 1:.2f}" width="5.8" height="4.4" rx="0.6" '
            f'fill="{F.MUTED}"/></g>')


def badge(x, y, letter):
    return (f'<g data-symbol="badge"><circle cx="{x:.2f}" cy="{y:.2f}" r="4.2" fill="#FFFFFF" stroke="{F.RED}" '
            f'stroke-width="0.7"/>{F.text(x, y + 2.2, letter, F.S_BODY, F.RED, True, "middle")}</g>')


def build():
    body, nodes, edges, containers, annotations = [], [], [], [], []
    xs = [i * (SW + GAP) for i in range(6)]
    stages = [("cohorts", "Cohorts", INPUT_TINT, INPUT_EDGE),
              ("crops", "Crop + losses", INPUT_TINT, INPUT_EDGE),
              ("input", "Shared input", INPUT_TINT, INPUT_EDGE),
              ("models", "Models", "#FFFFFF", F.RULE),
              ("composite", "Composite", "#FFFFFF", F.RULE),
              ("score", "Score", "#FFFFFF", F.RULE)]
    for (cid, title, fill, edge), x in zip(stages, xs):
        body.append(f'<g id="c:{cid}" data-kind="container" data-role="existing">'
                    f'<rect x="{x}" y="{TOP}" width="{SW}" height="{BOT - TOP}" rx="3" fill="{fill}" stroke="{edge}" '
                    f'stroke-width="0.6"/>{F.centred(title, (x, TOP + 1.5, SW, 10), F.S_TITLE, F.INK, True)}</g>')
        containers.append({"id": cid, "label": title, "role": "novel" if cid == "input" else "existing"})

    # timeline over the stages
    def span(x0, x1, label, icon=None):
        y = 9.5
        g = [f'<path d="M{x0 + 1:.2f} {y + 4:.2f} V{y + 6:.2f} H{x1 - 1:.2f} V{y + 4:.2f}" fill="none" '
             f'stroke="{F.RULE}" stroke-width="0.6"/>']
        lw = F.tw(label, F.S_BODY) + (8 if icon else 0)
        lx = (x0 + x1 - lw) / 2
        if icon:
            g.append(icon(lx + 2.9, y - 1.2))
            lx += 8
        g.append(F.text(lx, y + 0.8, label, fill=F.MUTED))
        return "".join(g)
    body.append(f'<g id="a:timeline" data-kind="annotation">'
                f'{span(xs[0], xs[2] + SW, "protocol committed before inference", lock)}'
                f'{span(xs[3], xs[3] + SW, "inference")}'
                f'{span(xs[4], xs[5] + SW, "automatic scoring, no human raters")}</g>')
    annotations.append({"id": "timeline", "kind": "label", "text": "protocol committed before inference / "
                        "inference / automatic scoring, no human raters"})

    # 1 cohorts
    x = xs[0]
    body.append(f'<g id="n:museums" data-kind="node" data-role="input" data-parent="cohorts">'
                f'{museum(x + 22, 47)}{museum(x + 53, 47)}'
                f'{F.text(x + 22, 64, "CMA 60", fill=F.INK, anchor="middle", extra=OUT)}'
                f'{F.text(x + 53, 64, "AIC 60", fill=F.INK, anchor="middle", extra=OUT)}</g>')
    nodes.append({"id": "museums", "label": "CMA 60 AIC 60", "kind": "icon", "parent": "cohorts"})
    media = ["oil on canvas", "oil on wood", "watercolour, paper", "ink, paper"]
    lines = "".join(F.text(x + SW / 2, 82 + 9 * i, m, fill=F.MUTED, anchor="middle") for i, m in enumerate(media))
    body.append(f'<g id="n:media" data-kind="node" data-role="note" data-parent="cohorts">{lines}'
                f'{F.text(x + SW / 2, 82 + 9 * 4 + 1, "15 works each", fill=F.INK, anchor="middle")}</g>')
    nodes.append({"id": "media", "label": " ".join(media) + " 15 works each", "kind": "note", "parent": "cohorts"})

    # 2 crop + masks
    x = xs[1]
    body.append(f'<g id="n:crop" data-kind="node" data-role="input" data-parent="crops">'
                f'{F.image(x + (SW - 34) / 2, 31, 34, 34, "f2_crop.png")}'
                f'{F.text(x + SW / 2, 73, "512 px, no resampling", fill=F.MUTED, anchor="middle")}</g>')
    nodes.append({"id": "crop", "label": "512 px, no resampling", "kind": "image", "parent": "crops",
                  "image": {"src": "f2_crop.png", "role": "data-thumbnail"}})
    t, g0 = 15, 3
    gx = x + (SW - (3 * t + 2 * g0)) / 2
    tiles = []
    for c, fam in enumerate(("crack", "flake", "loss")):
        for r, area in enumerate((1, 5)):
            tiles.append(F.image(gx + c * (t + g0), 80 + r * (t + g0), t, t, f"f2_mask_{fam}_{area}.png"))
        tiles.append(F.text(gx + c * (t + g0) + t / 2, 80 + 2 * t + g0 + 8, fam, fill=F.MUTED, anchor="middle"))
    tiles.append(F.text(gx - 2.5, 80 + t / 2 + 2.2, "1%", fill=F.MUTED, anchor="end"))
    tiles.append(F.text(gx - 2.5, 80 + t + g0 + t / 2 + 2.2, "5%", fill=F.MUTED, anchor="end"))
    body.append(f'<g id="n:masks" data-kind="node" data-role="input" data-parent="crops">{"".join(tiles)}</g>')
    nodes.append({"id": "masks", "label": "crack flake loss 1% 5%", "kind": "image", "parent": "crops",
                  "image": {"src": "f2_mask_crack_5.png", "role": "data-thumbnail"}})

    # 3 shared input
    x = xs[2]
    body.append(f'<g id="n:aligned" data-kind="node" data-role="novel" data-parent="input">'
                f'{F.image(x + (SW - 46) / 2, 31, 46, 46, "f2_input.png")}'
                f'{F.text(x + SW / 2, 88, "hole expanded to", fill=F.INK, anchor="middle")}'
                f'{F.text(x + SW / 2, 97, "whole 8×8 cells", fill=F.INK, anchor="middle")}'
                f'{F.text(x + SW / 2, 110, "same input for", fill=F.MUTED, anchor="middle")}'
                f'{F.text(x + SW / 2, 119, "all four models", fill=F.MUTED, anchor="middle")}</g>')
    nodes.append({"id": "aligned", "label": "hole expanded to whole 8×8 cells same input for all four models",
                  "kind": "image", "parent": "input", "image": {"src": "f2_input.png", "role": "sample-input"}})
    body.append(f'<g id="a:mark-a" data-kind="annotation" data-anchor="input">{badge(x + SW - 7, TOP + 7, "a")}</g>')
    annotations.append({"id": "mark-a", "kind": "verdict", "text": "a", "anchor": "input"})

    # 4 models
    x = xs[3]
    groups = [("pixel", "pixel space", PIXEL_TINT, PIXEL_EDGE, F.MODELS[:2], 31),
              ("latent", "latent space", F.BLUE_TINT, F.BLUE, F.MODELS[2:], 72)]
    for gid, glab, tint, edge, models, y0 in groups:
        rows = "".join(f'{F.marker(shape, x + 11, y0 + 17 + 10 * i - 2.4, 2.1, col)}'
                       f'{F.text(x + 16, y0 + 17 + 10 * i, name, F.S_BODY, F.INK, True)}'
                       for i, (name, col, shape) in enumerate(models))
        body.append(f'<g id="n:{gid}" data-kind="node" data-role="module" data-parent="models">'
                    f'<rect x="{x + 5}" y="{y0}" width="{SW - 10}" height="34" rx="2" fill="{tint}" stroke="{edge}" '
                    f'stroke-width="0.5"/>{F.text(x + 9, y0 + 7.6, glab, fill=F.MUTED)}{rows}</g>')
        nodes.append({"id": gid, "label": glab + " " + " ".join(m[0] for m in models), "kind": "module",
                      "parent": "models"})
    body.append(f'<g id="n:seed" data-kind="node" data-role="note" data-parent="models">'
                f'{F.text(x + SW / 2, 117, "seed 2026", fill=F.MUTED, anchor="middle")}'
                f'{F.text(x + SW / 2, 126, "one RTX 3090", fill=F.MUTED, anchor="middle")}</g>')
    nodes.append({"id": "seed", "label": "seed 2026 one RTX 3090", "kind": "note", "parent": "models"})
    body.append(f'<g id="a:mark-b" data-kind="annotation" data-anchor="models">{badge(x + SW - 7, TOP + 7, "b")}</g>')
    annotations.append({"id": "mark-b", "kind": "verdict", "text": "b", "anchor": "models"})

    # 5 composite
    x = xs[4]
    body.append(f'<g id="n:output" data-kind="node" data-role="output" data-parent="composite">'
                f'{F.image(x + (SW - 46) / 2, 31, 46, 46, "f2_output.png")}'
                f'{F.text(x + SW / 2, 88, "generated pixels", fill=F.INK, anchor="middle")}'
                f'{F.text(x + SW / 2, 97, "kept only in the", fill=F.INK, anchor="middle")}'
                f'{F.text(x + SW / 2, 106, "original hole", fill=F.INK, anchor="middle")}</g>')
    nodes.append({"id": "output", "label": "generated pixels kept only in the original hole", "kind": "image",
                  "parent": "composite", "image": {"src": "f2_output.png", "role": "sample-output"}})

    # 6 score + ledger
    x = xs[5]
    for i, (mid, m, sub) in enumerate((("mae", "MAE", ""), ("de", "\u0394E", "00"), ("lpips", "LPIPS", ""),
                                       ("dists", "DISTS", ""))):
        cxp, cyp = x + 6 + (i % 2) * 33, 31 + (i // 2) * 13
        p = F.place(m + sub, (cxp, cyp, 30, 10.5), size=F.S_BODY, font=F.FONT, bold=True)
        lab = (F.esc(m) + (f'<tspan font-size="5" dy="1.4">{sub}</tspan>' if sub else ""))
        body.append(f'<g id="n:metric-{mid}" data-kind="node" data-role="module" data-parent="score">'
                    f'<rect x="{cxp}" y="{cyp}" width="30" height="10.5" rx="2" fill="#FFFFFF" stroke="{F.RULE}" '
                    f'stroke-width="0.5"/><text x="{cxp + 15:.2f}" y="{p["y"]:.2f}" font-size="{F.S_BODY}" '
                    f'font-weight="bold" fill="{F.INK}" text-anchor="middle">{lab}</text></g>')
        nodes.append({"id": f"metric-{mid}", "label": m + sub, "kind": "module", "parent": "score"})
    rows = []
    for i, (lab, col) in enumerate((("planned", None), ("scored", "#D0D4DA"), ("withheld", F.RED))):
        ry = 66 + i * 10
        if col:
            rows.append(f'<rect x="{x + 10:.2f}" y="{ry - 4.2:.2f}" width="4.2" height="4.2" fill="{col}"/>')
        else:
            rows.append(f'<rect x="{x + 10:.2f}" y="{ry - 4.2:.2f}" width="4.2" height="4.2" fill="none" '
                        f'stroke="{F.MUTED}" stroke-width="0.5"/>')
        rows.append(F.text(x + 17, ry, lab, fill=F.INK))
    body.append(f'<g id="n:ledger" data-kind="node" data-role="module" data-parent="score">'
                f'<rect x="{x + 6}" y="57" width="{SW - 12}" height="32" rx="2" fill="#FFFFFF" stroke="{F.RULE}" '
                f'stroke-width="0.5"/>{"".join(rows)}</g>')
    nodes.append({"id": "ledger", "label": "planned scored withheld", "kind": "module", "parent": "score"})
    body.append(f'<g id="n:stats" data-kind="node" data-role="note" data-parent="score">'
                f'{F.text(x + SW / 2, 101, "per model, museum", fill=F.MUTED, anchor="middle")}'
                f'{F.text(x + SW / 2, 113, "paired bootstrap", fill=F.INK, anchor="middle")}'
                f'{F.text(x + SW / 2, 122, "over artworks", fill=F.INK, anchor="middle")}</g>')
    nodes.append({"id": "stats", "label": "per model, museum paired bootstrap over artworks", "kind": "note",
                  "parent": "score"})
    body.append(f'<g id="a:mark-c" data-kind="annotation" data-anchor="score">{badge(x + SW - 7, TOP + 7, "c")}</g>')
    annotations.append({"id": "mark-c", "kind": "verdict", "text": "c", "anchor": "score"})

    # hand-offs between stages
    for i in range(5):
        a, b = stages[i][0], stages[i + 1][0]
        y = 76
        body.append(f'<g id="e:{a}-{b}" data-kind="edge" data-from="{a}" data-to="{b}" data-edge-kind="data">'
                    f'<path d="M{xs[i] + SW + 0.6:.2f} {y} H{xs[i + 1] - 1.4:.2f}" fill="none" stroke="{F.MUTED}" '
                    f'stroke-width="0.7" marker-end="url(#arrow)"/></g>')
        edges.append({"id": f"{a}-{b}", "from": a, "to": b, "kind": "data"})

    defs = (f'<defs><marker id="arrow" viewBox="0 0 6 6" refX="5" refY="3" markerWidth="5" markerHeight="5" '
            f'orient="auto-start-reverse" markerUnits="userSpaceOnUse"><path d="M0 0.6 L5.4 3 L0 5.4 Z" '
            f'fill="{F.MUTED}"/></marker></defs>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}pt" height="{H}pt" '
           f'font-family="{F.STACK}" font-size="{F.S_BODY}" data-spec="fig2-pipeline" data-spec-version="1">'
           f'{defs}<rect x="0" y="0" width="{W}" height="{H}" fill="#FFFFFF"/>{"".join(body)}</svg>')
    spec = {"meta": {"id": "fig2-pipeline", "title": "Evaluation pipeline", "family": "ai", "venue": "cvpr",
                     "kind": "architecture", "figure_kind": "whole-system", "column": "double", "width_pt": W,
                     "max_height_pt": H, "template": "ai", "direction": "left-right", "palette": "office-pastel",
                     "font": F.FONT, "step_markers": "none", "language": "en", "version": 1,
                     "caption_draft": "Evaluation pipeline. Crops from two open-access collections receive six "
                     "procedural losses; every model sees the same 8x8-aligned input; generated pixels are kept only "
                     "in the original hole and scored against the recorded crop, with planned, scored and withheld "
                     "conditions counted per model. Letters mark where the three protocol choices of Figure 1 act.",
                     "ai": {"kinds": ["stage-pipeline"], "variant": "stage-chain", "subfield": "vision",
                            "arrangement": "pipeline-row", "grouping": ["framed-boxes", "tinted-regions"],
                            "samples": "image", "materials": ["the Figure 1 case's crop, masks and a composite"]}},
            "containers": containers, "nodes": nodes, "edges": edges, "annotations": annotations,
            "legend": {"mode": "none"}}
    return svg, spec


if __name__ == "__main__":
    svg, spec = build()
    (HERE / "fig.svg").write_text(svg)
    (HERE / "spec.json").write_text(json.dumps(spec, indent=1, ensure_ascii=False))
    print("wrote", HERE / "fig.svg")
