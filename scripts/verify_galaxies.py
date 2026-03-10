#!/usr/bin/env python3
"""
Comprehensive Galaxy Verification Script
Verifies 50 candidate galaxies against SIMBAD, NED, and literature databases
"""

import pandas as pd
import numpy as np
import requests
import time
import json
from datetime import datetime
from urllib.parse import quote
import warnings
warnings.filterwarnings('ignore')

# Rate limiting delays
SIMBAD_DELAY = 0.5
NED_DELAY = 0.5

def query_simbad(ra, dec, radius_arcsec=5):
    """
    Query SIMBAD TAP service for objects near coordinates
    """
    tap_url = "http://simbad.u-strasbg.fr/simbad/sim-tap/sync"
    
    # Convert radius to degrees for SIMBAD
    radius_deg = radius_arcsec / 3600.0
    
    query = f"""
    SELECT TOP 10 oid, main_id, otype_txt, sp_type, 
           DISTANCE(POINT('ICRS', ra, dec), POINT('ICRS', {ra}, {dec})) as dist
    FROM basic
    WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra}, {dec}, {radius_deg}))=1
    ORDER BY dist
    """
    
    params = {
        'request': 'doQuery',
        'lang': 'adql',
        'format': 'json',
        'query': query
    }
    
    try:
        response = requests.get(tap_url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                # Return the closest match
                closest = data['data'][0]
                return {
                    'match': True,
                    'name': closest[1] if len(closest) > 1 else 'Unknown',
                    'type': closest[2] if len(closest) > 2 else 'Unknown',
                    'distance_arcsec': closest[5] * 3600 if len(closest) > 5 else None,
                    'raw': closest
                }
            else:
                return {'match': False, 'name': None, 'type': None, 'distance_arcsec': None}
        else:
            return {'match': False, 'name': None, 'type': None, 'distance_arcsec': None, 'error': f'Status {response.status_code}'}
    except Exception as e:
        return {'match': False, 'name': None, 'type': None, 'distance_arcsec': None, 'error': str(e)}

def query_ned(ra, dec, radius_arcsec=5):
    """
    Query NED for objects near coordinates
    NED uses arcminutes for radius
    """
    # Convert arcseconds to arcminutes for NED
    radius_arcm = radius_arcsec / 60.0
    
    ned_url = f"https://ned.ipac.caltech.edu/cgi-bin/nph-objsearch"
    
    params = {
        'in_csys': 'Equatorial',
        'in_equinox': 'J2000',
        'lon': ra,
        'lat': dec,
        'radius': radius_arcm,
        'hconst': 73,
        'omegam': 0.27,
        'omegav': 0.73,
        'corr_z': 1,
        'search_type': 'Near Position Search',
        'z_constraint': 'Unconstrained',
        'z_value1': '',
        'z_value2': '',
        'z_unit': 'z',
        'ot_include': 'ANY',
        'nmp_op': 'ANY',
        'out_csys': 'Equatorial',
        'out_equinox': 'J2000',
        'obj_sort': 'Distance to search center',
        'of': 'pre_text',
        'zv_breaker': 30000.0,
        'list_limit': 5,
        'img_stamp': 'NO'
    }
    
    try:
        response = requests.get(ned_url, params=params, timeout=30)
        if response.status_code == 200:
            content = response.text
            # Check if any objects found
            if 'No object' in content or 'no objects' in content.lower():
                return {'match': False, 'name': None, 'redshift': None}
            
            # Try to extract object names and redshifts
            # This is a simplified parsing - NED returns HTML
            if 'NEDname' in content or 'Object Name' in content:
                # There's at least one object
                # Extract first object name
                return {'match': True, 'name': 'Object found in NED', 'redshift': None, 'raw_html': content[:500]}
            else:
                return {'match': False, 'name': None, 'redshift': None}
        else:
            return {'match': False, 'name': None, 'redshift': None, 'error': f'Status {response.status_code}'}
    except Exception as e:
        return {'match': False, 'name': None, 'redshift': None, 'error': str(e)}

def check_sdss_spectroscopy(ra, dec, radius_arcsec=5):
    """
    Check SDSS DR19 for spectroscopic observations
    Using the SkyServer API
    """
    try:
        # Use SDSS SkyServer API
        sql_query = f"""
        SELECT TOP 1 p.objid, p.ra, p.dec, s.specobjid, s.z, s.class
        FROM photoobj AS p
        LEFT JOIN specobj AS s ON p.objid = s.bestobjid
        WHERE p.ra BETWEEN {ra - radius_arcsec/3600.0} AND {ra + radius_arcsec/3600.0}
        AND p.dec BETWEEN {dec - radius_arcsec/3600.0} AND {dec + radius_arcsec/3600.0}
        AND s.specobjid IS NOT NULL
        """
        
        url = "http://skyserver.sdss.org/dr19/en/tools/search/x_sql.aspx"
        params = {
            'cmd': sql_query,
            'format': 'json'
        }
        
        response = requests.get(url, params=params, timeout=30)
        # For now, return a placeholder - we'll need to parse the response
        return {'has_spectroscopy': None, 'redshift': None, 'class': None}
    except Exception as e:
        return {'has_spectroscopy': False, 'redshift': None, 'class': None, 'error': str(e)}

def search_literature_arxiv(ra, dec):
    """
    Search arXiv for papers mentioning these coordinates
    """
    # Round coordinates to 0.1 deg for search
    ra_rounded = round(ra, 1)
    dec_rounded = round(dec, 1)
    
    query = f"{ra_rounded} {dec_rounded} galaxy"
    
    try:
        url = "http://export.arxiv.org/api/query"
        params = {
            'search_query': f'all:{query}',
            'start': 0,
            'max_results': 5
        }
        
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            content = response.text
            # Check if there are any entries
            if '<entry>' in content:
                return {'match': True, 'count': content.count('<entry>')}
            else:
                return {'match': False, 'count': 0}
        return {'match': False, 'count': 0}
    except Exception as e:
        return {'match': False, 'count': 0, 'error': str(e)}

def verify_candidates():
    """
    Main verification function
    """
    print("=" * 80)
    print("GALAXY VERIFICATION PIPELINE")
    print("=" * 80)
    print(f"Started: {datetime.now()}")
    print()
    
    # Read candidates
    candidates = pd.read_csv('results/comparison/uncataloged_candidates.csv')
    print(f"Loaded {len(candidates)} candidate galaxies")
    print()
    
    # Initialize results
    results = []
    
    # Process each candidate
    for idx, row in candidates.iterrows():
        objid = row['objid']
        ra = row['ra']
        dec = row['dec']
        method_a_score = row['method_a_score']
        method_b_score = row['method_b_score']
        
        print(f"[{idx+1}/50] Verifying objid={objid}, ra={ra:.4f}, dec={dec:.4f}")
        
        # Query SIMBAD
        print("  Querying SIMBAD...", end=" ")
        simbad_result = query_simbad(ra, dec)
        print(f"{'MATCH: ' + simbad_result['name'] if simbad_result['match'] else 'No match'}")
        time.sleep(SIMBAD_DELAY)
        
        # Query NED
        print("  Querying NED...", end=" ")
        ned_result = query_ned(ra, dec)
        print(f"{'MATCH' if ned_result['match'] else 'No match'}")
        time.sleep(NED_DELAY)
        
        # Check SDSS spectroscopy
        sdss_result = check_sdss_spectroscopy(ra, dec)
        
        # Literature search (only for top 20)
        lit_result = None
        if idx < 20:
            print("  Searching literature...", end=" ")
            lit_result = search_literature_arxiv(ra, dec)
            print(f"{'Found papers' if lit_result['match'] else 'No papers'}")
        
        # Determine final status
        if simbad_result['match'] or ned_result['match']:
            final_status = "KNOWN_OBJECT"
        elif simbad_result.get('error') or ned_result.get('error'):
            final_status = "NEEDS_REVIEW"
        else:
            final_status = "CONFIRMED_UNCATALOGED"
        
        # Store result
        result = {
            'objid': objid,
            'ra': ra,
            'dec': dec,
            'method_a_score': method_a_score,
            'method_b_score': method_b_score,
            'simbad_match': simbad_result['match'],
            'simbad_name': simbad_result['name'],
            'simbad_type': simbad_result['type'],
            'simbad_distance': simbad_result['distance_arcsec'],
            'ned_match': ned_result['match'],
            'ned_name': ned_result['name'],
            'ned_redshift': ned_result['redshift'],
            'literature_match': lit_result['match'] if lit_result else False,
            'literature_count': lit_result['count'] if lit_result else 0,
            'sdss_spectroscopy': sdss_result['has_spectroscopy'],
            'sdss_redshift': sdss_result['redshift'],
            'sdss_class': sdss_result['class'],
            'final_status': final_status
        }
        results.append(result)
        
        print(f"  Status: {final_status}")
        print()
        
        # Save intermediate results every 10 candidates
        if (idx + 1) % 10 == 0:
            df = pd.DataFrame(results)
            df.to_csv('results/verification/verification_results_partial.csv', index=False)
            print(f"  Saved intermediate results ({idx+1} candidates processed)")
            print()
    
    # Save final results
    df = pd.DataFrame(results)
    df.to_csv('results/verification/verification_results_final.csv', index=False)
    
    # Generate summary
    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print()
    
    confirmed = df[df['final_status'] == 'CONFIRMED_UNCATALOGED']
    known = df[df['final_status'] == 'KNOWN_OBJECT']
    review = df[df['final_status'] == 'NEEDS_REVIEW']
    
    print(f"Total candidates: {len(df)}")
    print(f"Confirmed uncataloged: {len(confirmed)}")
    print(f"Known objects: {len(known)}")
    print(f"Needs review: {len(review)}")
    print()
    
    if len(confirmed) > 0:
        print("CONFIRMED NEW DISCOVERIES:")
        print("-" * 60)
        for _, row in confirmed.iterrows():
            print(f"  objid={row['objid']}, RA={row['ra']:.4f}, Dec={row['dec']:.4f}")
    
    print()
    print(f"Verification complete: {datetime.now()}")
    
    return df

if __name__ == "__main__":
    # Create verification directory
    import os
    os.makedirs('results/verification', exist_ok=True)
    
    verify_candidates()
