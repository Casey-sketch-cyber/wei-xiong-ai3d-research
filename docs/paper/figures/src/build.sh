#!/usr/bin/env bash
# Build Figures 1 and 2 (FigGenie SVG -> checked -> PDF + editable PowerPoint) from the repository root.
#
#   FIGGENIE=/path/to/FigGenie-paper-diagram-skill/skills/figgenie-paper-diagram \
#   FIGURE_ARCHIVE=/path/to/project-data-disk \
#   bash docs/paper/figures/src/build.sh
#
# Without CROP / SDXL_* / COMPOSITE the bitmaps are neutral placeholders (fine for layout review only).
# Requirements: python3 with lxml, Pillow, playwright (Chromium), python-pptx; FigGenie cloned from
# https://github.com/Sleepy-Avacado/FigGenie-paper-diagram-skill (MIT).
set -euo pipefail
: "${FIGGENIE:?set FIGGENIE to the figgenie-paper-diagram skill folder}"
ROOT=$(git rev-parse --show-toplevel)
SRC="$ROOT/docs/paper/figures/src"
args=(--out "$SRC/fig1" --out-fig2 "$SRC/fig2" --slot "${CASE_SLOT:-2}")
if [[ -n "${FIGURE_ARCHIVE:-}" ]]; then
  args+=(--archive "$FIGURE_ARCHIVE")
else
  [[ -n "${CROP:-}" ]] && args+=(--crop "$CROP")
  [[ -n "${SDXL_BLACK:-}" ]] && args+=(--sdxl-black "$SDXL_BLACK")
  [[ -n "${SDXL_GRAY:-}" ]] && args+=(--sdxl-gray "$SDXL_GRAY")
  [[ -n "${SDXL_RING:-}" ]] && args+=(--sdxl-ring "$SDXL_RING")
  [[ -n "${COMPOSITE:-}" ]] && args+=(--composite "$COMPOSITE")
fi
(cd "$ROOT/experiments" && python3 make_teaser_assets.py "${args[@]}")

for fig in fig1 fig2; do
  cd "$SRC/$fig"
  python3 "make_${fig}.py"
  python3 "$FIGGENIE/scripts/spec_validate.py" spec.json
  python3 "$FIGGENIE/scripts/check.py" fig.svg --spec spec.json        # lint must report 0 errors
  python3 "$FIGGENIE/scripts/embed_fonts.py" fig.svg -o fig.final.svg
  python3 "$FIGGENIE/scripts/export_pdf.py" fig.final.svg -o fig.pdf
  python3 "$FIGGENIE/scripts/svg2pptx.py" fig.final.svg --spec spec.json --force
  python3 "$FIGGENIE/scripts/pptx_check.py" fig.final.pptx --svg fig.final.svg
  python3 "$SRC/pptx_noshadow.py" fig.final.pptx
  python3 "$FIGGENIE/scripts/pptx_check.py" fig.final.pptx --svg fig.final.svg
done

cp "$SRC/fig1/fig.final.pptx" "$ROOT/docs/paper/figures/figure-1-teaser.pptx"
cp "$SRC/fig2/fig.final.pptx" "$ROOT/docs/paper/figures/figure-2-pipeline.pptx"
cp "$SRC/fig1/fig.png" "$ROOT/docs/paper/figures/previews/figure-1-teaser.png"
cp "$SRC/fig2/fig.png" "$ROOT/docs/paper/figures/previews/figure-2-pipeline.png"
echo "PDF for the paper: $SRC/fig1/fig.pdf and $SRC/fig2/fig.pdf (keep on the server; not in Git)"
