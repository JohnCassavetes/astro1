# Candidate Detection Registry

## Detection Schema

Each detection must include:

```json
{
  "detection_id": "D001",
  "ra": 123.4567,
  "dec": -45.6789,
  "ra_err": 0.001,
  "dec_err": 0.001,
  "object_type": "planet_candidate|unusual_galaxy|anomalous_stellar",
  "detection_date": "2026-03-09",
  "mjd": 60700.5,
  "survey": "SDSS",
  "data_release": "DR19",
  "run": 756,
  "camcol": 3,
  "field": 125,
  "ml_confidence": 0.95,
  "anomaly_score": -0.45,
  "image_uri": "data/raw/1237645...jpg",
  "cutout_size_arcsec": 30,
  "magnitude_r": 20.5,
  "novelty_label": "uncataloged_candidate|known_object|artifact",
  "verification": {
    "simbad_checked": true,
    "simbad_match": false,
    "ned_checked": true,
    "ned_match": false,
    "exoplanet_archive_checked": true,
    "exoplanet_match": false,
    "vizier_checked": true,
    "vizier_match": false,
    "literature_checked": false
  },
  "evidence_log": [
    "High ML confidence (0.95)",
    "Strong anomaly score (-0.45)",
    "No SIMBAD match within 5 arcsec",
    "No NED match within 5 arcsec"
  ],
  "reviewer_notes": "",
  "follow_up_priority": "high|medium|low"
}
```

## Detection Classes

1. **Planet Candidates**
   - Point sources with proper motion
   - Transient events
   - Astrometric anomalies

2. **Unusual Galaxies**
   - Merger remnants
   - Ring galaxies
   - Tidal features
   - Blue compact dwarfs
   - Ultra-diffuse galaxies

3. **Anomalous Stellar Objects**
   - Variable stars
   - Unusual colors
   - High proper motion
   - Binary candidates

## Verification Requirements

| Check | Database | Radius | Required |
|-------|----------|--------|----------|
| SIMBAD | CDS | 5 arcsec | Yes |
| NED | IPAC | 5 arcsec | Yes |
| Exoplanet Archive | NExScI | 10 arcsec | For planet candidates |
| VizieR | CDS | 5 arcsec | Yes |
| arXiv | SAO/NASA | Coordinate search | Recommended |

## Proof Package

For publication, each detection must have:
- [ ] JPEG cutout (256×256)
- [ ] FITS cutout if available
- [ ] Coordinate table entry
- [ ] ML confidence score
- [ ] Verification status table
- [ ] Before/after if time-domain available
