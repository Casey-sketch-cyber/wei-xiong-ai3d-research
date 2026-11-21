"""Build the editable PowerPoint layout drafts for the teaser and pipeline."""

import argparse
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Cm, Pt


INK = "383848"
FRAME = "8898B8"
WHITE = "FFFFFF"
DATA, DATA_INK = "F8F8C8", "8A7A3A"
PIXEL, PIXEL_INK = "E8E8D8", "6B6B58"
LATENT, BLUE = "D8E8F8", "3888D8"
PROBLEM, BRICK = "F8D8D8", "B84848"
CORRECTED, GREEN = "E2F0D9", "3A6B48"
SCORED = "DCDFE4"
MODELS = (
    ("LaMa", "2F6FB5", MSO_SHAPE.OVAL),
    ("MAT", "7FB2E0", MSO_SHAPE.RECTANGLE),
    ("PowerPaint v1", "D9952B", MSO_SHAPE.ISOSCELES_TRIANGLE),
    ("SDXL", "8A6FAE", MSO_SHAPE.DIAMOND),
)
SCORED_CONDITIONS = (("CMA", 281), ("AIC", 350))
PLANNED = 360


def rgb(color):
    return RGBColor.from_string(color)


def group(shapes, name):
    item = shapes.add_group_shape()
    item.name = name
    return item.shapes


def clear_theme_effects(item):
    element = item._element
    style = element.find(qn("p:style"))
    if style is not None:
        element.remove(style)
    element.spPr.append(OxmlElement("a:effectLst"))


def box(shapes, name, x, y, w, h, fill=None, stroke=None, *, rounded=False, kind=None):
    shape_type = kind or (MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE)
    item = shapes.add_shape(shape_type, Cm(x), Cm(y), Cm(w), Cm(h))
    item.name = name
    if rounded:
        item.adjustments[0] = min(0.16, 0.12 / min(w, h))
    if fill is None:
        item.fill.background()
    else:
        item.fill.solid()
        item.fill.fore_color.rgb = rgb(fill)
    if stroke is None:
        item.line.fill.background()
    else:
        item.line.color.rgb = rgb(stroke)
        item.line.width = Pt(0.75)
    clear_theme_effects(item)
    return item


def text(shapes, name, value, x, y, w, h, *, size=7.5, bold=False, color=INK, left=False):
    item = shapes.add_textbox(Cm(x), Cm(y), Cm(w), Cm(h))
    item.name = name
    frame = item.text_frame
    frame.clear()
    frame.word_wrap = False
    frame.auto_size = MSO_AUTO_SIZE.NONE
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    for index, line in enumerate(value.split("\n")):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.alignment = PP_ALIGN.LEFT if left else PP_ALIGN.CENTER
        paragraph.space_before = paragraph.space_after = Pt(0)
        paragraph.line_spacing = Pt(size * 1.14)
        run = paragraph.add_run()
        run.text = line
        run.font.name = "Arial"
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = rgb(color)
    clear_theme_effects(item)
    return item


def line(shapes, name, x1, y1, x2, y2, *, color=FRAME, width=0.75, arrow=False, dashed=False):
    edge = shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Cm(x1), Cm(y1), Cm(x2), Cm(y2))
    edge.name = name
    edge.line.color.rgb = rgb(color)
    edge.line.width = Pt(width)
    if dashed:
        edge.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    if arrow:
        tail = OxmlElement("a:tailEnd")
        tail.set("type", "triangle")
        tail.set("len", "sm")
        tail.set("w", "sm")
        edge._element.spPr.get_or_add_ln().append(tail)
    clear_theme_effects(edge)


def crop_placeholder(shapes, name, x, y, side, *, fill=DATA, stroke=DATA_INK):
    image = group(shapes, name)
    box(image, name + "-frame", x, y, side, side, fill, stroke)
    inset = 0.09
    line(image, name + "-guide-1", x + inset, y + inset, x + side - inset, y + side - inset, width=0.5)
    line(image, name + "-guide-2", x + inset, y + side - inset, x + side - inset, y + inset, width=0.5)
    return image


def badge(shapes, name, x, y, letter):
    box(shapes, name + "-dot", x, y, 0.35, 0.35, BRICK, kind=MSO_SHAPE.OVAL)
    text(shapes, name + "-letter", letter, x, y, 0.35, 0.35, size=7, bold=True, color=WHITE)


