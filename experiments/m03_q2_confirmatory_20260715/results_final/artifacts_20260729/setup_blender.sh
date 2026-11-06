#!/usr/bin/env bash
set -euo pipefail

ROOT=/root/autodl-tmp/m03_q2_confirmatory_20260715
TOOLS="$ROOT/tools"
VERSION=4.3.2
ARCHIVE="blender-${VERSION}-linux-x64.tar.xz"
URL="https://download.blender.org/release/Blender4.3/${ARCHIVE}"
TARGET="$TOOLS/blender-${VERSION}-linux-x64"

mkdir -p "$TOOLS"
if [[ ! -x "$TARGET/blender" ]]; then
  cd "$TOOLS"
  if [[ ! -s "$ARCHIVE" ]]; then
    curl --fail --location --retry 7 --retry-delay 5 --output "$ARCHIVE.part" "$URL"
    mv "$ARCHIVE.part" "$ARCHIVE"
  fi
  tar -xf "$ARCHIVE"
fi

BLENDER_PYTHON="$TARGET/4.3/python/bin/python3.11"
"$BLENDER_PYTHON" -m ensurepip --upgrade
"$BLENDER_PYTHON" -m pip install --upgrade \
  pillow==11.3.0 \
  opencv-python-headless==4.10.0.84 \
  scipy==1.14.1 \
  trimesh==4.4.7

"$TARGET/blender" --version
sha256sum "$TOOLS/$ARCHIVE" > "$ROOT/blender_archive_sha256.txt"
