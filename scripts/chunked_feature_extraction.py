#!/usr/bin/env python3
"""
Chunked feature extraction helper.
Usage: python scripts/chunked_feature_extraction.py
"""

import os
import sys
import numpy as np
import pandas as pd

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from ml.feature_extractor import url_to_feature_vector, get_feature_names

DATASET_PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', 'data', 'datasets', 'url_dataset.csv')
CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'backend', 'cache')
CHUNK_SIZE = 25000

os.makedirs(CACHE_DIR, exist_ok=True)

def main():
    df = pd.read_csv(DATASET_PATH)
    feature_names = get_feature_names()
    n = len(df)
    for start in range(0, n, CHUNK_SIZE):
        end = min(start + CHUNK_SIZE, n)
        cache_path = os.path.join(CACHE_DIR, f"features_{start}_{end}.npz")
        if os.path.exists(cache_path):
            print(f"Cache exists {cache_path}, skipping")
            continue
        print(f"Processing chunk {start}:{end}")
        chunk = df.iloc[start:end]
        X = []
        for url in chunk['url']:
            X.append(url_to_feature_vector(str(url)))
        X = np.array(X, dtype=float)
        y = chunk['type'].astype(str).str.lower().str.strip().apply(lambda x: 0 if x in {'legitimate','benign','safe','good','0','clean','white'} else 1).values
        np.savez_compressed(cache_path, X=X, y=y)
        print(f"Saved {cache_path}")

if __name__ == "__main__":
    main()
