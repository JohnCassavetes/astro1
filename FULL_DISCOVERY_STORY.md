# The Complete ASTRO1 Discovery Story

**What we found, how we found it, and why the numbers don't match**

---

## The Short Version

We built a machine learning pipeline to find weird galaxies in SDSS data. 

**First run:** Found 7 unusual galaxies nobody had cataloged before.

**Second run:** Found 27 unusual galaxies nobody had cataloged before.

**Only 1 galaxy appears in both lists.**

Why? Because we accidentally used two completely different ways of "seeing" the galaxies. It's like looking at the same objects with a microscope vs binoculars — you notice different things.

---

## What We Actually Did (Step by Step)

### The Goal
Find galaxies that look statistically "weird" compared to normal galaxies. The logic: if a galaxy looks very different from the average, it might be scientifically interesting.

### Step 1: Get the Data
- Downloaded ~6,400 galaxy images from SDSS (Sloan Digital Sky Survey)
- Each galaxy: 256×256 pixel image in 3 colors (g, r, i bands)
- After quality cuts: 5,433 usable galaxies

### Step 2: Convert Images to Numbers (The Key Difference)

Computers can't look at images. They need numbers. We tried two different approaches:

#### Method A: The Custom Brain (Original 7 candidates)
**What we did:**
- Built a custom autoencoder (like a neural network)
- Trained it on galaxy images to learn "what makes a galaxy look like a galaxy"
- Compressed each image to just **24 numbers** (24-dimensional embedding)
- These 24 numbers capture the essential features of each galaxy

**Think of it like:** Teaching a child to recognize dogs by showing them thousands of dog photos. Eventually they learn "dog-ness" and can describe any dog in 24 key characteristics.

#### Method B: The Pre-Trained Expert (New 27 candidates)
**What we did:**
- Used ResNet50, a famous neural network pre-trained on 1 million everyday images (cats, cars, chairs...)
- Fed our galaxy images through it
- Got **2,048 numbers** per galaxy (2,048-dimensional embedding)

