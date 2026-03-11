# Raw JPG Secondary Object Scan

This scan works directly on valid 256x256 JPG cutouts in `data/raw`.
It detects multiple luminous components in the image plane and ranks cutouts by secondary-object evidence.

- Valid JPGs scanned: **4690**
- Flagged multi-component candidates: **190**
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
| 12376400000000001338 | 218.9912 | 67.5873 | 4 | 0.958 | 0.7729 | 12376400000000001338_overlay.png |
| 12376400000000006031 | 301.0046 | 10.1879 | 4 | 0.570 | 0.7467 | 12376400000000006031_overlay.png |
| 12376400000000001158 | 207.1380 | 41.4644 | 4 | 0.637 | 0.7431 | 12376400000000001158_overlay.png |
| 12376400000000006823 | 302.0423 | 12.5660 | 3 | 0.428 | 0.7975 | 12376400000000006823_overlay.png |
| 12376400000000000518 | 5.5122 | -3.6462 | 3 | 1.526 | 0.7950 | 12376400000000000518_overlay.png |
| 12376400000000003748 | 148.4919 | 13.5880 | 3 | 0.660 | 0.7678 | 12376400000000003748_overlay.png |
| 12376400000000003678 | 247.7763 | 30.1903 | 3 | 0.712 | 0.7592 | 12376400000000003678_overlay.png |
| 12376400000000003698 | 181.9933 | 44.4522 | 3 | 0.557 | 0.7582 | 12376400000000003698_overlay.png |
| 12376400000000000618 | 16.1363 | -11.9814 | 3 | 0.291 | 0.7578 | 12376400000000000618_overlay.png |
| 12376400000000001538 | 189.8343 | 50.7169 | 3 | 0.482 | 0.7549 | 12376400000000001538_overlay.png |
| 12376400000000003458 | 172.5775 | 50.3207 | 3 | 0.771 | 0.7547 | 12376400000000003458_overlay.png |
| 12376400000000000778 | 330.2056 | 43.9581 | 3 | 0.771 | 0.7534 | 12376400000000000778_overlay.png |
| 12376400000000000138 | 269.7632 | 40.5230 | 3 | 0.637 | 0.7422 | 12376400000000000138_overlay.png |
| 12376400000000004848 | 42.3456 | -5.1550 | 3 | 0.564 | 0.7359 | 12376400000000004848_overlay.png |
| 12376400000000004948 | 139.2397 | 16.7370 | 3 | 0.326 | 0.7296 | 12376400000000004948_overlay.png |
| 12376400000000005111 | 299.0423 | 11.2242 | 2 | 0.871 | 0.7859 | 12376400000000005111_overlay.png |
| 12376400000000003618 | 180.2596 | 36.4812 | 2 | 0.433 | 0.7828 | 12376400000000003618_overlay.png |
| 12376400000000006143 | 301.4907 | 14.5044 | 2 | 0.791 | 0.7801 | 12376400000000006143_overlay.png |
| 12376400000000004128 | 46.3083 | 2.8992 | 2 | 2.940 | 0.7796 | 12376400000000004128_overlay.png |
| 12376400000000004278 | 243.6663 | 31.4910 | 2 | 2.673 | 0.7788 | 12376400000000004278_overlay.png |
