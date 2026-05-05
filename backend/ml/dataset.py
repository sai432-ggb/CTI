import pandas as pd
import json
from pathlib import Path

class DatasetManager:
    def __init__(self, storage_dir: str = "data/uploads/"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def load_dataset(self, file_path: str) -> pd.DataFrame:
        """Loads dataset from CSV or JSON."""
        if file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        elif file_path.endswith('.json'):
            return pd.read_json(file_path)
        raise ValueError("Unsupported file format. Use CSV or JSON.")

    def save_uploaded_data(self, content: bytes, filename: str) -> str:
        """Saves uploaded dataset for retraining."""
        file_path = self.storage_dir / filename
        with open(file_path, "wb") as f:
            f.write(content)
        return str(file_path)