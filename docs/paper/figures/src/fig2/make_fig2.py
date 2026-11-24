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

D = 119                               # second row offset (snake layout: row 2 runs right to left)
W, H = 3 * 75 + 2 * 9, 112 + D + 4
INPUT_TINT, INPUT_EDGE = "#FFF8E1", "#D6B656"
PIXEL_TINT, PIXEL_EDGE = "#EDEDED", "#A6A6A6"
SW, GAP = 75, 9
OUT = ' data-label="outside"'
TOP, BOT = 19, 112


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
    """Pictures and short names only; the three protocol controls are the only coloured parts."""
    body, nodes, edges, containers, annotations = [], [], [], [], []
    col = [i * (SW + GAP) for i in range(3)]
    xs = [col[0], col[1], col[2], col[2], col[1], col[0]]
    dys = [0, 0, 0, D, D, D]
    NOVEL = ("input",)
    stages = [("cohorts", "Cohorts"), ("crops", "Crops + losses"), ("input", "Aligned input"),
              ("models", "Models"), ("composite", "Composite"), ("score", "Score")]
    for (cid, title), x, dy in zip(stages, xs, dys):
        fill, edge = (F.BLUE_TINT, F.BLUE) if cid in NOVEL else ("#FFFFFF", F.RULE)
        body.append(f'<g id="c:{cid}" data-kind="container" data-role="{"novel" if cid in NOVEL else "existing"}">'
                    f'<rect x="{x}" y="{TOP + dy}" width="{SW}" height="{BOT - TOP}" rx="3" fill="{fill}" stroke="{edge}" '
                    f'stroke-width="0.6"/>{F.centred(title, (x, TOP + dy + 1.5, SW, 10), F.S_TITLE, F.INK, True)}</g>')
        containers.append({"id": cid, "label": title, "role": "novel" if cid in NOVEL else "existing"})

    def span(x0, x1, label, icon=None, dy=0):
        y = 9.5 + dy
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
                f'{span(xs[0], xs[2] + SW, "fixed before inference", lock)}'
                f'{span(col[2], col[2] + SW - 16, "inference", dy=D)}{span(col[0], col[1] + SW, "automatic scoring", dy=D)}</g>')
    annotations.append({"id": "timeline", "kind": "label", "text": "fixed before inference / inference / "
                        "automatic scoring"})
    CY0 = (TOP + 12 + BOT) / 2         # vertical centre of the picture area, first row
    CY = CY0

    # 1 cohorts: two museum glyphs
    x = xs[0]
    body.append(f'<g id="n:museums" data-kind="node" data-role="input" data-parent="cohorts">'
                f'{museum(x + 22, CY - 4)}{museum(x + 53, CY - 4)}'
                f'{F.text(x + 22, CY + 13, "CMA", fill=F.MUTED, anchor="middle", extra=OUT)}'
                f'{F.text(x + 53, CY + 13, "AIC", fill=F.MUTED, anchor="middle", extra=OUT)}</g>')
    nodes.append({"id": "museums", "label": "CMA AIC", "kind": "icon", "parent": "cohorts"})

    # 2 crop + six masks
    x = xs[1]
    t, g0 = 12, 2
    grid_w = 3 * t + 2 * g0
    cs = 24
    x0 = x + (SW - cs - 4 - grid_w) / 2
    body.append(f'<g id="n:crop" data-kind="node" data-role="input" data-parent="crops">'
                f'{F.image(x0, CY - cs / 2, cs, cs, "f2_crop.png")}</g>')
    nodes.append({"id": "crop", "label": "", "kind": "image", "parent": "crops",
                  "image": {"src": "f2_crop.png", "role": "data-thumbnail"}})
    gx, gy = x0 + cs + 4, CY - (2 * t + g0) / 2
    tiles = "".join(F.image(gx + c * (t + g0), gy + r * (t + g0), t, t, f"f2_mask_{fam}_{area}.png")
                    for c, fam in enumerate(("crack", "flake", "loss")) for r, area in enumerate((1, 5)))
    body.append(f'<g id="n:masks" data-kind="node" data-role="input" data-parent="crops">{tiles}</g>')
    nodes.append({"id": "masks", "label": "", "kind": "image", "parent": "crops",
                  "image": {"src": "f2_mask_crack_5.png", "role": "data-thumbnail"}})

    # 3 aligned input (novel)
    x = xs[2]
    s3 = 52
    body.append(f'<g id="n:aligned" data-kind="node" data-role="novel" data-parent="input">'
                f'{F.image(x + (SW - s3) / 2, CY - s3 / 2 + 2, s3, s3, "f2_input.png")}</g>')
    nodes.append({"id": "aligned", "label": "", "kind": "image", "parent": "input",
                  "image": {"src": "f2_input.png", "role": "sample-input"}})
    body.append(f'<g id="a:mark-a" data-kind="annotation" data-anchor="input">{badge(x + SW - 7, BOT - 7, "a")}</g>')
    annotations.append({"id": "mark-a", "kind": "verdict", "text": "a", "anchor": "input"})

    # 4 models: pixel space (grey) and latent space (white) with the prefill control coloured
    x = xs[3]
    groups = [("pixel", PIXEL_TINT, PIXEL_EDGE, F.MODELS[:2], 33 + D), ("latent", "#FFFFFF", F.RULE, F.MODELS[2:], 66 + D)]
    for gid, tint, edge, models, y0 in groups:
        rows = "".join(f'{F.marker(shape, x + 11, y0 + 9 + 11 * i - 2.4, 2.1, col)}'
                       f'{F.text(x + 16, y0 + 9 + 11 * i, name, F.S_BODY, F.INK, True)}'
                       for i, (name, col, shape) in enumerate(models))
        body.append(f'<g id="n:{gid}" data-kind="node" data-role="module" data-parent="models">'
                    f'<rect x="{x + 5}" y="{y0}" width="{SW - 10}" height="26" rx="2" fill="{tint}" stroke="{edge}" '
                    f'stroke-width="0.5"/>{rows}</g>')
        nodes.append({"id": gid, "label": " ".join(m[0] for m in models), "kind": "module", "parent": "models"})
    sw = "".join(f'<rect x="{x + SW / 2 - 9.5 + 7 * i:.2f}" y="{96 + D}" width="5" height="5" fill="{c}" '
                 f'stroke="{F.BLUE}" stroke-width="0.6"/>' for i, c in enumerate(("#000000", "#808080", F.ring_colour())))
    body.append(f'<g id="n:prefill" data-kind="node" data-role="novel" data-parent="models">{sw}</g>')
    nodes.append({"id": "prefill", "label": "", "kind": "icon", "parent": "models"})
    body.append(f'<g id="a:mark-b" data-kind="annotation" data-anchor="models">{badge(x + SW - 7, BOT + D - 7, "b")}</g>')
    annotations.append({"id": "mark-b", "kind": "verdict", "text": "b", "anchor": "models"})

    # 5 composite
    x = xs[4]
    body.append(f'<g id="n:output" data-kind="node" data-role="output" data-parent="composite">'
                f'{F.image(x + (SW - s3) / 2, CY + D - s3 / 2 + 2, s3, s3, "f2_output.png")}</g>')
    nodes.append({"id": "output", "label": "", "kind": "image", "parent": "composite",
                  "image": {"src": "f2_output.png", "role": "sample-output"}})

    # 6 score: metric chips and the coverage ledger (novel, coloured)
    x = xs[5]
    for i, (mid, m, sub) in enumerate((("mae", "MAE", ""), ("de", "\u0394E", "00"), ("lpips", "LPIPS", ""),
                                       ("dists", "DISTS", ""))):
        cxp, cyp = x + 6 + (i % 2) * 33, 33 + D + (i // 2) * 13
        p = F.place(m + sub, (cxp, cyp, 30, 10.5), size=F.S_BODY, font=F.FONT, bold=True)
        lab = F.esc(m) + (f'<tspan font-size="5" dy="1.4">{sub}</tspan>' if sub else "")
        body.append(f'<g id="n:metric-{mid}" data-kind="node" data-role="module" data-parent="score">'
                    f'<rect x="{cxp}" y="{cyp}" width="30" height="10.5" rx="2" fill="#FFFFFF" stroke="{F.RULE}" '
                    f'stroke-width="0.5"/><text x="{cxp + 15:.2f}" y="{p["y"]:.2f}" font-size="{F.S_BODY}" '
                    f'font-weight="bold" fill="{F.INK}" text-anchor="middle">{lab}</text></g>')
        nodes.append({"id": f"metric-{mid}", "label": m + sub, "kind": "module", "parent": "score"})
    lx0, ly0, c, g = x + 6, 62 + D, 3.8, 0.9
    cells = "".join(f'<rect x="{lx0 + 3 + (i % 12) * (c + g):.2f}" y="{ly0 + 3 + (i // 12) * (c + g):.2f}" '
                    f'width="{c}" height="{c}" fill="{F.RED if i >= 31 else "#D0D4DA"}"/>' for i in range(36))
    body.append(f'<g id="n:ledger" data-kind="node" data-role="novel" data-parent="score">'
                f'<rect x="{lx0}" y="{ly0}" width="{SW - 12}" height="{3 * (c + g) - g + 6:.2f}" rx="2" '
                f'fill="{F.BLUE_TINT}" stroke="{F.BLUE}" stroke-width="0.5"/>{cells}</g>')
    nodes.append({"id": "ledger", "label": "", "kind": "icon", "parent": "score"})
    body.append(f'<g id="a:mark-c" data-kind="annotation" data-anchor="score">{badge(x + SW - 7, BOT + D - 7, "c")}</g>')
    annotations.append({"id": "mark-c", "kind": "verdict", "text": "c", "anchor": "score"})

    for i in range(5):
        a, b = stages[i][0], stages[i + 1][0]
        if i < 2:          # first row, left to right
            d = f"M{xs[i] + SW + 0.6:.2f} {CY0:.2f} H{xs[i + 1] - 1.4:.2f}"
        elif i == 2:       # turn down into the second row
            cx = xs[2] + SW - 9
            d = f"M{cx:.2f} {BOT + 0.6:.2f} V{TOP + D - 1.4:.2f}"
        else:              # second row, right to left
            d = f"M{xs[i] - 0.6:.2f} {CY0 + D:.2f} H{xs[i + 1] + SW + 1.4:.2f}"
        body.append(f'<g id="e:{a}-{b}" data-kind="edge" data-from="{a}" data-to="{b}" data-edge-kind="data">'
                    f'<path d="{d}" fill="none" stroke="{F.MUTED}" stroke-width="0.7" marker-end="url(#arrow)"/></g>')
        edges.append({"id": f"{a}-{b}", "from": a, "to": b, "kind": "data"})

    defs = (f'<defs><marker id="arrow" viewBox="0 0 6 6" refX="5" refY="3" markerWidth="5" markerHeight="5" '
            f'orient="auto-start-reverse" markerUnits="userSpaceOnUse"><path d="M0 0.6 L5.4 3 L0 5.4 Z" '
            f'fill="{F.MUTED}"/></marker></defs>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}pt" height="{H}pt" '
           f'font-family="{F.STACK}" font-size="{F.S_BODY}" data-spec="fig2-pipeline" data-spec-version="3">'
           f'{defs}<rect x="0" y="0" width="{W}" height="{H}" fill="#FFFFFF"/>{"".join(body)}</svg>')
    spec = {"meta": {"id": "fig2-pipeline", "title": "Evaluation pipeline", "family": "ai", "venue": "cvpr",
                     "kind": "architecture", "figure_kind": "whole-system", "column": "single", "width_pt": W,
                     "max_height_pt": H, "template": "ai", "direction": "mixed", "palette": "office-pastel",
                     "font": F.FONT, "step_markers": "none", "language": "en", "version": 3,
                     "caption_draft": "Evaluation pipeline. Crops from two open-access collections (60 works each, "
                     "15 works per medium) receive six procedural losses per artwork. The four models share the same "
                     "aperture, expanded to whole 8x8 cells (a); the SDXL sensitivity varies prefill (b); generated pixels "
                     "are kept only in the original hole and scored against the recorded crop, and planned, scored "
                     "and withheld conditions are counted against 360 planned per model per museum (c). "
                     "Coloured parts are the protocol controls.",
                     "ai": {"kinds": ["stage-pipeline"], "variant": "stage-chain", "subfield": "vision",
                            "arrangement": "bands", "grouping": ["framed-boxes"],
                            "samples": "image", "materials": ["the Figure 1(a) crop, its masks and a LaMa composite"]}},
            "containers": containers, "nodes": nodes, "edges": edges, "annotations": annotations,
            "legend": {"mode": "none"},
            "notes": "Pictures and short names only; ai.bare is deliberate (the figure shows what is new)."}
    return svg, spec


if __name__ == "__main__":
    svg, spec = build()
    (HERE / "fig.svg").write_text(svg)
    (HERE / "spec.json").write_text(json.dumps(spec, indent=1, ensure_ascii=False))
    print("wrote", HERE / "fig.svg")
