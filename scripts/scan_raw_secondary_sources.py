#!/usr/bin/env python3
"""
Scan raw SDSS JPG cutouts for multiple luminous components.

This is an image-plane detector, not a catalog verifier. It answers:
1. Does the cutout contain one dominant source or multiple resolved components?
2. Which cutouts have the strongest evidence for secondary objects/companions?

Outputs:
- results/raw_object_scan/raw_object_scan.csv
- results/raw_object_scan/raw_object_scan_summary.md
- results/raw_object_scan/overlays/*.png
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
from scipy import ndimage
from sklearn.ensemble import IsolationForest


import logging
import yaml

# Load configuration and setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
with open(PROJECT_ROOT / "config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Setup logging
LOG_DIR = PROJECT_ROOT / config['paths']['logs']
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f"{Path(__file__).stem}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(Path(__file__).stem)

RAW_DIR = PROJECT_ROOT / config['paths']['raw_data']
META_PATH = PROJECT_ROOT / config['paths']['metadata'] / "galaxy_catalog.csv"
OUT_DIR = PROJECT_ROOT / config['paths']['results'] / "raw_object_scan"
OVERLAY_DIR = OUT_DIR / "overlays"

MIN_AREA = int(config['pipeline']['scanner']['min_component_area'])
PRIMARY_SEARCH_RADIUS = float(config['pipeline']['scanner']['search_radius'])
MIN_SEPARATION = float(config['pipeline']['scanner']['separation_min'])
MAX_SECONDARY_DISTANCE = float(config['pipeline']['scanner']['separation_max'])
SECONDARY_FLUX_RATIO = float(config['pipeline']['scanner']['min_flux_ratio'])
THRESHOLD_SIGMA = float(config['pipeline']['scanner']['sigma_threshold'])
MAX_OVERLAYS = 20
MAX_COLOR_DIFF = 0.2  # Photometric color consistency threshold


@dataclass
class Component:
    label: int
    area: int
    flux: float
    centroid_x: float
    centroid_y: float
    center_distance: float
    bbox: tuple[int, int, int, int]
    g_r: float = 0.0
    r_i: float = 0.0


def valid_raw_paths() -> Iterable[Path]:
    for path in sorted(RAW_DIR.glob("*.jpg")):
        if path.stat().st_size > 0:
            yield path


def load_gray(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        return np.asarray(im.convert("L"), dtype=np.float32)

def load_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB"), dtype=np.float32)


def robust_background(gray: np.ndarray) -> tuple[float, float]:
    border = np.concatenate(
        [
            gray[:20, :].ravel(),
            gray[-20:, :].ravel(),
            gray[:, :20].ravel(),
            gray[:, -20:].ravel(),
        ]
    )
    median = float(np.median(border))
    mad = float(np.median(np.abs(border - median)))
    sigma = 1.4826 * mad if mad > 0 else float(border.std() + 1e-6)
    return median, sigma


def extract_components(gray: np.ndarray, rgb: np.ndarray) -> list[Component]:
    bg, sigma = robust_background(gray)
    smooth = ndimage.gaussian_filter(gray, sigma=2.0)
    threshold = bg + THRESHOLD_SIGMA * sigma
    mask = smooth > threshold
    mask = ndimage.binary_opening(mask, structure=np.ones((5, 5)))
    mask = ndimage.binary_closing(mask, structure=np.ones((5, 5)))

    labels, count = ndimage.label(mask)
    if count == 0:
        return []

    h, w = gray.shape
    cx_img = (w - 1) / 2.0
    cy_img = (h - 1) / 2.0
    components: list[Component] = []

    for label in range(1, count + 1):
        ys, xs = np.where(labels == label)
        area = int(len(xs))
        if area < MIN_AREA:
            continue
        values = gray[ys, xs] - bg
        flux = float(np.clip(values, 0, None).sum())
        if flux <= 0:
            continue
        weights = np.clip(values, 0, None) + 1e-6
        centroid_x = float(np.average(xs, weights=weights))
        centroid_y = float(np.average(ys, weights=weights))
        center_distance = float(np.hypot(centroid_x - cx_img, centroid_y - cy_img))
        bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
        
        # Color proxies (SDSS mapping: B->g, G->r, R->i)
        g_flux = float(np.mean(rgb[ys, xs, 2]) + 1.0)
        r_flux = float(np.mean(rgb[ys, xs, 1]) + 1.0)
        i_flux = float(np.mean(rgb[ys, xs, 0]) + 1.0)
        
        g_r = float(-2.5 * np.log10(g_flux / r_flux))
        r_i = float(-2.5 * np.log10(r_flux / i_flux))

        components.append(
            Component(
                label=label,
                area=area,
                flux=flux,
                centroid_x=centroid_x,
                centroid_y=centroid_y,
                center_distance=center_distance,
                bbox=bbox,
                g_r=g_r,
                r_i=r_i,
            )
        )

    return components


def choose_primary(components: list[Component]) -> Component | None:
    if not components:
        return None

    central = [c for c in components if c.center_distance <= PRIMARY_SEARCH_RADIUS]
    if central:
        return max(central, key=lambda c: (c.flux, -c.center_distance))
    return max(components, key=lambda c: c.flux)


def asymmetry_score(gray: np.ndarray) -> float:
    rotated = np.rot90(gray, 2)
    numerator = np.abs(gray - rotated).sum()
    denominator = np.abs(gray).sum() + 1e-6
    return float(numerator / denominator)


def secondary_components(primary: Component | None, components: list[Component]) -> list[Component]:
    if primary is None:
        return []
    out = []
    for comp in components:
        if comp.label == primary.label:
            continue
        separation = float(np.hypot(comp.centroid_x - primary.centroid_x, comp.centroid_y - primary.centroid_y))
        flux_ratio = comp.flux / (primary.flux + 1e-6)
        
        # Color consistency filter
        color_diff_g_r = abs(primary.g_r - comp.g_r)
        color_diff_r_i = abs(primary.r_i - comp.r_i)

        if (
            separation >= MIN_SEPARATION
            and separation <= MAX_SECONDARY_DISTANCE
            and comp.center_distance <= MAX_SECONDARY_DISTANCE
            and comp.area >= MIN_AREA
            and flux_ratio >= SECONDARY_FLUX_RATIO
            and color_diff_g_r < MAX_COLOR_DIFF
            and color_diff_r_i < MAX_COLOR_DIFF
        ):
            out.append(comp)
    return sorted(out, key=lambda c: c.flux, reverse=True)


def overlay_components(path: Path, primary: Component | None, secondaries: list[Component], out_path: Path) -> None:
    with Image.open(path) as im:
        overlay = im.convert("RGB")
    draw = ImageDraw.Draw(overlay)

    if primary is not None:
        draw.rectangle(primary.bbox, outline=(255, 80, 80), width=2)
        draw.ellipse(
            (
                primary.centroid_x - 3,
                primary.centroid_y - 3,
                primary.centroid_x + 3,
                primary.centroid_y + 3,
            ),
            fill=(255, 80, 80),
        )

    for comp in secondaries:
        draw.rectangle(comp.bbox, outline=(80, 220, 255), width=2)
        draw.ellipse(
            (
                comp.centroid_x - 3,
                comp.centroid_y - 3,
                comp.centroid_x + 3,
                comp.centroid_y + 3,
            ),
            fill=(80, 220, 255),
        )

    overlay.save(out_path)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OVERLAY_DIR.mkdir(parents=True, exist_ok=True)
    for old_overlay in OVERLAY_DIR.glob("*.png"):
        old_overlay.unlink()

    meta = pd.read_csv(META_PATH)
    meta["objid"] = meta["objid"].astype(str)
    meta = meta.drop_duplicates(subset="objid", keep="first")

    rows = []
    for idx, path in enumerate(valid_raw_paths(), start=1):
        objid = path.stem
        try:
            gray = load_gray(path)
            rgb = load_rgb(path)
        except Exception:
            continue

        comps = extract_components(gray, rgb)
        primary = choose_primary(comps)
        secondaries = secondary_components(primary, comps)
        bg, sigma = robust_background(gray)
        brightest_secondary_ratio = 0.0
        farthest_secondary_distance = 0.0
        if primary is not None and secondaries:
            brightest_secondary_ratio = float(secondaries[0].flux / (primary.flux + 1e-6))
            farthest_secondary_distance = float(
                max(
                    np.hypot(c.centroid_x - primary.centroid_x, c.centroid_y - primary.centroid_y)
                    for c in secondaries
                )
            )

        rows.append(
            {
                "objid": objid,
                "raw_path": str(path),
                "total_components": len(comps),
                "secondary_components": len(secondaries),
                "primary_flux": 0.0 if primary is None else primary.flux,
                "primary_center_distance": np.nan if primary is None else primary.center_distance,
                "brightest_secondary_flux_ratio": brightest_secondary_ratio,
                "farthest_secondary_distance_px": farthest_secondary_distance,
                "asymmetry_score": asymmetry_score(gray),
                "background_level": bg,
                "background_sigma": sigma,
                "component_json": json.dumps(
                    [
                        {
                            "area": c.area,
                            "flux": round(c.flux, 2),
                            "centroid_x": round(c.centroid_x, 1),
                            "centroid_y": round(c.centroid_y, 1),
                            "center_distance": round(c.center_distance, 1),
                            "bbox": c.bbox,
                            "g_r": round(c.g_r, 3),
                            "r_i": round(c.r_i, 3),
                        }
                        for c in comps
                    ]
                ),
            }
        )

        if idx % 500 == 0:
            print(f"Scanned {idx} images...")

    df = pd.DataFrame(rows)
    df = df.merge(meta[["objid", "ra", "dec", "petroMag_r", "petroR50_r"]], on="objid", how="left")

    features = df[
        [
            "total_components",
            "secondary_components",
            "brightest_secondary_flux_ratio",
            "farthest_secondary_distance_px",
            "asymmetry_score",
        ]
    ].fillna(0.0)

    iso = IsolationForest(
        n_estimators=200,
        contamination=0.03,
        random_state=42,
        n_jobs=-1,
    )
    iso.fit(features)
    df["secondary_object_score"] = -iso.score_samples(features)
    df["secondary_object_flag"] = (
        (df["secondary_components"] >= 1)
        & (
            (df["brightest_secondary_flux_ratio"] >= SECONDARY_FLUX_RATIO)
            | (df["secondary_object_score"] >= df["secondary_object_score"].quantile(0.97))
        )
    )

    df = df.sort_values(
        ["secondary_object_flag", "secondary_components", "secondary_object_score", "brightest_secondary_flux_ratio"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)

    # Create proof overlays for the strongest detections.
    overlay_candidates = df[df["secondary_object_flag"]].head(MAX_OVERLAYS)
    for _, row in overlay_candidates.iterrows():
        path = Path(row["raw_path"])
        gray = load_gray(path)
        rgb = load_rgb(path)
        comps = extract_components(gray, rgb)
        primary = choose_primary(comps)
        secondaries = secondary_components(primary, comps)
        overlay_path = OVERLAY_DIR / f"{row['objid']}_overlay.png"
        overlay_components(path, primary, secondaries, overlay_path)
        df.loc[df["objid"] == row["objid"], "overlay_path"] = str(overlay_path)

    csv_path = OUT_DIR / "raw_object_scan.csv"
    df.to_csv(csv_path, index=False)

    flagged = df[df["secondary_object_flag"]]
    top = flagged.head(20)
    summary_lines = [
        "# Raw JPG Secondary Object Scan",
        "",
        "This scan works directly on valid 256x256 JPG cutouts in `data/raw`.",
        "It detects multiple luminous components in the image plane and ranks cutouts by secondary-object evidence.",
        "",
        f"- Valid JPGs scanned: **{len(df)}**",
        f"- Flagged multi-component candidates: **{len(flagged)}**",
        f"- Overlay proofs generated: **{min(len(flagged), MAX_OVERLAYS)}**",
        "",
        "## Detection Logic",
        "",
        "1. Estimate background from the image border.",
        f"2. Threshold smoothed grayscale flux above background + {THRESHOLD_SIGMA:.1f} sigma.",
        "3. Label connected components and choose a primary source near the image center.",
        f"4. Count separated secondary components within {MAX_SECONDARY_DISTANCE:.0f} px of the center and >= {SECONDARY_FLUX_RATIO * 100:.0f}% of the primary flux.",
        "5. Rank candidates with Isolation Forest over component-count and asymmetry features.",
        "",
        "## Top Candidates",
        "",
        "| ObjID | RA | Dec | Secondary Components | Secondary Flux Ratio | Score | Overlay |",
        "|---|---|---|---|---|---|---|",
    ]
    for _, row in top.iterrows():
        overlay = Path(str(row.get("overlay_path", ""))).name if pd.notna(row.get("overlay_path")) else ""
        summary_lines.append(
            f"| {row['objid']} | {row['ra']:.4f} | {row['dec']:.4f} | "
            f"{int(row['secondary_components'])} | {row['brightest_secondary_flux_ratio']:.3f} | "
            f"{row['secondary_object_score']:.4f} | {overlay} |"
        )

    (OUT_DIR / "raw_object_scan_summary.md").write_text("\n".join(summary_lines) + "\n")
    print(f"Saved {csv_path}")
    print(f"Saved {OUT_DIR / 'raw_object_scan_summary.md'}")


if __name__ == "__main__":
    main()
