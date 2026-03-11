# Draft: An Automated Pipeline for Ranking Morphological Anomalies and Detecting Secondary Components in SDSS Galaxies

**Status:** 🚧 Draft v1.0 — METHODOLOGY FOCUS  
**Target:** Astronomy & Computing (A&C) or PASP  
**Word count:** ~2200 words  
**Last Updated:** 2026-03-10

---

## Abstract

We present a computational pipeline designed to systematically rank morphological anomalies and detect secondary luminous components in Sloan Digital Sky Survey (SDSS) galaxies. Moving beyond binary anomaly classification and catalog-dependent "discovery" claims, our approach combines deep feature extraction with image-plane scanning to provide a prioritized candidate list for follow-up observations. The pipeline operates in three stages: (1) extraction of 2,048-dimensional features using a pre-trained ResNet50 model; (2) global morphological anomaly ranking using an Isolation Forest; and (3) a custom image-plane scanning algorithm that robustly identifies secondary luminous components (e.g., merging companions, dual nuclei) within raw SDSS cutouts. Applying this pipeline to 4,690 quality-filtered SDSS DR19 galaxies, we successfully flag 605 multi-component candidates. We release our prioritized candidate catalog and overlay proofs to the community to facilitate targeted spectroscopic follow-up of merging systems and morphologically peculiar galaxies. All code and candidate catalogs are open-source and available at [GitHub Repository URL].

*Keywords:* methods: data analysis — techniques: image processing — galaxies: statistics — catalogs

---

## 1. Introduction

The Sloan Digital Sky Survey (SDSS; York et al. 2000) transformed extragalactic astronomy by providing uniform imaging of millions of galaxies. While the majority of these objects fit standard morphological classifications (e.g., Hubble sequence), rare and peculiar objects—such as ring galaxies, major mergers, and objects with distinct secondary components—offer crucial insights into galaxy evolution, local environment interactions, and extreme astrophysical processes. 

Historically, the detection of such rare objects relied heavily on visual inspection by experts or citizen scientists (e.g., Galaxy Zoo; Lintott et al. 2008). In the era of massive datasets, automated anomaly detection has emerged as a necessary tool. Unsupervised machine learning methods can isolate objects that deviate from the normative distribution of the dataset (e.g., Walmsley et al. 2022; Lochko et al. 2021). However, raw anomaly detection frequently struggles with high false-positive rates, flagging imaging artifacts or selecting objects that, while statistically rare, are fundamentally uninteresting or already well-cataloged.

Furthermore, framing anomaly detection solely as an engine for "new discoveries" is fraught. Absence from specific astronomical databases (like SIMBAD or NED) is difficult to prove conclusively and is often an artifact of search radius or naming conventions rather than true novelty. 

In this work, we pivot from the binary classification of "discovery" to a methodology focused on **candidate ranking and component scanning**. We present an automated, reproducible pipeline that not only identifies global morphological outliers using deep feature extraction but also explicitly scans raw image cutouts for secondary luminous components. This approach is highly effective for identifying merging systems, close companions, and structurally complex objects. We provide the resulting prioritized catalog as a resource for the community.

---

## 2. Data

### 2.1 SDSS Sample Selection

We utilize imaging data from SDSS Data Release 19 (DR19). Our initial query prioritized well-covered regions and applied basic photometric cuts to select a sample of distinct, extended sources:
- $r$-band Petrosian magnitude: $15 < m_r < 21$
- Petrosian half-light radius: $R_{50, r} > 2$ arcsec

This process yielded an initial sample of thousands of raw $g, r, i$-band FITS cutouts ($30'' \times 30''$, scale $0.396''$/pixel).

### 2.2 Image Preprocessing

To utilize pre-trained deep learning models and our image-plane scanner, we convert the FITS data into normalized, scale-uniform representations. Color composites are generated following the optimal arcsinh scaling principles outlined by Lupton et al. (2004). The images are resized to $256 \times 256$ pixels. 

Crucially, our pipeline implements a stringent quality screening step prior to analysis. Images containing extensive masked regions, severe edge artifacts, or saturated bleed trails are discarded, ensuring the downstream algorithms process robust morphological data. After filtering, the working dataset comprises **4,690 valid galaxy cutouts**.

---

## 3. Methodology

Our pipeline consists of two complementary branches: a global morphological anomaly ranker (based on deep feature embeddings) and a deterministic, image-plane scanner designed specifically to detect secondary components.

### 3.1 Global Anomaly Ranking via Deep Embeddings

To capture the complex morphological structure of galaxies, we utilize a convolutional neural network (CNN) for feature extraction. We employ a ResNet50 architecture (He et al. 2016), pre-trained on the ImageNet dataset. While not trained on astronomical data, the early layers of ResNet50 are highly effective at capturing generic textural and structural motifs (edges, gradients, color boundaries), which translate well to broad morphological characterization.

For each preprocessed $256 \times 256$ image, we extract the activations from the final global average pooling layer, producing a dense vector of 2,048 features.

These 2,048-dimensional embeddings serve as the input space for an **Isolation Forest** (Liu et al. 2008) anomaly detection algorithm. Isolation Forests are particularly well-suited for high-dimensional, unsupervised outlier detection. They isolate anomalous data points by randomly selecting features and split values; outliers, being sparser in the feature space, require fewer splits to be isolated. We configure the forest with 100 estimators and derive a global continuous anomaly score for every object in the catalog.

### 3.2 Raw Scanning for Secondary Components