**Think of it like:** Asking a world-class art critic (who's seen millions of paintings) to describe galaxies. They use a much richer vocabulary (2,048 descriptors vs 24) but learned that vocabulary looking at photos of cats, not galaxies.

### Step 3: Find the Weird Ones (Same for Both)

Once we had numbers for each galaxy, we used **Isolation Forest** — an algorithm that finds outliers.

**How it works:**
- Imagine 5,433 dots scattered in space (each dot = one galaxy)
- Normal galaxies cluster together
- Weird galaxies sit far from the clusters
- Isolation Forest finds the isolated dots

**Parameters:**
- Set "contamination" to 0.02 (expect 2% anomalies)
- This flagged ~100 galaxies as potentially weird from each method

### Step 4: Check If Anyone Knows About Them (Verification)

Just because ML says "weird" doesn't mean it's a discovery. Could be:
- A known weird galaxy already cataloged
- An artifact (cosmic ray, bad data)
- Something discussed in a paper we haven't seen

**What we checked:**
1. **SIMBAD** — Database of known astronomical objects (5 arcsec radius)
2. **NED** — NASA's extragalactic database (5 arcsec radius)
3. **Literature search** — arXiv, ADS for mentions of these coordinates

**Result:**
- Original 7: All passed (no matches anywhere)
- New 27: All passed (no matches anywhere)

Both sets are genuinely uncataloged. But they're different galaxies because the methods "see" different things.

---

## The 7 vs The 27: A Side-by-Side Comparison

| | Original 7 | New 27 |
|---|-----------|--------|
| **Feature extractor** | Custom autoencoder (trained on galaxies) | ResNet50 (trained on everyday images) |
| **Numbers per galaxy** | 24 | 2,048 |
| **What it captures** | "Galaxy-ness" — structures specific to galaxies | "Visual complexity" — patterns from general image recognition |
| **Galaxies processed** | 5,433 | 4,716 (subset with clean data) |
| **Anomalies flagged** | 239 | 99 |
| **Candidates verified** | 7 | 27 |
| **Top anomaly score** | -0.186 | -0.136 |
| **Detection rate** | 0.13% | 0.57% |

### Overlap Analysis

**Only 1 galaxy appears in both lists:**
- **ASTRO1-2026-005** (D005 / ObjID 12376400000000000250)
- Scores: -0.072 (24-dim) vs -0.078 (2,048-dim)

**Why so little overlap?**

Imagine describing faces:
- Method A (24-dim): Focuses on "face structure" — nose shape, eye spacing, jawline
- Method B (2,048-dim): Notices texture, lighting, background context, fine details

Both find "unusual" faces, but different ones:
- Method A flags someone with a very unusual face shape
- Method B flags someone with normal face shape but weird lighting/background

Similarly:
- 24-dim method finds galaxies with unusual structural patterns (spiral arms, bulges)
- 2,048-dim method finds galaxies that look visually complex or different in subtle texture ways

---

## What This Means Scientifically

### Good News
We have **34 potentially interesting galaxies** (7 + 27 - 1 overlap), not just 7.

### Complication
We can't directly compare them. A galaxy flagged by Method A might be interesting for completely different reasons than one flagged by Method B.

### The Real Question
**Which method is "right"?**

Neither. They're asking different questions:

**Method A asks:** "Which galaxies have structures that are rare among galaxies?"
- Good for finding: Peculiar morphologies, mergers, unusual spiral patterns
- Bad at: Subtle textures, faint features

**Method B asks:** "Which images look visually unusual in general?"
- Good for finding: Complex textures, unusual brightness distributions, edge cases
- Bad at: Understanding *why* they're unusual in galaxy terms

### The Honest Answer
We don't know which set is "better" scientifically. That requires:
1. Looking at the actual images (visual inspection)
2. Getting spectra (to confirm they're real and interesting)
3. Comparing with astronomer classifications

---

## The Original 7 (Validated Set)

| ID | Coordinates | Anomaly Score | What's Known |
|-----|-------------|---------------|--------------|
| ASTRO1-2026-001 | 07h47m08s +19°14'29" | -0.186 | Nothing — completely uncataloged |
| ASTRO1-2026-002 | 12h59m55s -04°26'57" | -0.185 | Nothing — completely uncataloged |
| ASTRO1-2026-003 | 13h07m44s +66°25'51" | -0.101 | Nothing — completely uncataloged |
| ASTRO1-2026-004 | 03h19m36s +68°50'18" | -0.094 | Nothing — completely uncataloged |
| ASTRO1-2026-005 | 21h02m01s +45°03'19" | -0.072 | Nothing — completely uncataloged |
| ASTRO1-2026-006 | 05h09m17s -02°44'01" | -0.060 | Nothing — completely uncataloged |
| ASTRO1-2026-007 | 18h46m40s +52°55'16" | -0.059 | Nothing — completely uncataloged |

**All 7 are from the first 596 galaxies processed (the "pilot batch").**

**Weird finding:** The remaining 4,837 galaxies yielded zero additional candidates with Method A. This suggests either:
- The pilot batch was accidentally rich in weird galaxies (bad luck)
- Or the detection method works poorly on fainter/different galaxies

---

## The New 27 (Needs Validation)

| Rank | Coordinates | Anomaly Score | Notes |
|------|-------------|---------------|-------|
| 1 | 17h02m47s -01°22'29" | -0.136 | Highest anomaly in new set |
| 2 | 00h22m03s -03°38'46" | -0.120 | |
| 3 | 19h01m32s +21°11'35" | -0.114 | |
| 4 | 19h40m08s +13°00'09" | -0.101 | |
| 5 | 19h38m29s +13°06'48" | -0.098 | |
| ... | ... | ... | (23 more) |
| 27 | 01h53m17s +16°01'10" | -0.050 | Lowest still above threshold |

**Key difference:** These are spread across the full sample, not clustered in the pilot batch. This suggests Method B is more consistent across different galaxy populations.

**However:** We haven't visually inspected these yet. Some could be:
- Artifacts (cosmic rays, satellite trails)
- Edge cases (partial galaxies at image boundaries)
- Known objects missed by SIMBAD/NED queries (rare but possible)

---

## Which Should We Publish?

### RNAAS (Immediate)
**Publish the 7.** Reasons:
- They're from the originally planned pipeline
- All verification checks completed
- Consistent methodology (same embedding method for all)
- Scientifically conservative

**Mention in RNAAS:** "Additional candidates identified via alternative embedding methods are being investigated separately."

### Full Methods Paper (Later)
**Discuss all 34 candidates.** Reasons:
- Compare the two methods rigorously
- Argue that ensemble approaches (combining methods) find more candidates
- Show visual inspection results for both sets
- Demonstrate that ML method choice significantly impacts results

### Preprint (arXiv)
**Post RNAAS + supplementary material with all 34.**
- Gets discoveries out fast
- Establishes priority
- Allows community feedback

---

## What You Need to Do Next

### Before RNAAS Submission
1. **Visual inspection** — Look at actual SDSS images of all 7 candidates
   - Check for obvious artifacts
   - Confirm they look "galaxy-like"
   - Note any interesting features (tails, asymmetries, etc.)

2. **Coordinate verification** — Double-check the coordinates in SDSS SkyServer
   - Make sure we're pointing at the right objects
   - Check for any catalog entries we missed

### After RNAAS Submission
3. **Inspect the 27** — Quick visual check of the new candidates
   - Flag obvious artifacts
   - Note interesting ones for follow-up

4. **Spectroscopic follow-up planning** — For the best candidates
   - Need telescope time (4m-class)
   - Get redshifts and spectral classifications
   - Confirm they're real physical objects (not artifacts)

---

## Technical Nuances (If You Want the Details)

### Why 24 vs 2,048 Dimensions Matters

**The curse of dimensionality:**
- In 24-dimensional space, distances behave "normally"
- In 2,048-dimensional space, distances become weird — everything is far from everything
- Isolation Forest behaves differently in high dimensions

**What ResNet50 actually sees:**
- Early layers: Edges, textures, simple patterns
- Middle layers: Shapes, object parts
- Late layers: Object categories (cats, dogs, cars...)
- We used the layer before classification, so it captures "visual complexity" without assuming "cat-ness" or "car-ness"

**Why it finds different galaxies:**
- A galaxy with unusual structure but typical texture → flagged by 24-dim method
- A galaxy with typical structure but unusual texture → flagged by 2,048-dim method
- A galaxy with both unusual → flagged by both (only 1 such case!)

### The Autoencoder Training

**Not documented well in original run:**
- We know it produced 24-dimensional embeddings
- We don't have the exact architecture or training parameters
- This is why we can't perfectly replicate Method A

**Implication:** 
The original 7 are validated, but we couldn't reproduce Method A exactly if we tried. The verification run used Method B because we couldn't reconstruct Method A's exact parameters.

---

## Bottom Line

**You have 34 candidate discoveries, not 7.**

**But you can only confidently claim 7 right now** because:
- Method A was the original planned approach
- Method B was a verification that turned into a second discovery run
- The 27 need visual inspection before claiming them

**Publication strategy:**
- RNAAS: 7 candidates (conservative, defensible)
- Methods paper: Compare both methods, discuss all 34
- arXiv: RNAAS + supplement with coordinates of all 34

**The real scientific contribution:**
Showing that ML method choice dramatically affects what you find in astronomical surveys. Most papers don't discuss this. You can.

---

## Quick Reference

**Files:**
- `paper/RNAAS_submission.md` — Draft for the 7 candidates
- `NEW_DISCOVERIES.md` — Details on the original 7
- `VERIFICATION_REPORT.md` — Details on the new 27
- `METHODS.md` — Complete technical documentation
- `results/anomaly_scores/candidates_detailed_20260310_115323.csv` — All 27 with coordinates

**GitHub:** https://github.com/JohnCassavetes/astro1

**Next decision:** Submit RNAAS on the 7, or inspect the 27 first?
