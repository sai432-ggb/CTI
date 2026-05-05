import pandas as pd
from ml.model import ThreatModel
import os

os.makedirs("ml/saved_models", exist_ok=True)

print("1. Loading massive dataset...")
df = pd.read_csv("data/datasets/url_dataset.csv")

# --- STEP 2: THE TRANSLATION LAYER ---
label_col = 'type' 
url_col = 'url'     

df['is_malicious'] = df[label_col].astype(str).str.lower().apply(
    lambda x: 0 if x in ['legitimate', 'benign', '0', 'safe'] else 1
)

# --- NEW STEP: PREVENT MEMORY CRASH ---
# Let's grab a random sample of 50,000 URLs so your RAM doesn't explode.
# (If your PC has 16GB+ RAM, you can try increasing this to 100000 later)
print("Balancing data to prevent RAM overload...")
df = df.sample(n=50000, random_state=42)

print(f"Sampled data! Training on {len(df[df['is_malicious'] == 1])} bad URLs and {len(df[df['is_malicious'] == 0])} good URLs.")

# Manually add your college to the training data
college_data = pd.DataFrame({
    'url': ['https://geethashishu.in/', 'http://atme.edu.in/'],
    'type': ['legitimate', 'legitimate'],
    'is_malicious': [0, 0]
})
df = pd.concat([df, college_data], ignore_index=True)

print("3. Initializing model...")
model = ThreatModel()

print("4. Training AI with sampled data (should take 10-30 seconds)...")
results = model.train(df, text_col=url_col, label_col='is_malicious')

print(f"Training Complete! Final Accuracy: {results['accuracy']}")
print("The professional model is now saved and ready for the dashboard!")