def begin(height, title):
    doc = Presentation()
    doc.slide_width = Cm(17.4)
    doc.slide_height = Cm(height)
    doc.core_properties.title = title
    page = doc.slides.add_slide(doc.slide_layouts[6])
    page.background.fill.solid()
    page.background.fill.fore_color.rgb = rgb(WHITE)
    return doc, page


def teaser_panel(slide, x, w, key, title):
    shapes = group(slide.shapes, f"{key}-panel")
    box(shapes, f"{key}-border", x, 0.22, w, 5.12, WHITE, FRAME, rounded=True)
    text(shapes, f"{key}-title", title, x + 0.10, 0.39, w - 0.20, 0.40, size=9, bold=True)
    text(shapes, f"{key}-panel-label", f"({key})", x, 4.89, w, 0.36, size=10, bold=True)
    return shapes


def crack_mock(shapes, name, x, y, side, variant):
    display = group(shapes, name)
    background = {"original": DATA, "sampled": LATENT, "aligned": CORRECTED}[variant]
    box(display, name + "-frame", x, y, side, side, background, FRAME)
    if variant != "original":
        for index in range(1, 5):
            step = side * index / 5
            line(display, f"{name}-grid-x{index}", x + step, y, x + step, y + side, color=WHITE, width=0.5)
            line(display, f"{name}-grid-y{index}", x, y + step, x + side, y + step, color=WHITE, width=0.5)
    points = ((0.17, 0.24), (0.40, 0.36), (0.31, 0.53), (0.67, 0.56), (0.51, 0.72), (0.79, 0.82))
    tones = {
        "original": (WHITE,) * 5,
        "sampled": (GREEN, BRICK, GREEN, BRICK, BRICK),
        "aligned": (GREEN,) * 5,
    }
    for index, ((sx, sy), (tx, ty)) in enumerate(zip(points[:-1], points[1:], strict=True)):
        line(
            display, f"{name}-schematic-segment-{index + 1}", x + sx * side, y + sy * side,
            x + tx * side, y + ty * side, color=tones[variant][index], width=1.8,
            dashed=variant == "sampled" and tones[variant][index] == BRICK,
        )


def teaser_mask(slide, x, w):
    shapes = teaser_panel(slide, x, w, "a", "What the model is asked to fill")
    text(shapes, "a-scope", "1% crack masks", x, 0.86, w, 0.34)
    side = 1.50
    starts = (x + 0.19, x + (w - side) / 2, x + w - 0.19 - side)
    for left, key, caption in zip(starts, ("original", "sampled", "aligned"), ("Original", "Sampled", "Aligned"),
                                  strict=True):
        crack_mock(shapes, f"a-mask-{key}", left, 1.86, side, key)
        text(shapes, f"a-{key}-caption", caption, left, 3.37, side, 0.34, size=7)
    start, end = starts[0] + side, starts[1]
    line(shapes, "a-original-to-sampled", start + 0.025, 2.61, end - 0.025, 2.61, width=1, arrow=True)
    mid = (start + end) / 2
    text(shapes, "a-sampling-label", "8× downsample", mid - 0.92, 1.52, 1.84, 0.34, size=7)
    left_center, right_center = starts[0] + side / 2, starts[2] + side / 2
    path = group(shapes, "a-original-to-aligned")
    line(path, "a-alignment-rise", left_center, 1.83, left_center, 1.48, width=1)
    line(path, "a-alignment-cross", left_center, 1.48, right_center, 1.48, width=1)
    line(path, "a-alignment-fall", right_center, 1.48, right_center, 1.82, width=1, arrow=True)
    text(path, "a-alignment-label", "Expand original", x, 1.14, w, 0.32, size=7)
    text(shapes, "a-missed-crack-pixels", "59.5% of crack pixels missed", x, 3.73, w, 0.39, size=10,
         bold=True, color=BRICK)
    text(shapes, "a-missed-cohort", "60 Cleveland works", x, 4.12, w, 0.32, size=7)
    text(shapes, "a-powerpaint-mae-change", "PowerPaint MAE −45% (40 paired works)", x, 4.45, w, 0.36,
         size=7.4, color=GREEN)


