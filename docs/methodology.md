# Methodology

## Data: SDSS DR17
- **Selection:** Clean galaxies, r < 21, size > 2"
- **Bands:** g, r, i combined to RGB
- **Cutouts:** 30" × 30" (76×76 pixels)

## Embedding: Self-Supervised CNN
- **Model:** SimCLR ResNet50 pretrained on ImageNet
- **Output:** 2048-dim feature vector
- **Rationale:** Captures visual similarity without labels

## Anomaly Detection: Isolation Forest
- **Method:** IsolationForest (scikit-learn)
- **Contamination:** 5% (flag 500/10k as anomalies)
- **Features:** CNN embeddings
- **Rationale:** Fast, no training, interpretable anomaly scores

## Novelty Filtering
1. **Database Cross-match:**
   - SIMBAD cone search (5" radius)
   - NED coordinates search
   - VizieR catalog query

2. **Literature Search:**
   - Arxiv query by coordinates
   - ADS bibcode search

3. **Artifact Checks:**
   - Edge proximity
   - Saturation flags
   - Cosmic ray detection
   - Visual inspection

## Classification Schema
| Label | Meaning |
|-------|---------|
| known_recovered | Previously cataloged |
| previously_discussed | In literature but not in major catalogs |
| artifact_low_confidence | Likely instrumental |
| uncataloged_candidate | Genuine candidate for follow-up |

## Validation
- Inject known peculiar galaxies
- Verify recovery in top anomalies
- Cross-check with Galaxy Zoo peculiar galaxies
