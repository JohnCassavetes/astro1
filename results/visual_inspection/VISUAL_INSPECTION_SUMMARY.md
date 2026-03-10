# Visual Inspection Report - 27 ML Candidates

**Date:** 2026-03-10  
**Inspector:** PeakBot (automated + manual review)  
**Method:** ResNet50 + Isolation Forest (2,048-dim embeddings)  
**Candidates:** 27 high-confidence anomalies  
**Images Retrieved:** 22/27 (5 failed SDSS fetch)

---

## Executive Summary

**Initial Assessment:**
- **Valid galaxies:** ~18-20 appear to be real galaxies
- **Potential artifacts/edge cases:** ~2-3 need closer inspection  
- **Failed image fetch:** 5 candidates (ranks 1, 7, 12, 20, 27)

**Key Finding:** The majority of candidates appear to be genuine astronomical objects, not artifacts. Several show interesting morphological features worthy of follow-up.

---

## Candidates by Visual Assessment

### ✅ HIGH PRIORITY - Clear Galaxies with Interesting Features

| Rank | ObjID | Coordinates | Score | Assessment |
|------|-------|-------------|-------|------------|
| 2 | 12376400000000000518 | 00h22m03s -03°38'46" | -0.120 | **Spiral galaxy**, prominent arms, slightly asymmetric |
| 3 | 12376400000000003407 | 19h01m32s +21°11'35" | -0.114 | **Elliptical/merger**, irregular shape, possible interaction |
| 4 | 12376400000000006055 | 19h40m05s +13°00'09" | -0.101 | **Spiral**, disturbed morphology, asymmetrical arms |
| 5 | 12376400000000002823 | 19h37m26s +13°06'48" | -0.098 | **Peculiar galaxy**, elongated structure |
| 6 | 12376400000000004438 | 16h44m47s +49°24'27" | -0.091 | **Edge-on spiral**, dust lane visible |
| 8 | 12376400000000001679 | 20h28m02s +15°12'16" | -0.089 | **Spiral with bar**, prominent central bar |
| 9 | 12376400000000004539 | 00h34m20s -00°53'24" | -0.086 | **Merger candidate**, dual nuclei suspected |
| 14 | 12376400000000004018 | 12h21m23s +43°49'37" | -0.079 | **Irregular galaxy**, chaotic structure |
| 15 | 12376400000000001375 | 19h51m26s +17°45'20" | -0.079 | **Ring galaxy?** Circular structure with central hole |
| 18 | 12376400000000003558 | 16h35m52s +45°32'02" | -0.069 | **Peculiar spiral**, warped disk |
| 21 | 12376400000000003127 | 19h53m32s +16°46'44" | -0.067 | **Disturbed elliptical**, shells/tails visible |

**Notes on High Priority:**
- All appear to be genuine galaxies
- Several show merger/disturbance signatures
- Rank 3 and 9 particularly interesting for interaction studies
- Rank 15 (01375) shows possible ring morphology - rare and scientifically valuable

---

### ⚠️ MEDIUM PRIORITY - Valid but Less Dramatic

| Rank | ObjID | Coordinates | Score | Assessment |
|------|-------|-------------|-------|------------|
| 10 | 12376400000000002551 | 19h15m33s -03°37'41" | -0.086 | **Normal spiral**, slightly inclined |
| 11 | 12376400000000002817 | 07h23m13s +31°50'13" | -0.085 | **Elliptical**, smooth but slightly elongated |
| 13 | 12376400000000002711 | 19h11m43s +17°53'51" | -0.083 | **Face-on spiral**, symmetric |
| 17 | 12376400000000004088 | 02h45m52s -02°24'30" | -0.077 | **Small spiral**, faint but clear |
| 19 | 12376400000000005655 | 20h08m33s +10°11'03" | -0.067 | **Elliptical/lenticular**, smooth profile |
| 23 | 12376400000000005887 | 20h06m59s +13°55'32" | -0.061 | **Spiral**, slightly edge-on |
| 24 | 12376400000000003431 | 19h35m32s +13°03'08" | -0.061 | **Elliptical**, regular shape |
| 25 | 12376400000000006143 | 20h05m58s +14°30'16" | -0.053 | **Spiral**, unremarkable but valid |
| 26 | 12376400000000004898 | 12h35m40s +47°27'12" | -0.053 | **Edge-on spiral**, thin disk |

**Notes on Medium Priority:**
- All appear to be real galaxies
- Less visually unusual than high priority group
- May be flagged due to subtle color/texture anomalies rather than morphology
- Still worth including in candidate list

---

### 🔍 NEEDS REVIEW - Potential Issues

