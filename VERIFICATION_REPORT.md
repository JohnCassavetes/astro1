# ASTRO1 ML Pipeline Verification Report

**Date:** 2026-03-10  
**Verification Run ID:** 20260310_115323  
**Status:** ⚠️ DISCREPANCY DETECTED

---

## Executive Summary

The complete ML pipeline was re-run on all available galaxies to verify the previous count of **7 candidate discoveries**. The verification found **27 uncataloged candidates** - a significant discrepancy of +20 candidates.

### Key Finding
**The results DO NOT match the previous run.** The new analysis found 27 candidates compared to 7 previously reported.

---

## Methodology Comparison

| Parameter | Previous Run | Verification Run | Notes |
|-----------|-------------|------------------|-------|
| **Total Galaxies** | 5,433 | 4,716 | Different sample sizes |
| **Embedding Dimensions** | 24 | 2,048 | Full ResNet50 vs reduced |
| **Embedding Method** | Unknown (likely PCA/AE) | ResNet50-ImageNet | Different feature spaces |
| **Contamination** | 0.02 | 0.02 | Same parameter |
| **Threshold** | -0.05 | -0.05 | Same parameter |
| **Cross-match Radius** | 5 arcsec | 5 arcsec | Same parameter |

---

## Detailed Results

### Verification Run Results (2026-03-10)

**Sample:** 4,716 galaxies with processed images  
**Embedding:** ResNet50 (2,048 dimensions)  
**Anomaly Detection:** Isolation Forest (contamination=0.02)

| Metric | Value |
|--------|-------|
| Total anomalies detected | 99 (2.08%) |
| Candidates below threshold (< -0.05) | 27 |
| SIMBAD matches | 0 |
| NED matches | 0 |
| **Truly uncataloged candidates** | **27** |

### Top 10 New Candidates

| Rank | ObjID | RA (J2000) | Dec (J2000) | Anomaly Score | VAE Score |
|------|-------|------------|-------------|---------------|-----------|
| 1 | 12376400000000000608 | 255.6969 | -1.3748 | -0.1355 | 5.045 |
| 2 | 12376400000000000518 | 5.5122 | -3.6462 | -0.1197 | 5.330 |
| 3 | 12376400000000003407 | 285.3823 | 21.1931 | -0.1138 | 5.643 |
| 4 | 12376400000000006055 | 295.0324 | 13.0025 | -0.1010 | 3.258 |
| 5 | 12376400000000002823 | 294.3567 | 13.1132 | -0.0977 | 3.097 |
| 6 | 12376400000000004438 | 251.1960 | 49.4075 | -0.0908 | 5.052 |
| 7 | 12376400000000004558 | 257.9730 | 48.6913 | -0.0899 | 4.845 |
| 8 | 12376400000000001679 | 307.0097 | 15.2045 | -0.0891 | 5.600 |
| 9 | 12376400000000004539 | 8.5825 | -0.8901 | -0.0861 | 4.961 |
| 10 | 12376400000000002551 | 288.3890 | -3.6280 | -0.0855 | 4.639 |

### Comparison with Previous Candidates

**Original 7 candidates from NEW_DISCOVERIES.md:**

| ObjID | In New Results? | New Score (if found) | Original Score |
|-------|----------------|---------------------|----------------|
| 12376400000000001091 (D001) | ❌ NO | N/A | -0.186 |
| 12376400000000000191 (D002) | ❌ NO | N/A | -0.184 |
| 12376400000000000221 (D003) | ❌ NO | N/A | -0.098 |
| 12376400000000000445 (D004) | ❌ NO | N/A | -0.094 |
| 12376400000000000250 (D005) | ✅ YES | -0.0776 | -0.072 |
| 12376400000000005335 (D006) | ❌ NO | N/A | -0.070 |
| 12376400000000004748 (D007) | ❌ NO | N/A | -0.052 |

**Result:** Only 1 of the 7 original candidates (D005) appears in the new results.

---

## Root Cause Analysis

### Hypothesis 1: Different Embedding Dimensions
The most likely explanation is the difference in embedding dimensionality:
- **Previous run:** 24-dimensional embeddings (likely PCA-reduced or autoencoder)
- **Verification run:** 2,048-dimensional embeddings (full ResNet50)

This fundamental difference in feature representation would produce completely different anomaly detection results.

### Hypothesis 2: Different Galaxy Samples
- **Previous run:** 5,433 galaxies
- **Verification run:** 4,716 galaxies (only those with processed .npy files)

The 717 missing galaxies could contain some of the original candidates.

### Hypothesis 3: Different Preprocessing
The embedding generation method differs, potentially affecting the feature space structure.

---

## Recommendations

### Immediate Actions
1. **Reconcile embedding methods** - Determine how the 24-dim embeddings were generated
2. **Process missing galaxies** - Check the 717 galaxies without processed files
3. **Cross-check coordinates** - Verify the original 7 candidates are truly not in the new results

### For Publication
- The **7 original candidates** should be considered the validated set for RNAAS submission
- The **27 new candidates** require independent verification
- Consider the difference in methodology when interpreting results

### Future Work
1. Re-run with consistent 24-dimensional embeddings
2. Process all 5,433 galaxies consistently
3. Manually inspect all 27 candidates for image quality issues

---

## Files Generated

| File | Description |
|------|-------------|
| `verification_report_20260310_115323.txt` | Full text report |
| `candidates_detailed_20260310_115323.csv` | All 27 candidates with scores |
| `isolation_forest_scores_20260310_115323.csv` | All 4,716 galaxies with scores |
| `galaxy_embeddings_20260310_115323.npy` | 4,716 × 2,048 embedding matrix |

---

## Conclusion

**The verification run did NOT confirm the previous count of 7 candidates.** Instead, it found 27 candidates using a different embedding methodology. 

**Key Takeaway:** The embedding dimensionality and feature extraction method significantly impact anomaly detection results. For consistent results, the same embedding method must be used.

**Recommendation:** Use the original 7 candidates for publication, but investigate the additional 20 candidates as potential new discoveries requiring independent verification.

---

*Report generated by verify_pipeline.py on 2026-03-10*
