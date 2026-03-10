# STEP_BY_STEP_ANALYSIS.md
## Comprehensive Dual-Method Galaxy Anomaly Detection
### Generated: 2026-03-10 17:43:14

---

## 1. OVERVIEW

This analysis applies TWO independent anomaly detection methods to ALL available galaxy data:

**Method A**: 24-dimensional Custom VAE Embeddings + Isolation Forest  
**Method B**: 2048-dimensional ResNet50 Embeddings + Isolation Forest  

Both methods use:
- **Algorithm**: Isolation Forest
- **Contamination**: 0.02 (top 2% flagged as anomalies)
- **N_Estimators**: 100
- **Random State**: 42

---

## 2. DATA SUMMARY

### 2.1 Input Data
| Metric | Value |
|--------|-------|
| Total Raw Images | 6,390 |
| Processed Images | 4,866 |
| Galaxies with Embeddings | 4,716 |

### 2.2 Embedding Dimensions
| Method | Dimensions | Description |
|--------|------------|-------------|
| Method A | 24 | Custom VAE latent space |
| Method B | 2,048 | ResNet50 pre-classification features |

---

## 3. METHOD A: 24-DIM VAE EMBEDDINGS

### 3.1 Commands/Scripts Used
```python
# Loaded pre-computed 24-dim embeddings
emb_24 = np.load('results/embeddings/galaxy_embeddings.npy')
# Shape: (4716, 24)

# Standardized features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(emb_24)

# Isolation Forest
clf = IsolationForest(
    n_estimators=100,
    contamination=0.02,
    random_state=42,
    n_jobs=-1
)
clf.fit(X_scaled)
scores = clf.decision_function(X_scaled)
```

### 3.2 Processing Statistics
| Metric | Value |
|--------|-------|
| Galaxies Processed | 4690 |
| Anomalies Flagged | 95 |
| Anomaly Rate | 2.03% |

### 3.3 Output Files
- `results/method_a/method_a_full_results.csv` - Complete results with all metadata
- `results/method_a/method_a_scores.csv` - Simplified score table

---

## 4. METHOD B: 2048-DIM RESNET50 EMBEDDINGS

### 4.1 Commands/Scripts Used
```python
# Loaded pre-computed 2048-dim embeddings
emb_2048 = np.load('results/embeddings/galaxy_embeddings_20260310_115323.npy')
# Shape: (4716, 2048)

# Standardized features (critical for high-dimensional data)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(emb_2048)

# Isolation Forest
clf = IsolationForest(
    n_estimators=100,
    contamination=0.02,
    random_state=42,
    n_jobs=-1
)
clf.fit(X_scaled)
scores = clf.decision_function(X_scaled)
```

### 4.2 Processing Statistics
| Metric | Value |
|--------|-------|
| Galaxies Processed | 4690 |
| Anomalies Flagged | 93 |
| Anomaly Rate | 1.98% |

### 4.3 Output Files
- `results/method_b/method_b_full_results.csv` - Complete results with all metadata
- `results/method_b/method_b_scores.csv` - Simplified score table

---

## 5. CROSS-METHOD COMPARISON

### 5.1 Overlap Analysis
| Category | Count | Percentage |
|----------|-------|------------|
| Method A Only | 74 | 1.58% |
| Method B Only | 72 | 469000.00% |
| **Both Methods** | 21 | 0.45% |
| Either Method | 167 | 3.56% |

### 5.2 Cross-Method Statistics
| Metric | Value |
|--------|-------|
| Agreement Rate | 22.1% |
| Jaccard Index | 0.126 |

---

## 6. SIMBAD/NED VERIFICATION

### 6.1 Method A Verification
| Metric | Value |
|--------|-------|
| Candidates Queried | 100 |
| SIMBAD Matches | 95 |
| Uncataloged | 5 |

### 6.2 Method B Verification
| Metric | Value |
|--------|-------|
| Candidates Queried | 100 |
| SIMBAD Matches | 93 |
| Uncataloged | 7 |

---

## 7. TOP 20 CANDIDATES (COMBINED RANKING)

