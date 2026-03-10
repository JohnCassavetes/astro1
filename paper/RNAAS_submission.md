# RNAAS Discovery Note - ASTRO1 Project

**Title:** Candidate Unusual Galaxies Identified via Machine Learning Anomaly Detection in SDSS DR19

**Authors:** J, PeakBot

**Affiliation:** Independent Research

**Status:** 🚧 DRAFT - NOT YET SUBMITTED  
**Word Count:** ~800 words (RNAAS limit: ~1000 words)

---

## 🚧 IMPORTANT: WORK IN PROGRESS

This RNAAS note is currently being drafted. We are processing the full dataset of **~6,800 galaxies** in batches of 500 to maximize the candidate sample before submission.

**Current Status:**
- ✅ Pilot batch: 7 candidates from 596 galaxies (1.2% rate)
- ⏳ Batch processing: ~5,400 additional galaxies pending
- 📊 Projected total: ~65+ candidates at current detection rate
- 🎯 Submission target: Maximum sample size (~70-80 candidates)

---

## Abstract

We report the detection of candidate unusual galaxies identified through a machine learning anomaly detection pipeline applied to Sloan Digital Sky Survey (SDSS) Data Release 19 imaging. Cross-matching with SIMBAD, NED, and literature databases confirms no prior catalog entries for these objects. The candidates display unusual morphologies including possible merger structures and asymmetric features. Spectroscopic follow-up is pending to confirm their nature and redshifts.

*Keywords:* galaxies: peculiar — methods: data analysis — surveys: SDSS

---

## 1. Introduction

Systematic discovery of unusual galaxies in large sky surveys remains challenging due to the volume of data exceeding human inspection capabilities. We present a machine learning approach combining feature extraction with Isolation Forest anomaly detection to flag morphologically atypical objects for follow-up.

---

## 2. Detection Method

Our pipeline processes SDSS $g$, $r$, and $i$-band imaging through: (1) Fast feature extraction (24-dim vectors), (2) Isolation Forest anomaly detection (2% contamination), and (3) novelty filtering against SIMBAD, NED, and literature databases.

**Processing Strategy:**
- Total dataset: ~6,800 galaxies
- Batch size: 500 galaxies per processing run
- This approach prevents token limit exhaustion while maximizing sample size
- All batches use identical detection parameters for consistency

---

## 3. Candidate Summary

| ID | SDSS Name | RA (J2000) | Dec (J2000) | Anomaly Score | Status |
|----|-----------|------------|-------------|---------------|--------|
| ASTRO1-2026-001 | SDSS J0747+1914 | $07^h47^m08^s$ | $+19^\circ14'29''$ | $-0.179$ | ✅ Confirmed uncataloged |
| ASTRO1-2026-002 | SDSS J1259-0426 | $12^h59^m55^s$ | $-04^\circ26'57''$ | $-0.186$ | ✅ Confirmed uncataloged |
| ASTRO1-2026-003 | SDSS J1307+6625 | $13^h07^m44^s$ | $+66^\circ25'51''$ | $-0.101$ | ✅ Confirmed uncataloged |
| ... | ... | ... | ... | ... | ⏳ Processing batches |

**Verification Status:**
- ✅ No SIMBAD matches within 5 arcsec (all verified candidates)
- ✅ No NED matches within 5 arcsec (all verified candidates)
- ✅ No SDSS spectroscopic observations (top candidates)

---

## 4. Discussion

The detection of uncataloged unusual galaxies from our pilot sample demonstrates the viability of ML-assisted discovery in archival data. The conservative pipeline prioritizes purity over completeness, suggesting scaling to the full SDSS catalog ($>10^6$ galaxies) would yield substantial candidate samples.

**Follow-up Status:** Spectroscopic confirmation is required before classification as confirmed discoveries. Deep imaging is requested for morphological confirmation.

---

## Data Availability

SDSS data are publicly available at https://www.sdss.org. Candidate coordinates and discovery images are available at [repository URL].

## Acknowledgments

Funding for SDSS has been provided by the Alfred P. Sloan Foundation, the Participating Institutions, the National Science Foundation, and the U.S. Department of Energy Office of Science.

---

**Submission Checklist:**
- [ ] Title (max 100 chars)
- [ ] Abstract (max 250 words)
- [ ] Main text (max 1000 words)
- [ ] References (max 10)
- [ ] Author list with affiliations
- [ ] Data availability statement
- [ ] FINAL CANDIDATE COUNT from all batches
- [ ] Visual inspection complete for all candidates

**Status: 🚧 DRAFT - Awaiting batch processing completion**

**Submission Target:** RNAAS (Research Notes of the American Astronomical Society)

---

*Generated: 2026-03-10*  
*Discovery Status: CANDIDATE POOL GROWING - pending full batch processing*
