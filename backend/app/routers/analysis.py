from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import URLRequest
from app.services.wireshark_analyzer import WiresharkAnalyzer
from app.services.ai_analyzer import CTIAnalyzer
from ml.model import ThreatModel
from ml.dataset import DatasetManager



import os
import shutil

router = APIRouter(prefix="/analyze", tags=["Analysis"])
ml_model = ThreatModel()
dataset_manager = DatasetManager()

# Add this at the top of your analysis function
WHITELIST = ["atme.edu.in", "geethashishu.in", "google.com", "microsoft.com"]

@router.post("/url")
async def analyze_url(req: URLRequest, db: Session = Depends(get_db)):
    try:
        # Check if the domain is in our safe list
        if any(domain in req.url.lower() for domain in WHITELIST):
            result = {
                "is_malicious": False,
                "confidence": 1.0,
                "reason": "Trusted domain (Whitelist)"
            }
        else:
            # If not whitelisted, then ask the AI
            result = ml_model.predict(req.url)
        return {"target": req.url, "analysis_type": "url", "result_data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/pcap")
async def analyze_pcap(file: UploadFile = File(...)):
    temp_file = f"temp_{file.filename}"
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    results = WiresharkAnalyzer.analyze_pcap(temp_file)
    os.remove(temp_file)
    
    return {"target": file.filename, "analysis_type": "pcap", "result_data": {"packets": results}}

@router.post("/train")
async def train_model(file: UploadFile = File(...)):
    """Endpoint to upload a new dataset and retrain the model."""
    content = await file.read()
    filepath = dataset_manager.save_uploaded_data(content, file.filename)
    df = dataset_manager.load_dataset(filepath)
    
    metrics = ml_model.train(df)
    return {"status": "Model retrained successfully", "metrics": metrics}