#!/usr/bin/env python3
"""
Ensemble Consensus for Galaxy Anomaly Detection
Combines multiple detection methods for robust anomaly identification.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict

def load_detection_results(results_dir):
    """Load results from multiple detection methods"""
    results_dir = Path(results_dir)
    
    methods = {}
    
    # Load Isolation Forest results
    if_path = results_dir / "anomaly_scores" / "isolation_forest_scores.json"
    if if_path.exists():
        with open(if_path) as f:
            methods['isolation_forest'] = json.load(f)
    
    # Load VAE results
    vae_path = results_dir / "anomaly_scores" / "vae_anomalies.json"
    if vae_path.exists():
        with open(vae_path) as f:
            methods['vae'] = json.load(f)
    
    # Load any other method results
    for result_file in results_dir.glob("anomaly_scores/*.json"):
        method_name = result_file.stem.replace('_scores', '').replace('_anomalies', '')
        if method_name not in methods:
            with open(result_file) as f:
                methods[method_name] = json.load(f)
    
    return methods

def normalize_scores(scores, method='minmax'):
    """Normalize scores to [0, 1] range"""
    scores = np.array(scores)
    
    if method == 'minmax':
        min_val = scores.min()
        max_val = scores.max()
        if max_val > min_val:
            return (scores - min_val) / (max_val - min_val)
        return scores
    
    elif method == 'zscore':
        mean = scores.mean()
        std = scores.std()
        if std > 0:
            return (scores - mean) / std
        return scores
    
    elif method == 'rank':
        from scipy.stats import rankdata
        ranks = rankdata(scores)
        return ranks / len(scores)
    
    return scores

def ensemble_consensus(methods, weights=None, agreement_threshold=2):
    """
    Combine multiple detection methods using weighted consensus.
    
    Args:
        methods: Dict of method_name -> results dict
        weights: Dict of method_name -> weight (default: equal weights)
        agreement_threshold: Minimum number of methods that must flag as anomaly
    
    Returns:
        DataFrame with ensemble scores and consensus decisions
    """
    # Collect all object IDs
    all_objids = set()
    method_scores = defaultdict(dict)
    
    for method_name, results in methods.items():
        if 'results' in results:
            for result in results['results']:
                objid = str(result['objid'])
                all_objids.add(objid)
                
                # Extract score (handle different naming conventions)
                if 'anomaly_score' in result:
                    score = result['anomaly_score']
                elif 'reconstruction_error' in result:
                    score = result['reconstruction_error']
                elif 'score' in result:
                    score = result['score']
                else:
                    score = 0.0
                    
                method_scores[method_name][objid] = {
                    'score': score,
                    'is_anomaly': result.get('is_anomaly', False)
                }
    
    # Set default weights if not provided
    if weights is None:
        weights = {method: 1.0 for method in methods.keys()}
    
    # Normalize weights
    total_weight = sum(weights.values())
    weights = {k: v / total_weight for k, v in weights.items()}
    
    # Build consensus results
    consensus_results = []
    
    for objid in all_objids:
        scores = []
        anomaly_votes = 0
        
        for method_name, weight in weights.items():
            if objid in method_scores[method_name]:
                method_result = method_scores[method_name][objid]
                scores.append(method_result['score'] * weight)
                if method_result['is_anomaly']:
                    anomaly_votes += 1
        
        # Calculate ensemble score
        if scores:
            ensemble_score = np.mean(scores)
        else:
            ensemble_score = 0.0
        
        # Consensus decision
        is_consensus_anomaly = (
            anomaly_votes >= agreement_threshold and 
            ensemble_score > np.percentile([r['ensemble_score'] for r in consensus_results] if consensus_results else [0], 95)
        )
        
        consensus_results.append({
            'objid': objid,
            'ensemble_score': float(ensemble_score),
            'anomaly_votes': anomaly_votes,
            'total_methods': len(methods),
            'is_consensus_anomaly': is_consensus_anomaly,
            'individual_scores': {
                method: method_scores[method].get(objid, {}).get('score', None)
                for method in methods.keys()
            }
        })
    
    # Sort by ensemble score
    consensus_results.sort(key=lambda x: x['ensemble_score'], reverse=True)
    
    return pd.DataFrame(consensus_results)

def statistical_consensus(df, methods_used, confidence_threshold=0.95):
    """
    Apply statistical consensus using confidence intervals.
    
    Args:
        df: DataFrame with individual method scores
        confidence_threshold: Confidence level for anomaly detection
    """
    # Calculate mean and std of scores across methods
    score_cols = [col for col in df.columns if col.startswith('score_')]
    
    df['mean_score'] = df[score_cols].mean(axis=1)
    df['std_score'] = df[score_cols].std(axis=1)
    
    # Confidence interval (using t-distribution approximation)
    n_methods = len(score_cols)
    from scipy import stats
    t_val = stats.t.ppf((1 + confidence_threshold) / 2, n_methods - 1)
    margin_error = t_val * df['std_score'] / np.sqrt(n_methods)
    
    df['ci_lower'] = df['mean_score'] - margin_error
    df['ci_upper'] = df['mean_score'] + margin_error
    
    # Flag as anomaly if lower bound of CI is above threshold
    threshold = df['mean_score'].quantile(0.95)
    df['is_anomaly'] = df['ci_lower'] > threshold
    
    return df

def generate_ensemble_report(consensus_df, output_path):
    """Generate detailed ensemble report"""
    output_path = Path(output_path)
    
    # Summary statistics
    total = len(consensus_df)
    anomalies = consensus_df['is_consensus_anomaly'].sum()
    
    report = f"""# Ensemble Consensus Report

Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- Total galaxies analyzed: {total}
- Consensus anomalies detected: {anomalies}
- Detection rate: {anomalies/total*100:.2f}%

