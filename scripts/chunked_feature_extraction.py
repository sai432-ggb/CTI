#!/usr/bin/env python3
"""
CTI-NLP - Chunked Feature Extraction
Precompute features in chunks and resume from checkpoints.

Usage:
    python scripts/chunked_feature_extraction.py --input data/datasets/url_dataset.csv --output data/features/features.pkl
    python scripts/chunked_feature_extraction.py --resume data/features/checkpoint.pkl
"""

import argparse
import os
import pickle
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from tqdm import tqdm

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from ml.feature_extractor import url_to_feature_vector, get_feature_names


class ChunkedFeatureExtractor:
    def __init__(self, chunk_size=10000, checkpoint_interval=5):
        self.chunk_size = chunk_size
        self.checkpoint_interval = checkpoint_interval
        self.feature_names = get_feature_names()
        
    def extract_features_chunked(self, input_path, output_path, resume_path=None):
        """Extract features in chunks with checkpoint support."""
        
        # Check for resume
        if resume_path and os.path.exists(resume_path):
            print(f"Resuming from checkpoint: {resume_path}")
            with open(resume_path, 'rb') as f:
                checkpoint = pickle.load(f)
            
            all_features = checkpoint['features']
            processed_urls = checkpoint['processed_urls']
            start_idx = checkpoint['next_index']
            df = checkpoint['dataframe']
        else:
            print(f"Starting fresh extraction from: {input_path}")
            df = pd.read_csv(input_path)
            all_features = []
            processed_urls = []
            start_idx = 0
            
        total_rows = len(df)
        print(f"Total URLs to process: {total_rows:,}")
        print(f"Starting from index: {start_idx:,}")
        
        # Process in chunks
        for chunk_start in range(start_idx, total_rows, self.chunk_size):
            chunk_end = min(chunk_start + self.chunk_size, total_rows)
            chunk_urls = df.iloc[chunk_start:chunk_end]['url'].tolist()
            
            print(f"\nProcessing chunk {chunk_start//self.chunk_size + 1}: {chunk_start:,} - {chunk_end:,}")
            
            # Extract features for this chunk
            chunk_features = []
            failed_urls = []
            
            for url in tqdm(chunk_urls, desc="Extracting features"):
                try:
                    features = url_to_feature_vector(str(url))
                    chunk_features.append(features)
                    processed_urls.append(url)
                except Exception as e:
                    print(f"Failed to extract features for {url}: {e}")
                    # Add zero features for failed URLs
                    chunk_features.append([0] * len(self.feature_names))
                    processed_urls.append(url)
                    failed_urls.append(url)
            
            # Append to all features
            all_features.extend(chunk_features)
            
            # Save checkpoint periodically
            chunk_num = chunk_start // self.chunk_size
            if chunk_num % self.checkpoint_interval == 0 or chunk_end >= total_rows:
                checkpoint_path = f"data/features/checkpoint_{chunk_start:06d}.pkl"
                self._save_checkpoint(checkpoint_path, all_features, processed_urls, df, chunk_end)
                print(f"Checkpoint saved: {checkpoint_path}")
                
                if failed_urls:
                    print(f"Failed URLs in chunk: {len(failed_urls)}")
        
        # Convert to numpy array
        final_features = np.array(all_features)
        print(f"\nFeature extraction complete!")
        print(f"Shape: {final_features.shape}")
        print(f"Failed URLs: {len([url for url in processed_urls if url in failed_urls])}")
        
        # Save final features
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            pickle.dump({
                'features': final_features,
                'urls': processed_urls,
                'feature_names': self.feature_names,
                'total_processed': len(processed_urls)
            }, f)
        
        print(f"Final features saved to: {output_path}")
        return final_features
    
    def _save_checkpoint(self, checkpoint_path, features, processed_urls, dataframe, next_index):
        """Save checkpoint data."""
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        checkpoint_data = {
            'features': features,
            'processed_urls': processed_urls,
            'dataframe': dataframe,
            'next_index': next_index,
            'timestamp': pd.Timestamp.now()
        }
        with open(checkpoint_path, 'wb') as f:
            pickle.dump(checkpoint_data, f)
    
    def get_latest_checkpoint(self, checkpoint_dir="data/features"):
        """Find the latest checkpoint file."""
        checkpoint_dir = Path(checkpoint_dir)
        checkpoints = list(checkpoint_dir.glob("checkpoint_*.pkl"))
        
        if not checkpoints:
            return None
        
        # Sort by index in filename
        checkpoints.sort(key=lambda x: int(x.stem.split('_')[1]))
        return checkpoints[-1]


def main():
    parser = argparse.ArgumentParser(description="Chunked feature extraction with checkpoint support")
    parser.add_argument("--input", required=True, help="Input CSV file with URLs")
    parser.add_argument("--output", required=True, help="Output pickle file for features")
    parser.add_argument("--resume", help="Resume from checkpoint file")
    parser.add_argument("--chunk-size", type=int, default=10000, help="Chunk size for processing")
    parser.add_argument("--checkpoint-interval", type=int, default=5, help="Save checkpoint every N chunks")
    
    args = parser.parse_args()
    
    extractor = ChunkedFeatureExtractor(
        chunk_size=args.chunk_size,
        checkpoint_interval=args.checkpoint_interval
    )
    
    # Auto-resume from latest checkpoint if --resume not specified
    if not args.resume:
        latest = extractor.get_latest_checkpoint()
        if latest:
            print(f"Found latest checkpoint: {latest}")
            response = input("Resume from latest checkpoint? (y/n): ")
            if response.lower() == 'y':
                args.resume = str(latest)
    
    features = extractor.extract_features_chunked(
        input_path=args.input,
        output_path=args.output,
        resume_path=args.resume
    )
    
    print(f"\nExtraction complete! Features shape: {features.shape}")


if __name__ == "__main__":
    main()