def teaser_prefill(slide, x, w):
    shapes = teaser_panel(slide, x, w, "b", "What fills the hole first")
    text(shapes, "b-input-heading", "Hole prefill", x + 0.16, 0.99, 1.56, 0.34, size=7.4)
    text(shapes, "b-output-heading", "Mean Δluma", x + 3.37, 0.99, 1.90, 0.34, size=7.2)
    model = group(shapes, "b-sdxl-model")
    box(model, "b-model-frame", x + 1.89, 1.43, 1.42, 3.02, LATENT, FRAME, rounded=True)
    box(model, "b-diffusion-icon-placeholder", x + 2.33, 2.18, 0.54, 0.54, WHITE, BLUE, rounded=True)
    for index, size in enumerate((0.10, 0.16, 0.21)):
        box(model, f"b-diffusion-placeholder-dot-{index + 1}", x + 2.39 + index * 0.10, 2.39 - size / 2,
            size, size, BLUE, kind=MSO_SHAPE.OVAL)
    text(model, "b-model-name", "SDXL", x + 1.89, 2.84, 1.42, 0.39, size=8.5, bold=True)
    text(model, "b-model-strength", "strength\n0.99", x + 1.89, 3.22, 1.42, 0.69, size=7.4)
    tone_rows = (
        ("black", "Black", "202020", "−0.085"),
        ("gray", "Mid-gray", "808080", "+0.055"),
        ("ring", "Ring mean", "C5AC83", "+0.034"),
    )
    for index, (key, name, fill, value) in enumerate(tone_rows):
        row = group(shapes, f"b-prefill-{key}")
        y = 1.45 + index * 1.05
        stroke = BRICK if index == 0 else FRAME
        box(row, f"b-{key}-swatch", x + 0.68, y + 0.08, 0.54, 0.54, fill, stroke)
        text(row, f"b-{key}-label", name, x + 0.18, y + 0.64, 1.55, 0.32, size=7.3)
        line(row, f"b-{key}-input-arrow", x + 1.33, y + 0.35, x + 1.88, y + 0.35, width=1, arrow=True)
        line(row, f"b-{key}-output-arrow", x + 3.32, y + 0.35, x + 3.91, y + 0.35, width=1, arrow=True)
        crop_placeholder(row, f"b-output-{key}", x + 3.98, y, 0.70, fill=PROBLEM if index == 0 else DATA,
                         stroke=stroke)
        text(row, f"b-{key}-mean-luminance-shift", value, x + 3.45, y + 0.71, 1.76, 0.33, size=8.5,
             color=BRICK if index == 0 else INK, bold=index == 0)
    text(shapes, "b-aggregate-scope", "16 works × 6 conditions", x, 4.63, w, 0.30, size=7)


def waffle(shapes, key, x, y, scored):
    cells = group(shapes, f"c-waffle-{key}")
    step = 0.108
    for index in range(PLANNED):
        row, column = divmod(index, 20)
        is_scored = index < scored
        state = "scored" if is_scored else "withheld"
        box(cells, f"c-{key}-{state}-{index + 1:03d}", x + column * step, y + row * step, 0.092, 0.092,
            SCORED if is_scored else BRICK)


def teaser_coverage(slide, x, w):
    shapes = teaser_panel(slide, x, w, "c", "Which outputs get scored")
    text(shapes, "c-powerpaint-model", "PowerPaint v1", x, 0.86, w, 0.34)
    for index, (museum, scored) in enumerate(SCORED_CONDITIONS):
        key = museum.lower()
        left = x + 0.31 + index * 2.66
        box(shapes, f"c-checker-{key}-icon-placeholder", left + 0.86, 1.23, 0.41, 0.41, LATENT, FRAME,
            kind=MSO_SHAPE.PENTAGON)
        text(shapes, f"c-checker-{key}-label", "Safety checker", left - 0.12, 1.66, 2.38, 0.32, size=7.1)
        waffle(shapes, key, left, 2.06, scored)
        text(shapes, f"c-{key}-availability", f"{museum} {scored / PLANNED:.0%}", left - 0.11, 4.03, 2.38, 0.35,
             size=9.2, bold=True, color=BLUE)
        text(shapes, f"c-{key}-fraction", f"{scored}/{PLANNED} scored", left - 0.11, 4.39, 2.38, 0.32, size=7.1)
    legend = group(shapes, "c-waffle-legend")
    box(legend, "c-legend-scored-swatch", x + 1.12, 4.77, 0.16, 0.16, SCORED)
    text(legend, "c-legend-scored-text", "Scored", x + 1.34, 4.69, 1.10, 0.32, size=7, left=True)
    box(legend, "c-legend-withheld-swatch", x + 3.0, 4.77, 0.16, 0.16, BRICK)
    text(legend, "c-legend-withheld-text", "Withheld", x + 3.22, 4.69, 1.14, 0.32, size=7, left=True)


