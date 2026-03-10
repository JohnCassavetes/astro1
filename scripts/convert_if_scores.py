#!/usr/bin/env python3
"""Convert existing Isolation Forest CSV results to JSON format"""
import pandas as pd
import json
from pathlib import Path

ROOT = Path("~/Desktop/astro1").expanduser()

# Load CSV
df = pd.read_csv(ROOT / "results" / "anomaly_scores" / "anomaly_scores.csv")

# Convert to JSON format matching the VAE structure
results = []
for _, row in df.iterrows():
    results.append({
        'objid': str(int(row['objid'])),
        'anomaly_score': float(row['anomaly_score']),
        'is_anomaly': bool(row['is_anomaly'])
    })

# Sort by anomaly score
results.sort(key=lambda x: x['anomaly_score'], reverse=True)

# Calculate threshold
threshold = df['anomaly_score'].quantile(0.95)

output = {
    'method': 'isolation_forest',
    'threshold': float(threshold),
    'total_galaxies': len(results),
    'anomalies_detected': int(df['is_anomaly'].sum()),
    'results': results
}

with open(ROOT / "results" / "anomaly_scores" / "isolation_forest_scores.json", 'w') as f:
    json.dump(output, f, indent=2)

print(f"Converted {len(results)} records to JSON")
print(f"Anomalies detected: {output['anomalies_detected']}")