## Method Agreement

"""
    
    # Vote distribution
    vote_counts = consensus_df['anomaly_votes'].value_counts().sort_index()
    report += "| Votes | Count | Percentage |\n"
    report += "|-------|-------|------------|\n"
    for votes, count in vote_counts.items():
        report += f"| {votes} | {count} | {count/total*100:.1f}% |\n"
    
    report += "\n## Top 20 Consensus Anomalies\n\n"
    report += "| Rank | Object ID | Ensemble Score | Votes |\n"
    report += "|------|-----------|----------------|-------|\n"
    
    top_anomalies = consensus_df[consensus_df['is_consensus_anomaly']].head(20)
    for i, (_, row) in enumerate(top_anomalies.iterrows(), 1):
        report += f"| {i} | {row['objid']} | {row['ensemble_score']:.4f} | {row['anomaly_votes']}/{row['total_methods']} |\n"
    
    # Save report
    with open(output_path, 'w') as f:
        f.write(report)
    
    # Save full results
    csv_path = output_path.with_suffix('.csv')
    consensus_df.to_csv(csv_path, index=False)
    
    print(f"Ensemble report saved to {output_path}")
    print(f"Full results saved to {csv_path}")
    
    return report

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Ensemble consensus for anomaly detection')
    parser.add_argument('--weights', type=str, help='JSON file with method weights')
    parser.add_argument('--agreement', type=int, default=2, 
                       help='Minimum methods agreeing for anomaly (default: 2)')
    parser.add_argument('--output-dir', type=str, help='Output directory')
    args = parser.parse_args()
    
    ROOT = Path("~/Desktop/astro1").expanduser()
    results_dir = ROOT / "results"
    
    # Load detection results from all methods
    print("Loading detection results...")
    methods = load_detection_results(results_dir)
    
    if not methods:
        print("No detection results found. Please run individual methods first.")
        return
    
    print(f"Found results from {len(methods)} methods: {list(methods.keys())}")
    
    # Load weights if provided
    weights = None
    if args.weights:
        with open(args.weights) as f:
            weights = json.load(f)
    
    # Compute ensemble consensus
    print("Computing ensemble consensus...")
    consensus_df = ensemble_consensus(methods, weights, args.agreement)
    
    # Generate report
    output_dir = Path(args.output_dir) if args.output_dir else results_dir / "candidates"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = output_dir / "ensemble_consensus_report.md"
    generate_ensemble_report(consensus_df, report_path)
    
    # Save JSON results
    json_path = output_dir / "ensemble_consensus.json"
    consensus_df.to_json(json_path, orient='records', indent=2)
    
    print(f"\nEnsemble consensus complete!")
    print(f"Top 5 anomalies:")
    top5 = consensus_df[consensus_df['is_consensus_anomaly']].head(5)
    for _, row in top5.iterrows():
        print(f"  {row['objid']}: score={row['ensemble_score']:.4f}, votes={row['anomaly_votes']}")

if __name__ == "__main__":
    main()
