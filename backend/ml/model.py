"""
CTI-NLP - Improved Threat Model
Uses feature engineering instead of TF-IDF character ngrams.
This is how real URL classifiers work (PhishTank, Google Safe Browsing, etc.)
"""

import joblib
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.utils import resample

from .feature_extractor import url_to_feature_vector, get_feature_names


class ThreatModel:
    def __init__(self, model_path: str = "ml/saved_models/threat_pipeline.joblib"):
        self.model_path = model_path
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        self.pipeline = self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            print(f"Loaded existing model from {self.model_path}")
            return joblib.load(self.model_path)
        return None

    def _extract_features_batch(self, urls: pd.Series) -> np.ndarray:
        """Convert a list of URLs into a feature matrix."""
        print(f"  Extracting features from {len(urls)} URLs...")
        features = []
        for i, url in enumerate(urls):
            if i % 10000 == 0 and i > 0:
                print(f"  ... processed {i}/{len(urls)}")
            try:
                features.append(url_to_feature_vector(str(url)))
            except Exception:
                # If feature extraction fails, use zeros
                features.append([0] * len(get_feature_names()))
        return np.array(features)

    def _balance_dataset(self, X: np.ndarray, y: np.ndarray):
        """Balance classes by upsampling minority class."""
        X_df = pd.DataFrame(X)
        X_df['label'] = y

        majority = X_df[X_df['label'] == 0]
        minority = X_df[X_df['label'] == 1]

        print(f"  Before balancing: {len(majority)} legitimate, {len(minority)} phishing")

        # Upsample minority to match majority
        minority_upsampled = resample(
            minority,
            replace=True,
            n_samples=len(majority),
            random_state=42
        )
        balanced = pd.concat([majority, minority_upsampled]).sample(frac=1, random_state=42)

        y_balanced = balanced['label'].values
        X_balanced = balanced.drop('label', axis=1).values

        print(f"  After balancing: {sum(y_balanced == 0)} legitimate, {sum(y_balanced == 1)} phishing")
        return X_balanced, y_balanced

    def train(self, df: pd.DataFrame, text_col: str = 'url', label_col: str = 'is_malicious'):
        """
        Train the model using feature engineering instead of TF-IDF.
        This gives much better accuracy and fewer false positives.
        """
        print("\n=== CTI-NLP Model Training (Feature Engineering Mode) ===\n")

        # Step 1: Extract features
        print("Step 1: Extracting URL features...")
        X = self._extract_features_batch(df[text_col])
        y = df[label_col].values

        # Step 2: Balance the dataset
        print("Step 2: Balancing dataset...")
        X, y = self._balance_dataset(X, y)

        # Step 3: Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=0.2,
            stratify=y,
            random_state=42
        )
        print(f"Step 3: Split into {len(X_train)} training, {len(X_test)} test samples")

        # Step 4: Build the ENSEMBLE model
        # We use 3 models that vote - this reduces false positives dramatically
        print("Step 4: Building ensemble classifier...")

        rf = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=4,
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'
        )

        gb = GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=6,
            random_state=42,
            subsample=0.8
        )

        # Ensemble: majority vote between RF and GB
        ensemble = VotingClassifier(
            estimators=[('rf', rf), ('gb', gb)],
            voting='soft'  # Use probability averaging, not hard vote
        )

        # Wrap in pipeline with scaler
        self.pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', ensemble)
        ])

        print("Step 5: Training ensemble (this takes 1-3 minutes)...")
        self.pipeline.fit(X_train, y_train)

        # Step 6: Evaluate
        print("\n=== EVALUATION ===")
        y_pred = self.pipeline.predict(X_test)
        acc = accuracy_score(y_test, y_pred)

        print(f"Test Accuracy: {acc:.4f} ({acc*100:.1f}%)")
        print("\nClassification Report:")
        report = classification_report(y_test, y_pred, target_names=['Legitimate', 'Malicious'])
        print(report)

        cm = confusion_matrix(y_test, y_pred)
        print(f"Confusion Matrix:")
        print(f"  True Legit (correct):    {cm[0][0]}")
        print(f"  False Positive (wrong):  {cm[0][1]}  ← should be LOW")
        print(f"  False Negative (missed): {cm[1][0]}  ← should be LOW")
        print(f"  True Malicious (correct):{cm[1][1]}")

        # Step 7: Save
        joblib.dump(self.pipeline, self.model_path)
        print(f"\nModel saved to {self.model_path}")

        return {
            "accuracy": acc,
            "report": report,
            "true_legit": int(cm[0][0]),
            "false_positives": int(cm[0][1]),
            "false_negatives": int(cm[1][0]),
            "true_malicious": int(cm[1][1]),
        }

    def predict(self, url: str) -> dict:
        """
        Predict if a URL is malicious.
        Returns is_malicious (bool) and confidence (float 0-1).
        """
        if not self.pipeline:
            raise Exception("Model not trained. Run train_model.py first.")

        features = np.array([url_to_feature_vector(url)])
        prob = self.pipeline.predict_proba(features)[0]
        is_malicious = bool(self.pipeline.predict(features)[0])

        # prob[0] = probability of legitimate
        # prob[1] = probability of malicious
        malicious_prob = float(prob[1])

        # Apply a confidence THRESHOLD to reduce false positives.
        # Only call it malicious if the model is > 60% confident.
        THRESHOLD = 0.60
        if malicious_prob >= THRESHOLD:
            is_malicious = True
        else:
            is_malicious = False

        # Get which features triggered the most suspicion (for explainability)
        feature_values = url_to_feature_vector(url)
        feature_names = get_feature_names()
        top_features = [
            {"feature": feature_names[i], "value": feature_values[i]}
            for i in sorted(
                range(len(feature_values)),
                key=lambda x: feature_values[x],
                reverse=True
            )[:5]
        ]

        return {
            "is_malicious": is_malicious,
            "confidence": malicious_prob,
            "probability_legitimate": float(prob[0]),
            "probability_malicious": malicious_prob,
            "top_suspicious_features": top_features,
            "threshold_used": THRESHOLD
        }