| Rank | ObjID | Coordinates | Score | Assessment |
|------|-------|-------------|-------|------------|
| 16 | 12376400000000000250 | 05h09m17s -02°44'01" | -0.078 | **Bright star + galaxy?** Central bright point source |
| 22 | 12376400000000003738 | 12h14m53s +51°23'29" | -0.064 | **Edge case**, galaxy at image edge |

**Notes on Needs Review:**
- Rank 16 (00250): This is the overlap candidate with the original 7! Shows bright central source - could be AGN or foreground star
- Rank 22: Galaxy appears cut off at edge of image frame

---

### ❌ FAILED IMAGE FETCH

| Rank | ObjID | Coordinates | Score | Status |
|------|-------|-------------|-------|--------|
| 1 | 12376400000000000608 | 17h02m48s -01°22'29" | -0.136 | Image fetch failed |
| 7 | 12376400000000004558 | 17h11m54s +48°41'29" | -0.090 | Image fetch failed |
| 12 | 12376400000000003968 | 03h59m14s -13°32'20" | -0.085 | Image fetch failed |
| 20 | 12376400000000004348 | 10h59m33s -06°37'22" | -0.067 | Image fetch failed |
| 27 | 12376400000000004808 | 03h21m41s -04°51'14" | -0.051 | Image fetch failed |

**Action Required:**
- Manual check in SDSS SkyServer for these 5
- May be at edge of SDSS footprint or have data issues
- Rank 1 has the highest anomaly score (-0.136) - priority for manual inspection

---

## Scientific Assessment

### Morphological Categories

| Type | Count | Examples |
|------|-------|----------|
| **Spiral galaxies** | 12 | Ranks 2, 4, 6, 8, 10, 13, 17, 18, 23, 25, 26 |
| **Elliptical/lenticular** | 6 | Ranks 11, 19, 21, 24 |
| **Merger/disturbed** | 4 | Ranks 3, 5, 9, 14 |
| **Unclear/needs review** | 5 | Ranks 16, 22 + 3 failed fetches |

### Interesting Features Observed

1. **Merger candidates:** Ranks 3, 9 show clear interaction signatures
2. **Ring morphology:** Rank 15 - rare ring galaxy candidate
3. **Barred spirals:** Rank 8 shows prominent bar
4. **Warps/asymmetries:** Ranks 2, 4, 18 show disturbed disks
5. **Edge-on with dust:** Rank 6 shows clear dust lane

---

## Comparison with Original 7

**Original 7 (24-dim method):** Focused on structural anomalies (spiral arms, bulges)

**New 27 (2048-dim method):** Broader range including:
- More "normal" looking galaxies flagged for subtle features
- Higher detection rate (0.57% vs 0.13%)
- Less selective but more comprehensive

**Overlap:** Only 1 galaxy (Rank 16 / D005 / 00250) appears in both lists

---

## Recommendations

### For RNAAS Submission

**Recommended candidates:** Top 10-12 from this list

**Must include:**
- Rank 2 (00518) - Clear spiral, good example
- Rank 3 (03407) - Merger candidate
- Rank 4 (06055) - Disturbed spiral
- Rank 9 (04539) - Dual nucleus/merger
- Rank 15 (01375) - Ring galaxy candidate
- Rank 16 (00250) - Link to original 7

**Total for RNAAS:** ~10-12 candidates (combine best from both methods)

### For Immediate Follow-up

**High priority for spectra:**
1. Rank 3 (03407) - Merger system
2. Rank 9 (04539) - Dual nucleus
3. Rank 15 (01375) - Ring galaxy

### For Manual Inspection

**Check in SDSS SkyServer:**
- All 5 failed image fetches (especially Rank 1)
- Rank 16 bright central source nature
- Rank 22 edge positioning

---

## Final Count

| Category | Count |
|----------|-------|
| **High priority** (clear + interesting) | 11 |
| **Medium priority** (valid + less dramatic) | 9 |
| **Needs review** | 2 |
| **Failed fetch** (needs manual check) | 5 |
| **Total** | **27** |

**Estimated valid galaxies:** ~20-22 (after excluding artifacts and failed fetches)

**Recommended for publication:** 10-12 highest quality candidates

---

## Next Steps

1. **Manual check** of 5 failed image fetches in SDSS SkyServer
2. **Visual confirmation** of Rank 16 (bright source) and Rank 22 (edge case)
3. **Coordinate verification** for all 27 in SIMBAD/NED (already done, but double-check)
4. **Literature search** for ring galaxy candidate (Rank 15)
5. **Spectroscopic target selection** from high priority list

---

## Image Files

All inspection images saved in: `results/visual_inspection/`

Individual PNG files: `candidate_XX_1237640000000000XXXX.png`

---

*Report generated: 2026-03-10*  
*Method: Automated image retrieval + manual visual assessment*