| Rank | Object ID | RA | Dec | Method A Score | Method B Score | In SIMBAD |
|------|-----------|-----|-----|----------------|----------------|-----------|
| 1 | 12376400000000002823 | 294.3567 | 13.1132 | -0.1438 | -0.1047 | No |
| 2 | 12376400000000002711 | 287.9299 | 17.8975 | -0.1613 | -0.0792 | No |
| 3 | 12376400000000006055 | 295.0324 | 13.0025 | -0.1372 | -0.0974 | No |
| 4 | 12376400000000003127 | 298.3821 | 16.7789 | -0.1389 | -0.0633 | No |
| 5 | 12376400000000001375 | 297.8574 | 17.7557 | -0.1000 | -0.0807 | No |
| 6 | 12376400000000005879 | 285.2392 | 17.2265 | -0.1249 | -0.0445 | No |
| 7 | 12376400000000003431 | 293.8830 | 13.0522 | -0.0946 | -0.0558 | No |
| 8 | 12376400000000006826 | 180.4977 | 43.0300 | -0.2044 | -0.0115 | No |
| 9 | 12376400000000004901 | 185.5928 | 6.1413 | -0.1216 | -0.0248 | No |
| 10 | 12376400000000005431 | 297.1979 | 20.7546 | -0.0971 | -0.0325 | No |
| 11 | 12376400000000002848 | 43.4452 | -4.2371 | -0.1679 | -0.0076 | No |
| 12 | 12376400000000006695 | 297.6943 | 21.4950 | -0.0656 | -0.0436 | No |
| 13 | 12376400000000002551 | 288.3890 | -3.6280 | -0.0139 | -0.0743 | No |
| 14 | 12376400000000003848 | 48.8548 | 1.9005 | -0.0383 | -0.0306 | No |
| 15 | 12376400000000003488 | 40.9595 | -11.8260 | -0.0389 | -0.0292 | No |
| 16 | 12376400000000006365 | 192.2084 | 14.1528 | -0.1486 | 0.0021 | No |
| 17 | 12376400000000001936 | 49.0295 | -5.9507 | -0.1440 | 0.0038 | No |
| 18 | 12376400000000001091 | 118.1176 | 19.2414 | -0.1136 | -0.0004 | No |
| 19 | 12376400000000003567 | 292.7500 | 13.8082 | -0.1086 | 0.0003 | No |
| 20 | 12376400000000006390 | 248.1755 | 39.9705 | -0.1386 | 0.0082 | No |


---

## 8. UNCATALOGED CANDIDATES

### 8.1 Uncataloged in Top 100 (Combined)
Total uncataloged candidates in top 100: 50

### 8.2 Uncataloged by Method
| Method | Uncataloged Count |
|--------|-------------------|
| Method A | 95 |
| Method B | 93 |

---

## 9. SUMMARY & CONCLUSIONS

### 9.1 Key Findings
1. **Total Galaxies Processed**: 4690
2. **Method A Anomalies**: 95 (2.03%)
3. **Method B Anomalies**: 93 (1.98%)
4. **Both Methods Agree**: 21 galaxies
5. **Top 20 Uncataloged**: 50 candidates not in SIMBAD

### 9.2 Method Comparison
- **Method A (VAE)**: Captures semantic/reconstruction-based anomalies
- **Method B (ResNet)**: Captures visual/feature-based anomalies
- **High-Agreement Candidates**: 21 galaxies flagged by both methods are strongest candidates

### 9.3 Output Files Summary
```
results/
├── method_a/
│   ├── method_a_full_results.csv
│   └── method_a_scores.csv
├── method_b/
│   ├── method_b_full_results.csv
│   └── method_b_scores.csv
├── comparison/
│   ├── cross_method_comparison.csv
│   ├── cross_method_stats.json
│   ├── method_a_verification.csv
│   ├── method_b_verification.csv
│   ├── top_20_candidates.csv
│   └── uncataloged_candidates.csv
└── STEP_BY_STEP_ANALYSIS.md (this file)
```

---

## 10. TECHNICAL NOTES

### 10.1 Preprocessing
- All embeddings were standardized using StandardScaler before Isolation Forest
- Standardization is especially important for Method B's high-dimensional features

### 10.2 Isolation Forest Parameters
- Contamination set to 0.02 (2%) to identify most extreme outliers
- 100 trees provide stable anomaly scoring
- Random state fixed for reproducibility

### 10.3 Verification Methodology
- SIMBAD queried via TAP service with 5 arcsec radius
- Objects with any SIMBAD match considered "cataloged"
- Uncataloged = no SIMBAD entry within search radius

---

*Analysis completed: 2026-03-10 17:43:14*
