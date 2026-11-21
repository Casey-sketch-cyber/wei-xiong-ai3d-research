#!/usr/bin/env python3
"""Remove theme shadows from a deck written by FigGenie's svg2pptx.

svg2pptx gives its shapes the default style, whose effectRef points at the theme's shadow, so PowerPoint draws a soft
drop shadow under every box. Paper figures must not have shadows (FIGURE_SPEC.md), so every effectRef in the slides
is pointed at index 0 (no effect).

    python3 pptx_noshadow.py fig.final.pptx
"""
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path


def strip(path: Path) -> int:
    count = 0
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / path.name
        with zipfile.ZipFile(path) as zin, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", item.filename):
                    text, n = re.subn(r'<a:effectRef idx="[1-9]"', '<a:effectRef idx="0"', data.decode("utf-8"))
                    data, count = text.encode("utf-8"), count + n
                zout.writestr(item, data)
        shutil.copyfile(out, path)
    return count


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print(arg, "effect references cleared:", strip(Path(arg)))
