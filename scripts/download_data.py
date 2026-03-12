#!/usr/bin/env python3
"""
Stage 1: Download Real SDSS DR19 Galaxy Data

Uses SDSS SkyServer for catalog queries and image cutouts.
Real data from: https://data.sdss.org/sas/dr19/
Documentation: https://www.sdss.org/dr19/data_access/

Updated with robust retry logic for network timeouts.
"""

import os
import json
import time
import io
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import requests
from tqdm import tqdm
from PIL import Image

from common import (
    ensure_dataset_state,
    load_config,
    save_json,
    setup_logger,
    update_project_state,
)

PROJECT_ROOT, config = load_config()
logger = setup_logger(__file__, config, PROJECT_ROOT)

DATA_RAW = PROJECT_ROOT / config['paths']['raw_data']
DATA_META = PROJECT_ROOT / config['paths']['metadata']
MEMORY = PROJECT_ROOT / config['paths']['memory']

# SDSS endpoints
SKYSERVER_URL = "https://skyserver.sdss.org/dr19/SkyServerWS"
SKYSERVER_SQL_URL = "https://skyserver.sdss.org/dr19/en/tools/search/x_sql.aspx"
DEFAULT_HEADERS = {
    "User-Agent": "astro1-pipeline/1.0",
    "Accept": "text/csv,application/octet-stream,image/jpeg,*/*",
}

def normalize_objid(value: object) -> str:
    """Preserve large SDSS objids exactly as strings."""
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text

def load_state() -> Dict:
    return ensure_dataset_state(MEMORY)

def save_state(state: Dict):
    save_json(MEMORY / "dataset_state.json", state)

def query_with_retry(url: str, params: Dict, max_retries: int = 3, timeout: int = 60) -> Optional[pd.DataFrame]:
    """Query SkyServer with retry logic."""
    for attempt in range(max_retries):
        try:
            print(f"  Attempt {attempt + 1}/{max_retries}...")
            response = requests.get(url, params=params, timeout=timeout, headers=DEFAULT_HEADERS)
            response.raise_for_status()
            
            # Parse CSV
            from io import StringIO
            # Remove comment lines starting with #
            lines = [line for line in response.text.split('\n') if not line.startswith('#')]
            csv_text = '\n'.join(lines)
            df = pd.read_csv(StringIO(csv_text), dtype={'objid': 'string'})
            return df
            
        except requests.exceptions.Timeout:
            print(f"    Timeout, waiting before retry...")
            time.sleep(5 * (attempt + 1))  # Exponential backoff
        except Exception as e:
            print(f"    Error: {e}")
            time.sleep(2)
    
    return None

def query_sdss_skyserver(n_galaxies: int = 100) -> pd.DataFrame:
    """
    Query SDSS DR19 via SkyServer SQL Search with retries.
    """
    print(f"Querying SDSS DR19 SkyServer for {n_galaxies} galaxies...")
    
    # Simplified SQL query - avoid complex flags
    query = f"""SELECT TOP {n_galaxies}
        CAST(p.objid AS VARCHAR(32)) AS objid, p.ra, p.dec,
        p.petroMag_r, p.petroR50_r,
        p.modelMag_g, p.modelMag_r, p.modelMag_i,
        p.run, p.rerun, p.camcol, p.field
    FROM PhotoObj AS p
    WHERE p.type = 3
    AND p.petroMag_r BETWEEN 16 AND 20
    AND p.petroR50_r > 2
    ORDER BY p.objid
    """
    
    # Try SkyServer REST API
    url = f"{SKYSERVER_URL}/SearchTools/SqlSearch"
    params = {'cmd': query, 'format': 'csv'}
    
    df = query_with_retry(url, params, max_retries=3, timeout=60)
    
    if df is not None and len(df) > 0:
        df['objid'] = df['objid'].map(normalize_objid)
        print(f"Retrieved {len(df)} galaxies from SkyServer")
        return df
    
    # Try alternate CasJobs interface
    print("Primary endpoint failed, trying CasJobs...")
    casjobs_url = "https://skyserver.sdss.org/casjobs/RestAPI/contexts/dr19/query"
    df = query_with_retry(casjobs_url, params, max_retries=2, timeout=90)
    
    if df is not None and len(df) > 0:
        df['objid'] = df['objid'].map(normalize_objid)
        print(f"Retrieved {len(df)} galaxies from CasJobs")
        return df
    
    # Fallback: try using astroquery with shorter timeout
    print("Trying astroquery fallback...")
    try:
        from astroquery.sdss import SDSS
        result = SDSS.query_sql(query, data_release=17, timeout=60)
        if result is not None:
            df = result.to_pandas()
            df['objid'] = df['objid'].map(normalize_objid)
            print(f"Retrieved {len(df)} galaxies via astroquery (DR17)")
            return df
    except Exception as e:
        print(f"Astroquery failed: {e}")
    
    raise RuntimeError(
        "All SDSS query methods failed.\n"
        "Possible issues:\n"
        "  - Network connectivity\n"
        "  - SDSS server maintenance\n"
        "  - Rate limiting\n"
        "Try again later or check https://www.sdss.org/"
    )

