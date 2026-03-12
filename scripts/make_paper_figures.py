#!/usr/bin/env python3
"""
Generate a multi-panel figure containing the top ranked overlay candidates.
"""

from pathlib import Path

import pandas as pd
from PIL import Image

from common import load_config, normalize_objid, setup_logger


PROJECT_ROOT, config = load_config()
logger = setup_logger(__file__, config, PROJECT_ROOT)

SCAN_CSV = PROJECT_ROOT / config["paths"]["results"] / "raw_object_scan" / "raw_object_scan.csv"
OVERLAY_DIR = PROJECT_ROOT / config["paths"]["results"] / "raw_object_scan" / "overlays"
FIGURE_DIR = PROJECT_ROOT / config["paths"]["results"] / "figures"
MANIFEST_PATH = FIGURE_DIR / "candidate_grid_manifest.csv"
OUT_PATH = FIGURE_DIR / "candidate_grid.png"

FIGURE_DIR.mkdir(parents=True, exist_ok=True)


def candidate_overlay_path(row: pd.Series) -> Path:
    overlay_path = row.get("overlay_path")
    if isinstance(overlay_path, str) and overlay_path:
        path = Path(overlay_path)
        if path.exists():
            return path
    return OVERLAY_DIR / f"{normalize_objid(row['objid'])}_overlay.png"


if not SCAN_CSV.exists():
    print(f"Scan results not found: {SCAN_CSV}")
    raise SystemExit(1)

df = pd.read_csv(SCAN_CSV, dtype={"objid": "string"})
df["objid"] = df["objid"].map(normalize_objid)
df["overlay_path"] = df.apply(candidate_overlay_path, axis=1).astype(str)

ranked = df[df["secondary_object_flag"] == True].copy()
ranked = ranked.sort_values(
    ["secondary_object_score", "brightest_secondary_flux_ratio", "secondary_components"],
    ascending=[False, False, False],
)
ranked = ranked[ranked["overlay_path"].map(lambda p: Path(p).exists())]

selected = ranked.head(4).copy()
if selected.empty:
    print("No ranked overlays found!")
    raise SystemExit(1)

images = [Image.open(Path(path)) for path in selected["overlay_path"]]

while len(images) < 4:
    images.append(images[-1].copy())

w, h = images[0].size
grid = Image.new("RGB", (w * 2, h * 2))
grid.paste(images[0], (0, 0))
grid.paste(images[1], (w, 0))
grid.paste(images[2], (0, h))
grid.paste(images[3], (w, h))
grid.save(OUT_PATH)

selected[
    [
        "objid",
        "ra",
        "dec",
        "secondary_components",
        "brightest_secondary_flux_ratio",
        "secondary_object_score",
        "overlay_path",
    ]
].to_csv(MANIFEST_PATH, index=False)

print(f"Saved figure grid to {OUT_PATH}")
print(f"Saved manifest to {MANIFEST_PATH}")
