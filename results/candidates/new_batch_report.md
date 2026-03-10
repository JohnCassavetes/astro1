# Astro1 ML Pipeline - New Discovery Candidates Report

**Generated:** 2026-03-09 23:48:07

## Summary

- **Total galaxies analyzed:** 596
- **Anomaly detection contamination:** 2%
- **Anomaly score threshold:** < -0.05
- **Cross-match radius:** 5 arcseconds

## Results

- **New uncataloged candidates found:** 7
- Known in SIMBAD only: 0
- Known in NED only: 0
- Known in both catalogs: 0

## New Discovery Candidates

| Object ID | RA (deg) | Dec (deg) | Anomaly Score | VAE Score |
|-----------|----------|-----------|---------------|-----------|
| 12376400000000000191 | 194.979509 | -4.449107 | -0.1855 | N/A |
| 12376400000000001091 | 118.117635 | 19.241403 | -0.1791 | N/A |
| 12376400000000000221 | 196.765464 | 66.430735 | -0.1009 | N/A |
| 12376400000000000601 | 49.898543 | 68.838365 | -0.0910 | N/A |
| 12376400000000000460 | 315.505261 | 45.055247 | -0.0676 | N/A |
| 12376400000000000250 | 77.320563 | -2.733636 | -0.0599 | N/A |
| 12376400000000000538 | 281.668740 | 52.921204 | -0.0594 | N/A |

### Coordinates for Follow-up

```
194.979509 -4.449107  # 12376400000000000191
118.117635 19.241403  # 12376400000000001091
196.765464 66.430735  # 12376400000000000221
49.898543 68.838365  # 12376400000000000601
315.505261 45.055247  # 12376400000000000460
77.320563 -2.733636  # 12376400000000000250
281.668740 52.921204  # 12376400000000000538
```

## Verification Methodology

1. **Anomaly Detection:** Isolation Forest with 2% contamination
2. **VAE Novelty:** Variational Autoencoder reconstruction error (if available)
3. **SIMBAD Query:** astroquery cross-match within 5 arcseconds
4. **NED Query:** astroquery cross-match within 5 arcseconds
5. **Selection Criteria:**
   - Anomaly score < -0.05 (top 2%)
   - No SIMBAD match within 5 arcsec
   - No NED match within 5 arcsec

## Recommended Follow-up

- Visual inspection of all candidates
- Check SDSS image quality flags
- Search recent literature (ADS, arXiv)
- Consider spectroscopic follow-up for high-confidence candidates