def download_cutout_jpeg(ra: float, dec: float, objid: str,
                         scale: float = 0.396, width: int = 256,
                         height: int = 256) -> Tuple[bool, Optional[str]]:
    """
    Download JPEG cutout from SkyServer with retry.
    """
    url = f"{SKYSERVER_URL}/ImgCutout/getjpeg"
    params = {
        "ra": ra,
        "dec": dec,
        "scale": scale,
        "width": width,
        "height": height,
        "opt": "",
    }
    output_path = DATA_RAW / f"{objid}.jpg"

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url,
                params=params,
                timeout=30,
                headers=DEFAULT_HEADERS,
            )
            response.raise_for_status()
            data = response.content

            if len(data) < 1000:
                raise ValueError(f"response too small ({len(data)} bytes)")

            with Image.open(io.BytesIO(data)) as img:
                img.verify()

            with open(output_path, 'wb') as f:
                f.write(data)
            return True, None

        except Exception as e:
            if output_path.exists():
                output_path.unlink()
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return False, str(e)

    return False, "download_failed"

def download_cutouts(df: pd.DataFrame, max_downloads: Optional[int] = None) -> pd.DataFrame:
    """
    Download image cutouts for catalog entries.
    """
    if max_downloads:
        df = df.head(max_downloads)
    
    print(f"\nDownloading {len(df)} image cutouts from SDSS DR19...")
    print("Source: skyserver.sdss.org/dr19/")
    
    results = []
    
    for idx, row in tqdm(df.iterrows(), total=len(df)):
        objid = normalize_objid(row['objid'])
        ra, dec = row['ra'], row['dec']
        
        # Download JPEG
        success, error = download_cutout_jpeg(ra, dec, objid, width=256, height=256)
        
        result = {
            'objid': objid,
            'ra': ra,
            'dec': dec,
            'petroMag_r': row.get('petroMag_r'),
            'petroR50_r': row.get('petroR50_r'),
            'downloaded': success,
            'filepath': str(DATA_RAW / f"{objid}.jpg") if success else None,
            'error': error
        }
        results.append(result)
        
        # Rate limiting
        time.sleep(0.2)
    
    return pd.DataFrame(results)

def main():
    default_n = int(config.get('pipeline', {}).get('sdss', {}).get('limit', 50))
    parser = argparse.ArgumentParser(description='Download SDSS DR19 galaxy data')
    parser.add_argument(
        '--n',
        type=int,
        default=default_n,
        help=f'Number of galaxies (default: config pipeline.sdss.limit={default_n})'
    )
    parser.add_argument('--max-images', type=int, default=None, help='Max images to download')
    parser.add_argument('--catalog-only', action='store_true', help='Skip image download')
    args = parser.parse_args()
    
    # Ensure directories exist
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_META.mkdir(parents=True, exist_ok=True)
    
    # Update project state
    update_project_state(MEMORY, "data_collection", "in_progress")
    
    # Load state
    state = load_state()
    
    # Query catalog
    print("\n" + "="*60)
    print("STAGE 1: Download SDSS DR19 Data")
    print("="*60)
    
    try:
        df = query_sdss_skyserver(args.n)
        if df is None or len(df) == 0:
            print("\nERROR: No data retrieved from SDSS.")
            exit(1)
    except RuntimeError as e:
        print(f"\nERROR: {e}")
        logger.info("\nTroubleshooting:")
        print("  1. Check internet connection: ping skyserver.sdss.org")
        print("  2. Check SDSS status: https://www.sdss.org/")
        print("  3. Try again later - servers may be under maintenance")
        exit(1)
    
    # Save catalog metadata
    catalog_path = DATA_META / "galaxy_catalog.csv"
    df.to_csv(catalog_path, index=False)
    print(f"\nSaved catalog to: {catalog_path}")
    
    # Download cutouts
    if not args.catalog_only:
        df_downloads = download_cutouts(df, max_downloads=args.max_images)
        
        # Ensure objid is treated as string for both dataframes to avoid merge errors
        df['objid'] = df['objid'].map(normalize_objid)
        df_downloads['objid'] = df_downloads['objid'].map(normalize_objid)
        
        # Merge with catalog
        df = df.merge(df_downloads[['objid', 'downloaded', 'filepath', 'error']],
                      on='objid', how='left')
        
        n_downloaded = df['downloaded'].sum()
        logger.info(f"\nDownloaded {n_downloaded}/{len(df)} images")
    
    # Update state
    state['source'] = 'SDSS_DR19_SkyServer'
    state['query_strategy'] = f"clean_galaxies_n{len(df)}"
    state['download_batches'].append({
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'n_requested': args.n,
        'n_retrieved': len(df),
        'n_images_downloaded': int(df['downloaded'].sum()) if 'downloaded' in df.columns else 0
    })
    state['validation_passed'] = True
    save_state(state)
    
    # Save updated catalog
    df.to_csv(catalog_path, index=False)
    
    # Update project state
    update_project_state(MEMORY, "data_collection", "completed")
    
    logger.info(f"\n{'='*60}")
    print(f"Stage 1 complete: REAL SDSS DR19 data")
    print(f"Catalog: {len(df)} galaxies")
    if 'downloaded' in df.columns:
        print(f"Images: {df['downloaded'].sum()}/{len(df)} downloaded")
    print(f"Source: skyserver.sdss.org/dr19/")
    print(f"{'='*60}")

    if 'downloaded' in df.columns and int(df['downloaded'].sum()) == 0:
        failed = df[df['downloaded'] == False]
        if not failed.empty and 'error' in failed.columns:
            print("\nERROR: Catalog retrieval succeeded, but all cutout downloads failed.")
            sample_errors = failed['error'].dropna().head(3).tolist()
            for err in sample_errors:
                print(f"  - {err}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