def model_label(shapes, name, model, x, y, w, h):
    label, color, shape = model
    box(shapes, name + "-marker", x + 0.13, y + (h - 0.13) / 2, 0.13, 0.13, color, kind=shape)
    text(shapes, name + "-name", label, x + 0.32, y, w - 0.35, h, size=7.2, bold=True, left=True)


def teaser_footer(slide):
    shapes = group(slide.shapes, "d-controlled-protocol")
    box(shapes, "d-frame", 0.22, 5.59, 16.96, 1.35, CORRECTED, GREEN, rounded=True)
    text(shapes, "d-title", "Under the controlled protocol", 0.46, 5.69, 6.35, 0.31, size=8, bold=True, left=True)
    text(shapes, "d-mae-scope", "Masked MAE, shared aperture", 9.48, 5.69, 7.08, 0.31, size=7.2, color=GREEN)
    starts, widths = (0.49, 2.40, 4.13, 6.96), (1.43, 1.23, 2.36, 1.44)
    for index, (model, x, w) in enumerate(zip(MODELS, starts, widths, strict=True)):
        name = f"d-model-{index + 1}"
        box(shapes, name + "-block", x, 6.08, w, 0.46, WHITE, FRAME, rounded=True)
        model_label(shapes, name, model, x, 6.08, w, 0.46)
        if index < len(MODELS) - 1:
            right = x + w
            text(shapes, f"d-rank-{index + 1}", "≈" if index == 0 else "<", right, 6.08,
                 starts[index + 1] - right, 0.46, size=10, bold=True)
    for left, key, caption in (
        (9.65, "museum", "2 museums"), (11.92, "media", "4 media"), (14.08, "loss", "6 loss conditions"),
    ):
        box(shapes, f"d-{key}-icon-placeholder", left, 6.13, 0.32, 0.32, WHITE, GREEN, rounded=True)
        text(shapes, f"d-{key}-scope", caption, left + 0.43, 6.1, 2.64, 0.39, size=7.7, left=True)
    text(shapes, "d-panel-label", "(d)", 8.18, 6.56, 1.04, 0.36, size=10, bold=True)


def teaser():
    doc, slide = begin(7.15, "Figure 1. Teaser")
    w = (17.4 - 0.44 - 0.60) / 3
    for index, draw in enumerate((teaser_mask, teaser_prefill, teaser_coverage)):
        draw(slide, 0.22 + index * (w + 0.30), w)
    teaser_footer(slide)
    slide.notes_slide.notes_text_frame.text = (
        "Mask coverage is the mean for the 60 Cleveland 1% crack conditions in the 60-work alignment replication. "
        "The PowerPaint relative MAE reduction rounds to 45%. The 40 complete same-work pairs changed from "
        "0.1055 to 0.0583 with the checker enabled in both arms. Source: docs/NATIVE_APERTURE.md.\n"
        "Rec.709 sRGB luminance shifts are output minus reference and rounded to three decimals. The values "
        "−0.0847, +0.0553, and +0.0339 are aggregates for 16 works with six conditions per prefill color, "
        "with SDXL strength fixed at 0.99. Source: docs/SDXL_PREFILL.md.\n"
        "PowerPaint safety-on scored fractions: 281/360 in Cleveland, 350/360 in Chicago. "
        "Sources: docs/NATIVE_MAIN.md and docs/AIC_REPLICATION.md. The ranking summarizes masked MAE "
        "under the shared expanded aperture."
    )
    return doc


