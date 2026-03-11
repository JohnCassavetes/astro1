.PHONY: all data preprocess embed anomaly scan stats figures clean

all: data preprocess embed anomaly scan stats figures

data:
	python scripts/download_data.py --n 5000

preprocess:
	python scripts/preprocess_images.py

embed:
	python scripts/generate_embeddings.py

anomaly:
	python scripts/detect_anomalies.py

scan:
	python scripts/scan_raw_secondary_sources.py

stats:
	python scripts/compute_scan_stats.py

figures:
	python scripts/make_paper_figures.py

clean:
	rm -rf logs/*
	rm -rf data/raw/*
	rm -rf data/processed/*
	rm -rf results/intermediate/*