While the ResNet50 + Isolation Forest approach ranks global morphological unusualness, it is treated as a "black box" and does not interpret *why* an object is anomalous. To complement this, we developed a deterministic, image-plane scanning algorithm (`scan_raw_secondary_sources.py`) that operates directly on the grayscale representations of the cutouts.

The goal of this scanner is to explicitly answer: *Does this cutout contain a single dominant source, or are there multiple resolved, luminous components?*

The algorithm proceeds as follows:

1.  **Robust Background Estimation:** Edge pixels (the outer 20 pixels of the image) are extracted to compute a resistant background median and an absolute deviation-based scatter ($\sigma$).
2.  **Smoothing and Thresholding:** The image is smoothed via a Gaussian filter ($\sigma=2.0$ pixels) to suppress noise. We apply a strict threshold at $+7.0\sigma$ above the background.
3.  **Component Extraction:** Contiguous regions above the threshold undergo binary opening and closing to separate narrow bridges and fill small holes. We label all discrete connected components. Components with an area of fewer than 60 pixels are discarded to avoid high-frequency noise.
4.  **Primary Identification:** The primary object is identified as the most luminous component located within a central search radius ($R < 64$ pixels from the image center).
5.  **Secondary Flagging:** Secondary components are accepted if they meet the following criteria:
    *   Separation from the primary centroid: $15 < d < 70$ pixels.
    *   Flux ratio: The integrated flux of the secondary must be at least 15% ($f_{\text{ratio}} \ge 0.15$) of the primary component's flux.

Finally, an Isolation Forest evaluates features derived specifically from this image-plane scan (total components, secondary count, brightest secondary flux ratio, farthest secondary distance, and rotational asymmetry) to compute a targeted `secondary_object_score`.

---

## 4. Results

### 4.1 Output of the Raw Object Scan

Applying the `scan_raw_secondary_sources.py` algorithm to the 4,690 valid cutouts yielded highly structured results. The algorithm successfully identified multiple luminous components in a significant fraction of the data, filtering out single, isolated ellipticals or standard spirals.

*   **Valid JPGs scanned:** 4,690
*   **Flagged multi-component candidates:** 605

The scanner effectively flags close companions, dual-nucleus candidates, and late-stage mergers where tidal bridges might fall below the $7.0\sigma$ threshold while the distinct cores remain visible.

### 4.2 Candidate Ranking

Table 1 presents the top candidates ranked by their `secondary_object_score`. These objects represent the most extreme multi-component systems identified by the pipeline.

**Table 1. Top High-Scoring Secondary Component Candidates**

| ObjID | RA | Dec | Secondary Count | Max Flux Ratio | Scan Score |
|-------|----|-----|-----------------|----------------|------------|
| 12376400000000006791 | 305.5417 | 8.2974 | 7 | 1.509 | 0.7743 |
| 12376400000000001618 | 173.2024 | 43.3572 | 6 | 7.328 | 0.7675 |
| 12376400000000000518 | 5.5122 | -3.6462 | 6 | 1.526 | 0.7574 |
| 12376400000000000578 | 316.3732 | -2.7793 | 6 | 0.642 | 0.7156 |
| 12376400000000006823 | 302.0423 | 12.5660 | 5 | 0.428 | 0.7676 |

*(Note: Data subset shown. The full catalog of ranked candidates is available in the supplementary material.)*

### 4.3 Diagnostic Overlays

To validate the deterministic scanner, the pipeline automatically generates bounding box overlays for the highest-scoring candidates. These overlays (available in the repository) visually confirm the pipeline's ability to distinguish the primary central target from nearby, distinct luminous sources (e.g., companion galaxies or bright star-forming knots mimicking dual nuclei) that survive the strict thresholding and separation criteria.

---

## 5. Discussion

Our methodology highlights the advantage of pairing deep, black-box embedding spaces with deterministic, interpretable image-plane scans. 

While the ResNet50 + Isolation Forest branch identifies objects that "look weird" structurally, the secondary component scanner specifically targets physical interaction indicators. By defining strict thresholds (minimum 15% flux ratio, separation bounds), the scanner minimizes flagging foreground stars or faint background galaxies, focusing instead on substantial companion structures likely to be physically associated or part of a merging system segment.

Crucially, by framing this effort as a **candidate generation pipeline** rather than a claim of definitive discovery, we alleviate the burden of exhaustive, potentially incomplete cross-matching against historical databases. SDSS `objid` entries are, by definition, survey-detected objects; proving they are entirely absent from the literature is difficult. Instead, providing a rigorously ranked subset of 605 multi-component objects out of ~4,700 allows observational astronomers to prioritize targets for integral field spectroscopy (IFS) or high-resolution follow-up imaging without having to manually sift through the larger survey footprint.

---

## 6. Conclusion

We have presented a robust, automated pipeline for processing SDSS imaging data to rank morphological anomalies and detect secondary luminous components. 

1. We extracted 2,048-dimensional features and derived global anomaly scores for 4,690 quality-filtered SDSS galaxies.
2. We deployed a custom image-plane algorithm that successfully flagged 605 targets demonstrating strong evidence of multiple luminous components (e.g., mergers, close companions).
3. We release the fully ranked candidate lists, along with diagnostic overlays and the open-source pipeline code.

This methodology provides a scalable framework to prepare target lists for future facilities and large-scale spectroscopic surveys, turning vast archival datasets into prioritized, actionable candidate sets.

## Data Availability

Raw imaging data are available via the Sloan Digital Sky Survey (https://www.sdss.org). The full processing pipeline, resulting candidate catalogs (`raw_object_scan.csv`), and generated diagnostic figures are available at [GitHub Repository URL].

## Acknowledgments
*To be added: SDSS standard acknowledgment text.*
