#!/usr/bin/env python3
"""
Generate a multi-panel figure containing the top 4 candidates for the manuscript.
"""

from pathlib import Path
from PIL import Image

ROOT = Path("~/Desktop/astro1").expanduser()
OVERLAY_DIR = ROOT / "results" / "raw_object_scan" / "overlays"
FIGURE_DIR = ROOT / "paper" / "figures"

FIGURE_DIR.mkdir(parents=True, exist_ok=True)

# Select the top 4 overlays (we'll just take the first 4 we find or specific ones if known)
# From the summary, top 4 are:
# 12376400000000006791, 12376400000000001618, 12376400000000000518, 12376400000000000578
target_objids = [
    "12376400000000006791",
    "12376400000000001618",
    "12376400000000000518",
    "12376400000000000578"
]

images = []
for objid in target_objids:
    path = OVERLAY_DIR / f"{objid}_overlay.png"
    if path.exists():
        images.append(Image.open(path))

if len(images) != 4:
    print(f"Expected 4 images, found {len(images)}. Using available pngs.")
    images = []
    for path in list(OVERLAY_DIR.glob("*.png"))[:4]:
        images.append(Image.open(path))

if not images:
    print("No overlays found!")
    exit(1)

# Assume all are 256x256
w, h = images[0].size
grid_w = w * 2
grid_h = h * 2

grid = Image.new('RGB', (grid_w, grid_h))
grid.paste(images[0], (0, 0))
if len(images) > 1:
    grid.paste(images[1], (w, 0))
if len(images) > 2:
    grid.paste(images[2], (0, h))
if len(images) > 3:
    grid.paste(images[3], (w, h))

out_path = FIGURE_DIR / "candidate_grid.png"
grid.save(out_path)
print(f"Saved figure grid to {out_path}")
