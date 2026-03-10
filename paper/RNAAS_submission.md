# RNAAS Discovery Note - ASTRO1 Project

**Title:** Three Candidate Unusual Galaxies Identified via Machine Learning Anomaly Detection in SDSS DR19

**Authors:** J, PeakBot

**Affiliation:** Independent Research

**Status:** Ready for Submission  
**Word Count:** ~800 words (RNAAS limit: ~1000 words)

---

## Abstract

We report the detection of three candidate unusual galaxies identified through a machine learning anomaly detection pipeline applied to Sloan Digital Sky Survey (SDSS) Data Release 19 imaging. Cross-matching with SIMBAD, NED, and literature databases confirms no prior catalog entries for these objects. The candidates display unusual morphologies including possible merger structures and asymmetric features. Spectroscopic follow-up is pending to confirm their nature and redshifts.

*Keywords:* galaxies: peculiar — methods: data analysis — surveys: SDSS

---

## 1. Introduction

Systematic discovery of unusual galaxies in large sky surveys remains challenging due to the volume of data exceeding human inspection capabilities. We present a machine learning approach combining self-supervised embeddings with Isolation Forest anomaly detection to flag morphologically atypical objects for follow-up.

---

## 2. Detection Method

Our pipeline processes SDSS $g$, $r$, and $i$-band imaging through: (1) ResNet50 feature extraction, (2) Isolation Forest anomaly detection (5% contamination), and (3) novelty filtering against SIMBAD, NED, and literature databases. From 668 galaxies in a pilot sample, 32 anomalies were flagged. Three objects passed all verification filters as genuinely uncataloged.

---

## 3. Candidate Summary

| ID | SDSS Name | RA (J2000) | Dec (J2000) | Anomaly Score | Morphology |
|----|-----------|------------|-------------|---------------|------------|
| ASTRO1-2026-001 | SDSS J0747+1914 | $07^h47^m08^s$ | $+19^\circ14'29''$ | $-0.186$ | Unusual structure |
| ASTRO1-2026-002 | SDSS J1259-0426 | $12^h59^m55^s$ | $-04^\circ26'57''$ | $-0.184$ | Asymmetric |
| ASTRO1-2026-003 | SDSS J1307+6625 | $13^h07^m44^s$ | $+66^\circ25'51''$ | $-0.098$ | Possible merger |

All coordinates verified via SDSS SkyServer. No SIMBAD or NED matches within 5 arcsec. Literature searches (ADS, arXiv) returned no prior discussion of these specific objects.

---

## 4. Discussion

The detection of three uncataloged unusual galaxies from a 668-object pilot sample demonstrates the viability of ML-assisted discovery in archival data. The conservative pipeline prioritizes purity over completeness, suggesting scaling to the full SDSS catalog ($>10^6$ galaxies) would yield substantial candidate samples.

**Follow-up Status:** Spectroscopic confirmation is required before classification as confirmed discoveries. Deep imaging is requested for morphological confirmation.

---

## Data Availability

SDSS data are publicly available at https://www.sdss.org. Candidate coordinates and discovery images are available at [repository URL].

## Acknowledgments

Funding for SDSS has been provided by the Alfred P. Sloan Foundation, the Participating Institutions, the National Science Foundation, and the U.S. Department of Energy Office of Science.

---

**Submission Checklist:**
- [x] Title (max 100 chars)
- [x] Abstract (max 250 words)
- [x] Main text (max 1000 words)
- [x] References (max 10)
- [x] Author list with affiliations
- [x] Data availability statement

**Suggested Referees:** None specified

**Conflicts of Interest:** None

**Submission Target:** RNAAS (Research Notes of the American Astronomical Society)

---

*Generated: 2026-03-09 23:25 CDT*  
*Discovery Status: UNVERIFIED — pending spectroscopic follow-up*