def module(slide, key, title, x, w, fill=WHITE, letter=None):
    shapes = group(slide.shapes, f"pipeline-{key}")
    box(shapes, f"{key}-module-frame", x, 1.24, w, 4.38, fill, FRAME, rounded=True)
    text(shapes, f"{key}-heading", title, x + 0.08, 1.37, w - 0.16, 0.80, size=9, bold=True)
    if letter:
        badge(shapes, f"{key}-protocol-{letter}", x + w - 0.47, 1.11, letter)
    return shapes


def pipeline_cohorts(slide, x, w):
    shapes = module(slide, "cohorts", "Open-access\ncohorts", x, w, DATA)
    for index, museum in enumerate(("cma", "aic")):
        start = x + 0.38 + index * 0.97
        box(shapes, f"cohorts-{museum}-icon-placeholder", start, 2.50, 0.80, 0.80, WHITE, DATA_INK, rounded=True)
        text(shapes, f"cohorts-{museum}-initials", museum.upper(), start, 2.50, 0.80, 0.80, size=7, bold=True)
    text(shapes, "cohorts-sample-size", "CMA 60 + AIC 60", x, 3.64, w, 0.35, size=7.5, bold=True)
    text(shapes, "cohorts-strata", "4 media × 15\nper museum", x, 4.14, w, 0.76, size=7.4)


def pipeline_masks(slide, x, w):
    shapes = module(slide, "crops", "512 crop +\n6 masks", x, w, DATA)
    crop_placeholder(shapes, "crops-source", x + 0.23, 2.46, 0.99, fill=WHITE)
    grid = group(shapes, "crops-mask-grid")
    for row, area in enumerate(("1pct", "5pct")):
        for col, family in enumerate(("crack", "flake", "loss")):
            left = x + 1.38 + col * 0.30
            top = 2.58 + row * 0.35
            name = f"crops-mask-{family}-{area}"
            box(grid, name + "-thumbnail", left, top, 0.24, 0.24, WHITE, DATA_INK)
            box(grid, name + "-hole", left + 0.055, top + 0.055, 0.13, 0.13, DATA_INK,
                kind=(MSO_SHAPE.DIAMOND, MSO_SHAPE.RECTANGLE, MSO_SHAPE.OVAL)[col])
    text(shapes, "crops-mask-families", "Cracks, flakes,\nand broad loss", x, 3.61, w, 0.73, size=7.4)
    text(shapes, "crops-mask-areas", "1% and 5% area", x, 4.62, w, 0.35, size=7.3, bold=True)


def pipeline_aperture(slide, x, w):
    shapes = module(slide, "aperture", "Shared input", x, w, LATENT, letter="a")
    left = x + (w - 1.42) / 2
    crack_mock(shapes, "aperture-expanded-mask-placeholder", left, 2.44, 1.42, "aligned")
    text(shapes, "aperture-expansion", "8 × 8-aligned\naperture", x, 4.12, w, 0.75, size=7.5)


def pipeline_models(slide, x, w):
    shapes = module(slide, "models", "Four pinned\nmodels", x, w, letter="b")
    box(shapes, "models-pixel-block", x + 0.14, 2.37, w - 0.28, 0.53, PIXEL, PIXEL_INK, rounded=True)
    model_label(shapes, "models-lama", MODELS[0], x + 0.15, 2.37, 1.23, 0.53)
    model_label(shapes, "models-mat", MODELS[1], x + 1.32, 2.37, 1.06, 0.53)
    box(shapes, "models-latent-block", x + 0.14, 3.01, w - 0.28, 0.83, LATENT, FRAME, rounded=True)
    model_label(shapes, "models-powerpaint", MODELS[2], x + 0.15, 3.07, w - 0.28, 0.33)
    model_label(shapes, "models-sdxl", MODELS[3], x + 0.15, 3.43, w - 0.28, 0.33)
    box(shapes, "models-gpu-icon-placeholder", x + (w - 0.42) / 2, 4.08, 0.42, 0.42, WHITE, FRAME, rounded=True)
    text(shapes, "models-gpu-device", "RTX 3090", x, 4.58, w, 0.32, size=7.4, bold=True)
    text(shapes, "models-inference-seed", "Seed 2026", x, 4.94, w, 0.32, size=7.4)


