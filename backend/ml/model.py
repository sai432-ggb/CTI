import joblib
import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from .preprocess import clean_url

class ThreatModel:
    def __init__(self, model_path: str = "ml/saved_models/threat_pipeline.joblib"):
        self.model_path = model_path
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        self.pipeline = self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            return joblib.load(self.model_path)
        return None

    def train(self, df: pd.DataFrame, text_col: str = 'url', label_col: str = 'is_malicious'):
        """Trains the NLP model to classify URLs."""
        df[text_col] = df[text_col].apply(clean_url)
        X_train, X_test, y_train, y_test = train_test_split(df[text_col], df[label_col], test_size=0.2, random_state=42)

        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(analyzer='char', ngram_range=(3, 5), max_features=5000)),
            ('clf', RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1))
        ])

        print("Training model...")
        self.pipeline.fit(X_train, y_train)
        
        # Evaluate
        predictions = self.pipeline.predict(X_test)
        acc = accuracy_score(y_test, predictions)
        report = classification_report(y_test, predictions)
        
        # Save
        joblib.dump(self.pipeline, self.model_path)
        return {"accuracy": acc, "report": report}

    def predict(self, url: str) -> dict:
        if not self.pipeline:
            raise Exception("Model not trained yet.")
        
        cleaned = clean_url(url)
        prob = self.pipeline.predict_proba([cleaned])[0]
        is_malicious = bool(self.pipeline.predict([cleaned])[0])
        
        return {
            "is_malicious": is_malicious,
            "confidence": float(prob[1] if is_malicious else prob[0])
        }