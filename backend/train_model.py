"""
CTI-NLP - Model Training Script
Drop-in replacement for your existing train_model.py.

Run this with:  python train_model.py

Your dataset only needs two columns: 'url' and a label column.
Supported label values: 'phishing', 'legitimate', 'benign', '0', '1', etc.
"""

import pandas as pd
import os
import sys

# Add parent dir to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.model import ThreatModel

# ─────────────────────────────────────────────
# CONFIGURATION - Edit these if needed
# ─────────────────────────────────────────────
DATASET_PATH = "data/datasets/url_dataset.csv"
URL_COLUMN = "url"           # Column name containing URLs
LABEL_COLUMN = "type"        # Column name containing labels
SAMPLE_SIZE = 60000          # How many URLs to train on (increase if RAM allows)
# ─────────────────────────────────────────────

os.makedirs("ml/saved_models", exist_ok=True)

print("=" * 60)
print("  CTI-NLP Threat Model - Feature Engineering Trainer")
print("=" * 60)

# ── Step 1: Load dataset ──
print(f"\n[1/5] Loading dataset from {DATASET_PATH}...")
try:
    df = pd.read_csv(DATASET_PATH)
    print(f"      Loaded {len(df):,} rows")
    print(f"      Columns: {list(df.columns)}")
except FileNotFoundError:
    print(f"\n❌ ERROR: Dataset not found at '{DATASET_PATH}'")
    print("   Place your URL dataset CSV at that path and re-run.")
    sys.exit(1)

# ── Step 2: Normalize labels ──
print(f"\n[2/5] Normalizing labels (column: '{LABEL_COLUMN}')...")

LEGITIMATE_VALUES = {'legitimate', 'benign', 'safe', 'good', '0', 'clean', 'white'}

df['is_malicious'] = df[LABEL_COLUMN].astype(str).str.lower().str.strip().apply(
    lambda x: 0 if x in LEGITIMATE_VALUES else 1
)

legit_count = (df['is_malicious'] == 0).sum()
malicious_count = (df['is_malicious'] == 1).sum()
print(f"      Legitimate: {legit_count:,}")
print(f"      Malicious:  {malicious_count:,}")

if legit_count == 0 or malicious_count == 0:
    print("\n❌ ERROR: One class has 0 samples!")
    print(f"   Unique label values in your dataset: {df[LABEL_COLUMN].unique()}")
    print("   Update LEGITIMATE_VALUES in this script to match your data.")
    sys.exit(1)

# ── Step 3: Add anchor samples (always-legit sites your model must know) ──
print(f"\n[3/5] Adding anchor legitimate samples...")
anchor_legit = pd.DataFrame({
    URL_COLUMN: [
        'https://www.google.com',
        'https://www.youtube.com',
        'https://www.microsoft.com',
        'https://www.amazon.com',
        'https://github.com',
        'https://stackoverflow.com',
        'https://www.wikipedia.org',
        'https://www.linkedin.com',
        # Your college URLs
        'https://geethashishu.in/',
        'http://atme.edu.in/',
        'https://www.atme.edu.in',
    ],
    LABEL_COLUMN: ['legitimate'] * 11,
    'is_malicious': [0] * 11
})

# Add anchor phishing samples that model must always catch
anchor_malicious = pd.DataFrame({
    URL_COLUMN: [
        'http://secure-login-update.bank-verify.zip/account?id=1',
        'http://192.168.1.1/phishing/login.html',
        'http://paypal-update-secure.xyz/verify',
        'http://microsoft-login.suspicious-domain.top/signin',
        'http://bit.ly/suslink123',
        'http://login.update-microsoft-secure.top',
    ],
    LABEL_COLUMN: ['phishing'] * 6,
    'is_malicious': [1] * 6
})

df = pd.concat([df, anchor_legit, anchor_malicious], ignore_index=True)
print(f"      Added {len(anchor_legit)} anchor legit + {len(anchor_malicious)} anchor phishing samples")

# ── Step 4: Sample for memory management ──
print(f"\n[4/5] Sampling {SAMPLE_SIZE:,} rows for training...")
sample_size = min(SAMPLE_SIZE, len(df))
df_sampled = df.sample(n=sample_size, random_state=42)

# Make sure anchor samples are always included
df_anchors = pd.concat([anchor_legit, anchor_malicious])
df_sampled = pd.concat([df_sampled, df_anchors]).drop_duplicates(subset=[URL_COLUMN])

print(f"      Final training size: {len(df_sampled):,} URLs")

# ── Step 5: Train ──
print(f"\n[5/5] Training model...")
model = ThreatModel()
results = model.train(df_sampled, text_col=URL_COLUMN, label_col='is_malicious')

# ── Final Summary ──
print("\n" + "=" * 60)
print("   TRAINING COMPLETE")
print("=" * 60)
print(f"  Accuracy:        {results['accuracy']*100:.1f}%")
print(f"  True Legitimate: {results['true_legit']}")
print(f"  False Positives: {results['false_positives']}  ← good URLs wrongly flagged")
print(f"  False Negatives: {results['false_negatives']}  ← bad URLs missed")
print(f"  True Malicious:  {results['true_malicious']}")
print(f"\n  Model saved to: ml/saved_models/threat_pipeline.joblib")
print("\n   Restart your FastAPI backend to use the new model!")
