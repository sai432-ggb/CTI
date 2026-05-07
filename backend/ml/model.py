"""
Improved ThreatModel with calibration, SMOTE option, chunked feature caching,
operational threshold selection, and robust saving of metadata.
"""

import os
import time
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_curve
from sklearn.calibration import CalibratedClassifierCV
from imblearn.over_sampling import SMOTE

from .feature_extractor import url_to_feature_vector, get_feature_names

class ThreatModel:
    def __init__(self, model_path: str = "ml/saved_models/threat_pipeline.joblib", cache_dir: str = "cache", logger=None):
        self.model_path = model_path
        self.cache_dir = cache_dir
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        self.pipeline = None
        self.feature_names = get_feature_names()
        self.scaler = None
        self.threshold = 0.6
        self.logger = logger
        # load existing model if present
        if os.path.exists(self.model_path):
            try:
                loaded = joblib.load(self.model_path)
                # support multiple model formats
                if isinstance(loaded, dict):
                    if 'pipeline' in loaded:
                        # Standard ThreatModel format
                        self.pipeline = loaded['pipeline']
                        self.feature_names = loaded.get('feature_names', self.feature_names)
                        self.threshold = loaded.get('threshold', 0.6)
                    elif 'model' in loaded and 'scaler' in loaded:
                        # Full dataset training format
                        self.scaler = loaded['scaler']
                        self.pipeline = loaded['model']
                        self.feature_names = loaded.get('feature_names', self.feature_names)
                        self.threshold = loaded.get('threshold', 0.05)
                    else:
                        # Unknown dict format
                        raise ValueError("Unknown model dict format")
                else:
                    # Direct pipeline (legacy format)
                    self.pipeline = loaded
                    self.threshold = 0.6
                
                if self.logger:
                    self.logger.info(f"Loaded existing model from {self.model_path}")
                    if self.scaler:
                        self.logger.info("Using full dataset model with separate scaler")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Failed to load existing model: {e}")
                # Fallback to untrained state
                self.pipeline = None

    def _log(self, msg):
        if self.logger:
            self.logger.info(msg)
        else:
            print(msg)

    def _extract_features_batch(self, urls: pd.Series, cache_name: str = None):
        """
        Convert a list of URLs into a feature matrix.
        If cache_name provided, save to cache_dir/cache_name.npz and reuse if exists.
        """
        if cache_name:
            cache_path = os.path.join(self.cache_dir, f"{cache_name}.npz")
            if os.path.exists(cache_path):
                self._log(f"Loading cached features from {cache_path}")
                data = np.load(cache_path)
                return data['X'], data['y']

        self._log(f"Extracting features from {len(urls)} URLs...")
        features = []
        for i, url in enumerate(urls):
            if i % 10000 == 0 and i > 0:
                self._log(f"  ... processed {i}/{len(urls)}")
            try:
                vec = url_to_feature_vector(str(url))
                if len(vec) != len(self.feature_names):
                    raise ValueError("feature length mismatch")
                features.append(vec)
            except Exception as e:
                # log and use zeros
                self._log(f"Feature extraction failed for index {i}: {e}")
                features.append([0.0] * len(self.feature_names))
        X = np.array(features, dtype=float)
        # y must be provided by caller; return X only here
        if cache_name:
            np.savez_compressed(cache_path, X=X)
            self._log(f"Saved features to cache {cache_path}")
        return X

    def _balance_dataset(self, X: np.ndarray, y: np.ndarray, method: str = "upsample"):
        """
        Balance classes. method: 'upsample' (safer for large datasets)
        Returns balanced X, y.
        """
        self._log(f"  Before balancing: {np.sum(y==0)} legitimate, {np.sum(y==1)} malicious")
        
        # Use simple upsample for large datasets to avoid memory issues
        if method == "smote":
            self._log("Using upsample instead of SMOTE for memory efficiency with large datasets")
            method = "upsample"

        if method == "upsample":
            # simple upsample minority
            dfX = pd.DataFrame(X)
            dfX['label'] = y
            majority = dfX[dfX['label'] == 0]
            minority = dfX[dfX['label'] == 1]
            minority_upsampled = minority.sample(n=len(majority), replace=True, random_state=42)
            balanced = pd.concat([majority, minority_upsampled]).sample(frac=1, random_state=42)
            y_bal = balanced['label'].values
            X_bal = balanced.drop('label', axis=1).values
            self._log(f"  After upsample: {np.sum(y_bal==0)} legitimate, {np.sum(y_bal==1)} malicious")
            return X_bal, y_bal

        return X, y

    def _build_pipeline(self):
        rf = RandomForestClassifier(
            n_estimators=100,  # Reduced for memory
            max_depth=10,      # Reduced depth
            min_samples_split=10,  # Increased to prevent overfitting
            min_samples_leaf=5,    # Increased to prevent overfitting
            random_state=42,
            n_jobs=1,          # Single thread to save memory
            class_weight='balanced',
            max_samples=0.6    # Use 60% of samples per tree
        )
        gb = GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=6,
            random_state=42,
            subsample=0.8
        )
        ensemble = VotingClassifier(
            estimators=[('rf', rf), ('gb', gb)],
            voting='soft',
            n_jobs=1  # Single thread to save memory
        )
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', ensemble)
        ])
        return pipeline

    def train(self, df: pd.DataFrame, text_col: str = 'url', label_col: str = 'is_malicious', cache_name: str = None):
        """
        Train the model end-to-end. Returns metrics and saves model + metadata.
        """
        self._log("\n=== CTI-NLP Model Training (Feature Engineering Mode) ===\n")
        # Step 1: Extract features (with optional caching)
        self._log("Step 1: Extracting URL features...")
        X = self._extract_features_batch(df[text_col], cache_name=cache_name)
        y = df[label_col].values

        # Step 2: Balance dataset
        self._log("Step 2: Balancing dataset...")
        X_bal, y_bal = self._balance_dataset(X, y, method="upsample")

        # Step 3: Train/test split with holdout validation for calibration
        X_train, X_hold, y_train, y_hold = train_test_split(
            X_bal, y_bal, test_size=0.2, stratify=y_bal, random_state=42
        )
        self._log(f"Step 3: Split into {len(X_train)} training, {len(X_hold)} holdout samples")

        # Step 4: Build pipeline and fit
        self._log("Step 4: Building ensemble classifier...")
        self.pipeline = self._build_pipeline()
        self._log("Step 5: Training ensemble (this may take time)...")
        self.pipeline.fit(X_train, y_train)

        # Calibrate probabilities using holdout (robust across sklearn versions)
        self._log("Step 6: Calibrating probabilities (isotonic/sigmoid fallback)...")
        calibrator = None
        try:
            base_clf = self.pipeline.named_steps['clf']
            scaler = self.pipeline.named_steps['scaler']
            X_hold_scaled = scaler.transform(X_hold)

            # Try modern API first (estimator param)
            try:
                calibrator = CalibratedClassifierCV(estimator=base_clf, method='isotonic', cv=5)
            except TypeError:
                # Older sklearn uses base_estimator param name
                calibrator = CalibratedClassifierCV(base_estimator=base_clf, method='isotonic', cv=5)

            calibrator.fit(X_hold_scaled, y_hold)
            # Replace clf with calibrated wrapper
            self.pipeline.named_steps['clf'] = calibrator
            self._log("Calibration complete (isotonic).")
        except Exception as e_iso:
            self._log(f"Isotonic calibration failed: {e_iso}. Trying sigmoid (Platt) fallback.")
            try:
                # Try sigmoid (more stable on small calibration sets)
                try:
                    calibrator = CalibratedClassifierCV(estimator=base_clf, method='sigmoid', cv=5)
                except TypeError:
                    calibrator = CalibratedClassifierCV(base_estimator=base_clf, method='sigmoid', cv=5)
                calibrator.fit(X_hold_scaled, y_hold)
                self.pipeline.named_steps['clf'] = calibrator
                self._log("Calibration complete (sigmoid).")
            except Exception as e_sig:
                self._log(f"Calibration failed entirely: {e_sig}. Proceeding without calibration.")
                calibrator = None

        # Step 6: Evaluate on holdout
        self._log("\n=== EVALUATION ===")
        probs = self.pipeline.predict_proba(X_hold)[:, 1]
        preds = (probs >= 0.5).astype(int)
        acc = accuracy_score(y_hold, preds)
        report = classification_report(y_hold, preds, target_names=['Legitimate', 'Malicious'])
        cm = confusion_matrix(y_hold, preds)
        self._log(f"Test Accuracy: {acc:.4f} ({acc*100:.1f}%)")
        self._log("\nClassification Report:")
        self._log(report)
        self._log("Confusion Matrix:")
        self._log(f"  True Legit (correct):    {cm[0][0]}")
        self._log(f"  False Positive (wrong):  {cm[0][1]}")
        self._log(f"  False Negative (missed): {cm[1][0]}")
        self._log(f"  True Malicious (correct):{cm[1][1]}")

        # Compute operational threshold from precision-recall curve
        precision, recall, thresholds = precision_recall_curve(y_hold, probs)
        # thresholds[i] corresponds to precision[i+1], recall[i+1]
        # We want indices in thresholds where recall at thresholds >= desired_recall
        desired_recall = 0.98
        # recall_for_thresholds aligns with thresholds
        recall_for_thresholds = recall[1:]
        idxs = np.where(recall_for_thresholds >= desired_recall)[0]

        if len(idxs) > 0:
            operational_threshold = float(thresholds[idxs[0]])
        else:
            # fallback: choose threshold that maximizes F1 (exclude last element)
            f1_scores = 2 * (precision * recall) / (precision + recall + 1e-12)
            # f1_scores length == len(precision); thresholds length == len(precision)-1
            best_idx = int(np.nanargmax(f1_scores[:-1]))
            operational_threshold = float(thresholds[best_idx]) if len(thresholds) > 0 else 0.5

        # enforce a sensible minimum floor to avoid near-zero thresholds
        MIN_THRESHOLD = 0.05
        operational_threshold = max(operational_threshold, MIN_THRESHOLD)
        self._log(f"Chosen operational threshold: {operational_threshold:.3f}")

        # Step 8: Save pipeline and metadata
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        model_artifact = {
            "pipeline": self.pipeline,
            "feature_names": self.feature_names,
            "threshold": operational_threshold,
            "calibrator": calibrator,
            "trained_at": timestamp
        }
        joblib.dump(model_artifact, self.model_path)
        self._log(f"Model saved to {self.model_path}")

        return {
            "accuracy": acc,
            "report": report,
            "true_legit": int(cm[0][0]),
            "false_positives": int(cm[0][1]),
            "false_negatives": int(cm[1][0]),
            "true_malicious": int(cm[1][1]),
            "model_path": self.model_path,
            "threshold": operational_threshold,
            "trained_at": timestamp
        }

    def predict(self, url: str):
        """
        Predict if a URL is malicious. Returns dict with probabilities, threshold used,
        action triage, and top contributing features (raw values).
        """
        if not self.pipeline:
            raise Exception("Model not trained. Run train_model.py first.")

        features = np.array([url_to_feature_vector(url)], dtype=float)
        
        # Handle different model formats
        if self.scaler:
            # Full dataset model with separate scaler
            features_scaled = self.scaler.transform(features)
            prob = self.pipeline.predict_proba(features_scaled)[0]
        else:
            # Standard pipeline model
            prob = self.pipeline.predict_proba(features)[0]
        
        malicious_prob = float(prob[1])
        
        # Two-threshold triage for better decision making
        high_threshold = max(self.threshold, 0.5)   # auto-block threshold
        low_threshold = min(self.threshold, 0.2)    # manual review threshold

        action = "allow"
        is_malicious = False
        
        if malicious_prob >= high_threshold:
            is_malicious = True
            action = "block"
        elif malicious_prob >= low_threshold:
            is_malicious = False
            action = "manual_review"
        else:
            is_malicious = False
            action = "allow"

        # top features by raw value
        feature_values = url_to_feature_vector(url)
        feature_names = self.feature_names
        top_idx = sorted(range(len(feature_values)), key=lambda i: feature_values[i], reverse=True)[:5]
        top_features = [{"feature": feature_names[i], "value": float(feature_values[i])} for i in top_idx]

        return {
            "is_malicious": bool(is_malicious),
            "action": action,
            "confidence": malicious_prob,
            "probability_legitimate": float(prob[0]),
            "probability_malicious": malicious_prob,
            "top_suspicious_features": top_features,
            "threshold_used": float(self.threshold),
            "high_threshold": float(high_threshold),
            "low_threshold": float(low_threshold)
        }
