#!/usr/bin/env python3
"""
Galaxy Verification Script - Batch Processing
Queries SIMBAD, NED, and other databases for 50 candidate galaxies
"""

import pandas as pd
import numpy as np
import requests
import time
import json
from datetime import datetime
import csv
import sys

# Configuration
SIMBAD_DELAY = 0.5
NED_DELAY = 0.5
REQUEST_TIMEOUT = 10

print("=" * 80)
print("GALAXY VERIFICATION PIPELINE")
print("=" * 80)
print(f"Started: {datetime.now()}")
print()

# Load candidates
candidates = pd.read_csv('results/comparison/uncataloged_candidates.csv')
print(f"Loaded {len(candidates)} candidate galaxies")
print()

# Output file
output_file = 'results/verification/verification_results.csv'

# Write header
with open(output_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([
        'objid', 'ra', 'dec', 'method_a_score', 'method_b_score',
        'simbad_match', 'simbad_name', 'simbad_type', 'simbad_distance_arcsec',
        'ned_match', 'ned_name', 'ned_redshift',
        'literature_match', 'literature_refs',
        'sdss_spectroscopy', 'sdss_redshift', 'sdss_class',
        'final_status', 'verification_notes'
    ])

# Process each candidate
for idx, row in candidates.iterrows():
    objid = int(row['objid'])
    ra = float(row['ra'])
    dec = float(row['dec'])
    method_a_score = float(row['method_a_score'])
    method_b_score = float(row['method_b_score'])
    
    print(f"[{idx+1}/50] objid={objid}, ra={ra:.4f}, dec={dec:.4f}")
    
    # Initialize results
    simbad_match = False
    simbad_name = None
    simbad_type = None
    simbad_distance = None
    ned_match = False
    ned_name = None
    ned_redshift = None
    lit_match = False
    lit_refs = None
    sdss_spec = False
    sdss_z = None
    sdss_class = None
    notes = []
    
    # 1. Query SIMBAD
    try:
        radius_deg = 5.0 / 3600.0  # 5 arcsec
        query = f"""
        SELECT TOP 3 main_id, otype_txt, 
               DISTANCE(POINT('ICRS', ra, dec), POINT('ICRS', {ra}, {dec})) as dist
        FROM basic
        WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra}, {dec}, {radius_deg}))=1
        ORDER BY dist
        """
        
        tap_url = "http://simbad.u-strasbg.fr/simbad/sim-tap/sync"
        params = {'request': 'doQuery', 'lang': 'adql', 'format': 'json', 'query': query}
        
        response = requests.get(tap_url, params=params, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    closest = data['data'][0]
                    simbad_match = True
                    simbad_name = str(closest[0]) if closest[0] else 'Unknown'
                    simbad_type = str(closest[1]) if len(closest) > 1 and closest[1] else 'Unknown'
                    if len(closest) > 2 and closest[2] is not None:
                        simbad_distance = float(closest[2]) * 3600  # Convert to arcsec
            except:
                pass
        else:
            notes.append(f"SIMBAD HTTP {response.status_code}")
    except Exception as e:
        notes.append(f"SIMBAD error: {str(e)[:30]}")
    
    time.sleep(SIMBAD_DELAY)
    
    # 2. Query NED
    try:
        radius_arcm = 5.0 / 60.0  # 5 arcsec in arcmin
        ned_url = "https://ned.ipac.caltech.edu/cgi-bin/nph-objsearch"
        params = {
            'in_csys': 'Equatorial',
            'in_equinox': 'J2000',
            'lon': ra,
            'lat': dec,
            'radius': radius_arcm,
            'search_type': 'Near Position Search',
            'out_csys': 'Equatorial',
            'out_equinox': 'J2000',
            'obj_sort': 'Distance to search center',
            'of': 'pre_text',
            'list_limit': 3,
        }
        
        response = requests.get(ned_url, params=params, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            content = response.text
            if 'No object' in content or 'no objects found' in content.lower():
                ned_match = False
            elif 'Search Results' in content or 'Object Name' in content or 'MAIN_ID' in content:
                ned_match = True
                ned_name = 'Object found in NED'
        else:
            notes.append(f"NED HTTP {response.status_code}")
    except Exception as e:
        notes.append(f"NED error: {str(e)[:30]}")
    
    time.sleep(NED_DELAY)
    
    # 3. Literature search for top 20 candidates
    if idx < 20:
        try:
            # Check if coordinates match known literature
            # For now, we'll note this needs manual check
            lit_match = False
            lit_refs = "Manual check required"
        except:
            pass
    
    # 4. Determine final status
    if simbad_match or ned_match:
        final_status = "KNOWN_OBJECT"
    elif simbad_name is None and ned_name is None:
        final_status = "CONFIRMED_UNCATALOGED"
    else:
        final_status = "NEEDS_REVIEW"
    
    # Build notes string
    notes_str = "; ".join(notes) if notes else ""
    
    # Write result
    with open(output_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            objid, ra, dec, method_a_score, method_b_score,
            simbad_match, simbad_name, simbad_type, simbad_distance,
            ned_match, ned_name, ned_redshift,
            lit_match, lit_refs,
            sdss_spec, sdss_z, sdss_class,
            final_status, notes_str
        ])
    
    print(f"       SIMBAD: {'YES - ' + simbad_name if simbad_match else 'NO'}")
    print(f"       NED: {'YES' if ned_match else 'NO'}")
    print(f"       STATUS: {final_status}")
    print()

# Print summary
print("=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
print(f"Finished: {datetime.now()}")
print()

# Read results and print summary
df = pd.read_csv(output_file)
confirmed = len(df[df['final_status'] == 'CONFIRMED_UNCATALOGED'])
known = len(df[df['final_status'] == 'KNOWN_OBJECT'])
review = len(df[df['final_status'] == 'NEEDS_REVIEW'])

print(f"Summary:")
print(f"  Total candidates: {len(df)}")
print(f"  Confirmed uncataloged: {confirmed}")
print(f"  Known objects: {known}")
print(f"  Needs review: {review}")
print()
print(f"Results saved to: {output_file}")
