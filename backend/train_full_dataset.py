#!/usr/bin/env python3
"""
Full Dataset Training for 450K+ URLs
Memory-efficient incremental training with proper threshold selection.
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime
import joblib
import logging
import gc
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_curve
from sklearn.calibration import CalibratedClassifierCV

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml.feature_extractor import url_to_feature_vector, get_feature_names

# CONFIG
DATASET_PATH = "data/datasets/url_dataset.csv"
CHUNK_SIZE = 50000  # Process 50K URLs at a time
MODEL_DIR = "ml/saved_models"
LOG_DIR = "logs"
CACHE_DIR = "cache"

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Logging
timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
logfile = os.path.join(LOG_DIR, f"full_dataset_train_{timestamp}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(logfile), logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("full_train")

class FullDatasetTrainer:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = None
        self.feature_names = get_feature_names()
        self.threshold = 0.1  # Start with reasonable threshold
        
    def load_cached_features(self):
        """Load precomputed features from cache."""
        logger.info("Loading cached features...")
        
        # Find all cache files
        cache_files = []
        for file in os.listdir(CACHE_DIR):
            if file.startswith("features_") and file.endswith(".npz"):
                cache_files.append(os.path.join(CACHE_DIR, file))
        
        cache_files.sort()  # Process in order
        
        all_X = []
        all_y = []
        
        for cache_file in cache_files:
            logger.info(f"Loading {cache_file}")
            data = np.load(cache_file)
            X = data['X']
            y = data['y']
            
            all_X.append(X)
            all_y.append(y)
            
            # Clean up memory
            del data
            gc.collect()
        
        # Combine all features
        X_combined = np.vstack(all_X)
        y_combined = np.hstack(all_y)
        
        logger.info(f"Loaded {X_combined.shape[0]:,} samples with {X_combined.shape[1]} features")
        return X_combined, y_combined
    
    def train_incremental(self, X, y):
        """Train using incremental learning to save memory."""
        logger.info("Starting incremental training...")
        
        # Split into chunks for incremental learning
        n_samples = X.shape[0]
        n_chunks = (n_samples + CHUNK_SIZE - 1) // CHUNK_SIZE
        
        logger.info(f"Training in {n_chunks} chunks of {CHUNK_SIZE:,} samples each")
        
        # Compute class weights manually for partial_fit
        from sklearn.utils.class_weight import compute_class_weight
        import numpy as np
        class_weights = compute_class_weight('balanced', classes=np.array([0, 1]), y=y)
        class_weight_dict = {0: class_weights[0], 1: class_weights[1]}
        logger.info(f"Class weights: {class_weight_dict}")
        
        # Initialize SGDClassifier for incremental learning
        self.model = SGDClassifier(
            loss='log_loss',  # Logistic regression
            penalty='l2',
            alpha=0.0001,
            learning_rate='adaptive',
            eta0=0.01,
            random_state=42,
            class_weight=class_weight_dict,  # Use computed weights
            max_iter=1000,
            tol=1e-3
        )
        
        # Fit scaler on first chunk
        first_chunk = X[:CHUNK_SIZE]
        self.scaler.fit(first_chunk)
        
        # Train incrementally
        for i in range(n_chunks):
            start_idx = i * CHUNK_SIZE
            end_idx = min((i + 1) * CHUNK_SIZE, n_samples)
            
            X_chunk = X[start_idx:end_idx]
            y_chunk = y[start_idx:end_idx]
            
            logger.info(f"Training chunk {i+1}/{n_chunks}: {len(X_chunk):,} samples")
            
            # Scale features
            X_chunk_scaled = self.scaler.transform(X_chunk)
            
            # Partial fit (incremental learning)
            self.model.partial_fit(X_chunk_scaled, y_chunk, classes=[0, 1])
            
            # Clean up memory
            del X_chunk, X_chunk_scaled
            gc.collect()
        
        logger.info("Incremental training complete")
    
    def calibrate_and_threshold(self, X, y):
        """Calibrate probabilities and select proper threshold."""
        logger.info("Calibrating probabilities and selecting threshold...")
        
        # Use a subset for calibration (to save memory)
        n_calibrate = min(50000, len(X))
        indices = np.random.choice(len(X), n_calibrate, replace=False)
        X_cal = X[indices]
        y_cal = y[indices]
        
        # Scale features
        X_cal_scaled = self.scaler.transform(X_cal)
        
        # Get probabilities
        probs = self.model.predict_proba(X_cal_scaled)[:, 1]
        
        # Calibrate
        try:
            calibrator = CalibratedClassifierCV(self.model, method='sigmoid', cv='prefit')
            calibrator.fit(X_cal_scaled, y_cal)
            self.model = calibrator
            logger.info("Calibration successful")
        except Exception as e:
            logger.warning(f"Calibration failed: {e}")
        
        # Select threshold with proper mapping
        precision, recall, thresholds = precision_recall_curve(y_cal, probs)
        
        # Correct threshold mapping
        recall_for_thresholds = recall[1:]  # Align with thresholds
        desired_recall = 0.95
        idxs = np.where(recall_for_thresholds >= desired_recall)[0]
        
        if len(idxs) > 0:
            self.threshold = float(thresholds[idxs[0]])
        else:
            # Fallback to 0.1 if no suitable threshold found
            self.threshold = 0.1
        
        # Enforce minimum threshold
        self.threshold = max(self.threshold, 0.05)
        
        logger.info(f"Selected threshold: {self.threshold:.3f}")
        
        # Evaluate
        preds = (probs >= self.threshold).astype(int)
        acc = accuracy_score(y_cal, preds)
        cm = confusion_matrix(y_cal, preds)
        
        logger.info(f"Calibration accuracy: {acc:.3f}")
        logger.info(f"False positives: {cm[0][1]}")
        logger.info(f"False negatives: {cm[1][0]}")
    
    def save_model(self):
        """Save the trained model."""
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'threshold': self.threshold,
            'trained_at': timestamp,
            'model_type': 'incremental_sgd'
        }
        
        model_path = os.path.join(MODEL_DIR, f"full_dataset_model_{timestamp}.joblib")
        joblib.dump(model_data, model_path)
        
        # Also save as default for compatibility
        default_path = os.path.join(MODEL_DIR, "threat_pipeline.joblib")
        joblib.dump(model_data, default_path)
        
        logger.info(f"Model saved to {model_path}")
        logger.info(f"Also saved as default: {default_path}")
    
    def predict(self, url: str):
        """Predict with two-threshold triage."""
        if not self.model:
            raise Exception("Model not trained")
        
        features = np.array([url_to_feature_vector(url)], dtype=float)
        features_scaled = self.scaler.transform(features)
        
        prob = self.model.predict_proba(features_scaled)[0]
        malicious_prob = float(prob[1])
        
        # Two-threshold triage
        high_threshold = max(self.threshold, 0.3)
        low_threshold = min(self.threshold, 0.1)
        
        if malicious_prob >= high_threshold:
            action = "block"
            is_malicious = True
        elif malicious_prob >= low_threshold:
            action = "manual_review"
            is_malicious = False
        else:
            action = "allow"
            is_malicious = False
        
        return {
            "is_malicious": is_malicious,
            "action": action,
            "confidence": malicious_prob,
            "probability_legitimate": float(prob[0]),
            "probability_malicious": malicious_prob,
            "threshold_used": self.threshold,
            "high_threshold": high_threshold,
            "low_threshold": low_threshold
        }

def main():
    logger.info("="*80)
    logger.info("FULL DATASET TRAINING - 450K+ URLs")
    logger.info("="*80)
    
    trainer = FullDatasetTrainer()
    
    # Step 1: Load cached features
    try:
        X, y = trainer.load_cached_features()
    except Exception as e:
        logger.error(f"Failed to load cached features: {e}")
        logger.info("Please run chunked feature extraction first:")
        logger.info("python ../scripts/chunked_feature_extraction.py")
        return
    
    # Step 2: Normalize labels
    logger.info("Normalizing labels...")
    # y should already be normalized from cache, but double-check
    unique_labels = np.unique(y)
    logger.info(f"Unique labels: {unique_labels}")
    logger.info(f"Legitimate: {np.sum(y==0):,}, Malicious: {np.sum(y==1):,}")
    
    # Step 3: Train incrementally
    trainer.train_incremental(X, y)
    
    # Step 4: Calibrate and select threshold
    trainer.calibrate_and_threshold(X, y)
    
    # Step 5: Save model
    trainer.save_model()
    
    # Step 6: Test prediction
    test_urls = [
        "https://www.google.com",
        "https://www.drdo.gov.in/drdo/",
        "http://suspicious-phishing-site.xyz/login"
    ]
    
    logger.info("\nTesting predictions:")
    for url in test_urls:
        result = trainer.predict(url)
        logger.info(f"{url}: {result['action']} (confidence: {result['confidence']:.3f})")
    
    logger.info("\n" + "="*80)
    logger.info("FULL DATASET TRAINING COMPLETE")
    logger.info("="*80)

if __name__ == "__main__":
    main()