def pipeline_composite(slide, x, w):
    shapes = module(slide, "composite", "Composite in\noriginal hole", x, w, CORRECTED)
    left = x + (w - 1.45) / 2
    crop = crop_placeholder(shapes, "composite-output-placeholder", left, 2.45, 1.45, fill=WHITE, stroke=GREEN)
    hole = box(crop, "composite-original-hole", left + 0.35, 2.82, 0.73, 0.64, CORRECTED, GREEN,
               kind=MSO_SHAPE.OVAL)
    hole.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    text(shapes, "composite-original-outside", "Original pixels\noutside the hole", x, 4.15, w, 0.77, size=7.4)


def pipeline_ledger(slide, x, w):
    shapes = module(slide, "ledger", "Score + ledger", x, w, CORRECTED, letter="c")
    metrics = group(shapes, "ledger-metrics")
    for index, name in enumerate(("MAE", "ΔE₀₀", "LPIPS", "DISTS")):
        row, col = divmod(index, 2)
        left, top = x + 0.19 + col * 1.08, 2.23 + row * 0.42
        box(metrics, f"ledger-metric-{index + 1}-background", left, top, 1.00, 0.34, WHITE, GREEN, rounded=True)
        text(metrics, f"ledger-metric-{index + 1}-name", name, left, top, 1.00, 0.34, size=7.1, bold=True)
    text(shapes, "ledger-color-summaries", "ΔE₀₀: two summaries", x, 3.16, w, 0.35, size=7)
    ledger = group(shapes, "ledger-denominator-rows")
    for index, (key, label, value) in enumerate(
        (("planned", "Planned", "360"), ("scored", "Scored", "✓"), ("withheld", "Withheld", "×")),
    ):
        y = 3.64 + index * 0.40
        box(ledger, f"ledger-{key}-frame", x + 0.17, y, w - 0.34, 0.40, PROBLEM if index == 2 else WHITE, FRAME)
        text(ledger, f"ledger-{key}-label", label, x + 0.28, y, 1.22, 0.40, size=7.2, left=True)
        text(ledger, f"ledger-{key}-value", value, x + 1.64, y, 0.62, 0.40, size=7.6, bold=True,
             color=BRICK if index == 2 else GREEN)
    text(shapes, "ledger-planned-scope", "Per model\nper museum", x, 4.96, w, 0.60, size=7)


def pipeline():
    doc, slide = begin(6.0, "Figure 2. Methods pipeline")
    timeline = group(slide.shapes, "pipeline-preregistration-timeline")
    box(timeline, "timeline-lock-shackle-placeholder", 0.39, 0.65, 0.25, 0.26, None, FRAME, rounded=True)
    box(timeline, "timeline-lock-body-placeholder", 0.35, 0.80, 0.33, 0.23, WHITE, FRAME, rounded=True)
    line(timeline, "timeline-preregistration-arrow", 0.72, 0.92, 17.13, 0.92, arrow=True)
    text(timeline, "timeline-protocol-caption", "Protocol committed before inference", 0.32, 0.24, 16.76, 0.38,
         size=9, bold=True)
    spacing = 0.33
    w = (17.4 - 0.46 - 5 * spacing) / 6
    modules = (pipeline_cohorts, pipeline_masks, pipeline_aperture, pipeline_models, pipeline_composite,
               pipeline_ledger)
    starts = [0.23 + index * (w + spacing) for index in range(len(modules))]
    for draw, x in zip(modules, starts, strict=True):
        draw(slide, x, w)
    for index, (current, following) in enumerate(zip(starts[:-1], starts[1:], strict=True)):
        line(slide.shapes, f"pipeline-arrow-{index + 1}", current + w + 0.035, 3.39, following - 0.035, 3.39,
             width=1, arrow=True)
    slide.notes_slide.notes_text_frame.text = (
        "The main protocol pairs 60 works at each museum with six damage conditions per work. "
        "Each model has 360 planned conditions per museum. ΔE₀₀ appears as the mean of per-pixel differences "
        "and as the difference of mean masked Lab colors. Sources: docs/NATIVE_MAIN.md and docs/AIC_REPLICATION.md."
    )
    return doc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory for the two editable drafts")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, draw in (("figure-1-teaser", teaser), ("figure-2-pipeline", pipeline)):
        path = args.output_dir / f"{name}.pptx"
        draw().save(path)
        print(path)


if __name__ == "__main__":
    main()
