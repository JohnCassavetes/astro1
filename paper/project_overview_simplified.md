# Hunting Hidden Galaxy Collisions with AI

**What is this?** A simplified, "no-jargon" overview of what we built, why we built it, and how you can run it.

---

## 🚀 The TL;DR

We built a data pipeline that downloads thousands of images of galaxies, uses an AI vision model to figure out which ones look "weird," and then runs a custom image-scanning script to find galaxies that are crashing into each other. We process massive amounts of space data to give astronomers a highly ranked "hit list" of cool targets to point their telescopes at.

## 🔭 The Problem: Too Much Space

Projects like the Sloan Digital Sky Survey (SDSS) have taken pictures of *millions* of galaxies. Most of them are pretty standard: either fuzzy footballs (ellipticals) or spirally pinwheels (spirals). 

However, the most scientifically interesting galaxies are the ones doing something weird—like crashing into a neighbor (mergers) or getting torn apart. 

**The bottleneck:** Humans can't manually look at millions of images to find the 1% that are doing something weird. We need code to do the heavy lifting and float the best candidates to the top.

## 🛠️ What We Did (The "How")

Our pipeline solves this in four main steps:

### Step 1: Get the Data
We use an API to download raw image cutouts (256x256 pixels) of about 4,700 galaxies from the SDSS database. 

### Step 2: AI Feature Extraction (The "Vibe Check")
How do you teach a computer what "weird" looks like if you don't know what you're looking for? 
We pass every galaxy image through **ResNet50**—a deep learning vision model. Even though ResNet was trained on photos of dogs and cars, its early layers are really good at understanding basic structures (edges, blobs, textures). The AI spits out a list of 2,048 numbers for every galaxy. This list is essentially the mathematical "vibe" or "shape profile" of that image.

### Step 3: Global Anomaly Detection
Now we have 4,700 lists of numbers. We feed these into a machine learning algorithm called an **Isolation Forest**. This algorithm looks at all the number lists and finds the ones that are the most mathematically isolated—the outliers. These are our "Global Anomalies."

### Step 4: The Image Scanner (The Cool Part)
Global anomalies just tell us an image is "weird," but not *why*. 
To find specific phenomena—like galaxies merging—we wrote a custom Python script (`scan_raw_secondary_sources.py`). 
This script operates directly on the image pixels. It isolates the background noise, finds the main bright blob in the center (the primary galaxy), and then scans the immediate surrounding area for a *second* distinct bright blob (a "buddy"). 
If it finds a buddy that is bright enough and close enough, it flags the image as a multi-component system (likely a merger or a galaxy with a huge companion).

## 📊 What We Found

In the past, anomaly detection in astronomy was often framed as "Look! We discovered a brand new object no one has ever seen!" But in reality, almost all bright things have been cataloged somewhere. 

Instead of claiming fake discoveries, we built a highly reliable **Recommendation Engine**. 

Out of 4,700 galaxies, our image scanner successfully flagged **605 galaxies** showing strong evidence of multiple components (buddies). We ranked these 605 candidates and generated overlay images showing exactly where the algorithm spotted the primary and secondary blobs. 

Astronomers can take our top 20 or top 50 ranked list and immediately request telescope time to study these merging systems, saving them hundreds of hours of manual searching.

---

## 💻 How to Run It Yourself

All the magic happens in the `scripts/` folder. If you want to run the pipeline from start to finish, run these scripts in order:

1. **Get the data:**
   ```bash
   python scripts/download_data.py
   ```
2. **Clean and prep the images:**
   ```bash
   python scripts/preprocess_images.py
   ```
3. **Run the AI vision model (ResNet50):**
   ```bash
   python scripts/generate_embeddings.py
   ```
4. **Find the global weirdos (Isolation Forest):**
   ```bash
   python scripts/detect_anomalies.py
   ```
5. **Scan for multi-component galaxies (The Image Scanner):**
   ```bash
   python scripts/scan_raw_secondary_sources.py
   ```

*Note: You can find all the final ranked data and overlay images inside the `results/raw_object_scan/` directory.*
