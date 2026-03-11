# Raw JPG Secondary Object Scan

This scan works directly on valid 256x256 JPG cutouts in `data/raw`.
It detects multiple luminous components in the image plane and ranks cutouts by secondary-object evidence.

- Valid JPGs scanned: **4690**
- Flagged multi-component candidates: **605**
- Overlay proofs generated: **20**

## Detection Logic

1. Estimate background from the image border.
2. Threshold smoothed grayscale flux above background + 7.0 sigma.
3. Label connected components and choose a primary source near the image center.
4. Count separated secondary components within 70 px of the center and >= 15% of the primary flux.
5. Rank candidates with Isolation Forest over component-count and asymmetry features.

## Top Candidates

| ObjID | RA | Dec | Secondary Components | Secondary Flux Ratio | Score | Overlay |
|---|---|---|---|---|---|---|
| 12376400000000006791 | 305.5417 | 8.2974 | 7 | 1.509 | 0.7743 | 12376400000000006791_overlay.png |
| 12376400000000001618 | 173.2024 | 43.3572 | 6 | 7.328 | 0.7675 | 12376400000000001618_overlay.png |
| 12376400000000000518 | 5.5122 | -3.6462 | 6 | 1.526 | 0.7574 | 12376400000000000518_overlay.png |
| 12376400000000000578 | 316.3732 | -2.7793 | 6 | 0.642 | 0.7156 | 12376400000000000578_overlay.png |
| 12376400000000006823 | 302.0423 | 12.5660 | 5 | 0.428 | 0.7676 | 12376400000000006823_overlay.png |
| 12376400000000001338 | 218.9912 | 67.5873 | 5 | 1.745 | 0.7399 | 12376400000000001338_overlay.png |
| 12376400000000003748 | 148.4919 | 13.5880 | 5 | 0.660 | 0.7189 | 12376400000000003748_overlay.png |
| 12376400000000000918 | 270.2176 | 60.6475 | 5 | 0.596 | 0.7035 | 12376400000000000918_overlay.png |
| 12376400000000004358 | 247.0878 | 31.0770 | 5 | 0.810 | 0.7025 | 12376400000000004358_overlay.png |
| 12376400000000004288 | 56.2217 | -3.3529 | 4 | 2.365 | 0.7691 | 12376400000000004288_overlay.png |
| 12376400000000003618 | 180.2596 | 36.4812 | 4 | 0.433 | 0.7465 | 12376400000000003618_overlay.png |
| 12376400000000003223 | 290.6874 | 14.0176 | 4 | 0.608 | 0.7268 | 12376400000000003223_overlay.png |
| 12376400000000004528 | 53.1832 | -3.2078 | 4 | 2.519 | 0.7239 | 12376400000000004528_overlay.png |
| 12376400000000004418 | 188.8866 | 43.4765 | 4 | 1.623 | 0.7227 | 12376400000000004418_overlay.png |
| 12376400000000000168 | 215.2076 | 22.0846 | 4 | 1.264 | 0.7144 | 12376400000000000168_overlay.png |
| 12376400000000003858 | 189.7672 | 45.4063 | 4 | 0.403 | 0.7133 | 12376400000000003858_overlay.png |
| 12376400000000006271 | 310.7255 | 9.9373 | 4 | 0.746 | 0.7066 | 12376400000000006271_overlay.png |
| 12376400000000004678 | 248.1750 | 34.5059 | 4 | 0.285 | 0.7044 | 12376400000000004678_overlay.png |
| 12376400000000003498 | 176.7322 | 49.8791 | 4 | 0.870 | 0.7031 | 12376400000000003498_overlay.png |
| 12376400000000004218 | 170.4368 | 37.9420 | 4 | 0.811 | 0.7030 | 12376400000000004218_overlay.png |
