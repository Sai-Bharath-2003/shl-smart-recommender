"""
Evaluation script for SHL Assessment Recommendation System
Computes Mean Recall@K on the train set and generates predictions on the test set
"""

import pandas as pd
import json
import re
import sys
import os
import time
import requests
from typing import List, Dict, Set

# Add parent dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# ---------------------------------------------------------------------------
# Metric computation
# ---------------------------------------------------------------------------

def recall_at_k(predicted: List[str], relevant: Set[str], k: int = 10) -> float:
    """Compute Recall@K."""
    if not relevant:
        return 0.0
    top_k = set(predicted[:k])
    hits = len(top_k & relevant)
    return hits / len(relevant)


def mean_recall_at_k(predictions: Dict[str, List[str]], labels: Dict[str, Set[str]], k: int = 10) -> float:
    """Compute Mean Recall@K across all queries."""
    scores = []
    for query, relevant in labels.items():
        predicted = predictions.get(query, [])
        r_k = recall_at_k(predicted, relevant, k)
        scores.append(r_k)
        print(f"  Query: {query[:60]}...")
        print(f"  Recall@{k}: {r_k:.3f} ({len(set(predicted[:k]) & relevant)}/{len(relevant)} hits)")
        print()
    
    mean = sum(scores) / len(scores) if scores else 0.0
    return mean


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_train_labels(excel_path: str) -> Dict[str, Set[str]]:
    """Load ground truth labels from train set."""
    df = pd.read_excel(excel_path, sheet_name='Train-Set')
    
    labels = {}
    for _, row in df.iterrows():
        query = str(row['Query']).strip()
        url = str(row['Assessment_url']).strip()
        
        if query not in labels:
            labels[query] = set()
        labels[query].add(url)
    
    print(f"Loaded {len(labels)} train queries with {sum(len(v) for v in labels.values())} total labels")
    return labels


def load_test_queries(excel_path: str) -> List[str]:
    """Load test queries."""
    df = pd.read_excel(excel_path, sheet_name='Test-Set')
    return [str(q).strip() for q in df['Query'].tolist()]


# ---------------------------------------------------------------------------
# Get predictions via API
# ---------------------------------------------------------------------------

def get_predictions_api(queries: List[str], api_url: str) -> Dict[str, List[str]]:
    """Get predictions from the API endpoint."""
    predictions = {}
    
    for i, query in enumerate(queries):
        print(f"Getting predictions for query {i+1}/{len(queries)}: {query[:60]}...")
        
        try:
            resp = requests.post(
                f"{api_url}/recommend",
                json={"query": query},
                timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            urls = [a['url'] for a in data.get('recommended_assessments', [])]
            predictions[query] = urls
            print(f"  Got {len(urls)} recommendations")
        except Exception as e:
            print(f"  ERROR: {e}")
            predictions[query] = []
        
        time.sleep(0.5)  # Rate limiting
    
    return predictions


# ---------------------------------------------------------------------------
# Get predictions via direct engine
# ---------------------------------------------------------------------------

def get_predictions_direct(queries: List[str], catalog_path: str, api_key: str) -> Dict[str, List[str]]:
    """Get predictions directly from the recommendation engine."""
    from recommender import get_engine
    
    engine = get_engine(catalog_path=catalog_path, api_key=api_key)
    predictions = {}
    
    for i, query in enumerate(queries):
        print(f"Getting predictions for query {i+1}/{len(queries)}: {query[:60]}...")
        
        try:
            recs = engine.recommend(query, n=10, use_llm_rerank=True)
            urls = [r['url'] for r in recs]
            predictions[query] = urls
            print(f"  Got {len(urls)} recommendations")
        except Exception as e:
            print(f"  ERROR: {e}")
            predictions[query] = []
    
    return predictions


# ---------------------------------------------------------------------------
# Save test predictions as CSV
# ---------------------------------------------------------------------------

def save_predictions_csv(predictions: Dict[str, List[str]], output_path: str):
    """Save predictions in the required CSV format."""
    rows = []
    for query, urls in predictions.items():
        for url in urls:
            rows.append({'Query': query, 'Assessment_url': url})
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"\nSaved predictions to {output_path}")
    print(f"Total rows: {len(rows)} across {len(predictions)} queries")


# ---------------------------------------------------------------------------
# Main evaluation
# ---------------------------------------------------------------------------

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate SHL Recommendation System')
    parser.add_argument('--dataset', required=True, help='Path to Gen_AI_Dataset.xlsx')
    parser.add_argument('--catalog', required=True, help='Path to shl_catalog.json')
    parser.add_argument('--api-key', default=os.environ.get('GEMINI_API_KEY', ''), help='Gemini API key')
    parser.add_argument('--api-url', default='', help='API base URL (optional, uses direct engine if not provided)')
    parser.add_argument('--output-csv', default='predictions_test.csv', help='Output CSV path')
    parser.add_argument('--mode', choices=['train', 'test', 'both'], default='both', help='Evaluation mode')
    args = parser.parse_args()
    
    print("=" * 60)
    print("SHL Assessment Recommendation Evaluation")
    print("=" * 60)
    
    # Load data
    train_labels = load_train_labels(args.dataset)
    test_queries = load_test_queries(args.dataset)
    
    # Choose prediction method
    get_preds = (
        lambda queries: get_predictions_api(queries, args.api_url)
        if args.api_url
        else get_predictions_direct(queries, args.catalog, args.api_key)
    )
    
    # Evaluate on train set
    if args.mode in ('train', 'both'):
        print("\n--- TRAIN SET EVALUATION ---\n")
        train_queries = list(train_labels.keys())
        train_preds = get_preds(train_queries)
        
        mean_r10 = mean_recall_at_k(train_preds, train_labels, k=10)
        print(f"\n{'='*40}")
        print(f"Mean Recall@10 (Train): {mean_r10:.4f}")
        print(f"{'='*40}\n")
        
        # Save train predictions
        save_predictions_csv(train_preds, 'predictions_train.csv')
    
    # Generate test predictions
    if args.mode in ('test', 'both'):
        print("\n--- TEST SET PREDICTIONS ---\n")
        test_preds = get_preds(test_queries)
        save_predictions_csv(test_preds, args.output_csv)
    
    print("\nDone!")


if __name__ == '__main__':
    main()
