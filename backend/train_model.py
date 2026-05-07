#!/usr/bin/env python3
"""
Main training entrypoint.
Usage: python train_model.py
"""

import os
import sys
import time
import logging
from datetime import datetime
import pandas as pd
import joblib

# ensure repo root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml.model import ThreatModel
from ml.feature_extractor import get_feature_names

# CONFIG
DATASET_PATH = "data/datasets/url_dataset.csv"
URL_COLUMN = "url"
LABEL_COLUMN = "type"
SAMPLE_SIZE = 100000  # Use 100K samples for memory-efficient training
CACHE_DIR = "cache"
LOG_DIR = "logs"
MODEL_DIR = "ml/saved_models"

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# Logging
timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
logfile = os.path.join(LOG_DIR, f"train_{timestamp}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(logfile), logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("train")

def backup_artifacts():
    os.makedirs("backups", exist_ok=True)
    try:
        if os.path.exists(DATASET_PATH):
            dst = f"backups/url_dataset_{timestamp}.csv"
            logger.info(f"Backing up dataset to {dst}")
            import shutil
            shutil.copy2(DATASET_PATH, dst)
    except Exception as e:
        logger.warning(f"Backup dataset failed: {e}")
    try:
        model_path = os.path.join(MODEL_DIR, "threat_pipeline.joblib")
        if os.path.exists(model_path):
            dst = f"backups/threat_pipeline_{timestamp}.joblib"
            logger.info(f"Backing up existing model to {dst}")
            import shutil
            shutil.copy2(model_path, dst)
    except Exception as e:
        logger.warning(f"Backup model failed: {e}")

def main():
    logger.info("="*60)
    logger.info("CTI-NLP Threat Model - Full Training Runner")
    logger.info("="*60)

    # Step 0: basic checks
    if not os.path.exists(DATASET_PATH):
        logger.error(f"Dataset not found at {DATASET_PATH}")
        sys.exit(1)

    backup_artifacts()

    # Load dataset
    logger.info("[1/6] Loading dataset")
    df = pd.read_csv(DATASET_PATH)
    logger.info(f"Loaded {len(df):,} rows. Columns: {list(df.columns)}")

    # Normalize labels to binary 'is_malicious'
    logger.info("[2/6] Normalizing labels")
    LEGITIMATE_VALUES = {'legitimate', 'benign', 'safe', 'good', '0', 'clean', 'white', 'false', 'no'}
    df['is_malicious'] = df[LABEL_COLUMN].astype(str).str.lower().str.strip().apply(
        lambda x: 0 if x in LEGITIMATE_VALUES else 1
    )
    logger.info(f"Legitimate: {(df['is_malicious']==0).sum():,}, Malicious: {(df['is_malicious']==1).sum():,}")

    # Optional sampling
    if SAMPLE_SIZE:
        sample_size = min(SAMPLE_SIZE, len(df))
        logger.info(f"[3/6] Sampling {sample_size:,} rows (stratified)")
        from sklearn.model_selection import train_test_split
        df_sampled, _ = train_test_split(df, train_size=sample_size, stratify=df['is_malicious'], random_state=42)
        df = df_sampled.reset_index(drop=True)
        logger.info(f"Sampled dataset size: {len(df):,}")
    else:
        logger.info("[3/6] Using full dataset for training")

    # Step 4: Train
    logger.info("[4/6] Training model")
    model = ThreatModel(model_path=os.path.join(MODEL_DIR, "threat_pipeline.joblib"), cache_dir=CACHE_DIR, logger=logger)
    results = model.train(df, text_col=URL_COLUMN, label_col='is_malicious')

    # Step 5: Save summary and metadata
    logger.info("[5/6] Saving training summary")
    summary_path = os.path.join(MODEL_DIR, f"train_summary_{timestamp}.joblib")
    joblib.dump({"results": results, "timestamp": timestamp}, summary_path)
    logger.info(f"Training summary saved to {summary_path}")

    # Step 6: Final notes
    logger.info("[6/6] TRAINING COMPLETE")
    logger.info(f"Accuracy: {results['accuracy']*100:.2f}%")
    logger.info(f"Model saved to {results.get('model_path')}")
    logger.info("Restart your FastAPI backend to use the new model.")
    logger.info("="*60)

if __name__ == "__main__":
    main()
