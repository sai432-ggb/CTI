from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import URLRequest, ReportRequest, IPRequest, DeviceRequest
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
WHITELIST = [
    "atme.edu.in", 
    "geethashishu.in", 
    "google.com", 
    "microsoft.com",
    "web.whatsapp.com",
    "whatsapp.com",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "linkedin.com",
    "youtube.com",
    "github.com"
]

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
            try:
                result = ml_model.predict(req.url)
            except Exception as model_error:
                # Fallback if model fails
                print(f"Model prediction failed for URL {req.url}: {str(model_error)}")
                result = {
                    "is_malicious": False,
                    "confidence": 0.5,
                    "reason": "Model unavailable - using fallback analysis"
                }
        return {"target": req.url, "analysis_type": "url", "result_data": result}
    except Exception as e:
        print(f"URL analysis failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"URL analysis failed: {str(e)}")

@router.post("/report")
async def analyze_report(req: ReportRequest):
    try:
        print(f"Processing CTI report: {req.report[:100]}...")
        analysis = await CTIAnalyzer.analyze_report(req.report)
        
        if isinstance(analysis, dict) and analysis.get("error"):
            print(f"CTI analysis returned error: {analysis['error']}")
            result_data = {
                "is_malicious": False,
                "confidence": 0.0,
                "reason": analysis["error"],
                "ips": [],
                "domains": [],
                "ttps": [],
                "summary": analysis.get("summary", "Analysis failed")
            }
        else:
            result_data = {
                "is_malicious": bool(analysis.get("ips") or analysis.get("domains") or analysis.get("ttps")),
                "confidence": 0.75,
                "reason": analysis.get("summary", "CTI analysis completed."),
                "ips": analysis.get("ips", []),
                "domains": analysis.get("domains", []),
                "ttps": analysis.get("ttps", []),
                "summary": analysis.get("summary", "Analysis completed")
            }
        
        response = {"target": req.report[:200], "analysis_type": "cti", "result_data": result_data}
        print(f"CTI response: {response}")
        return response
        
    except Exception as e:
        print(f"Report analysis failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Report analysis failed: {str(e)}")

@router.post("/ip")
async def analyze_ip(req: IPRequest):
    try:
        is_suspicious = req.ip.startswith("185.") or req.ip.endswith(".45")
        result = {
            "is_malicious": is_suspicious,
            "confidence": 0.8 if is_suspicious else 0.35,
            "reason": "Suspicious IP range or pattern detected." if is_suspicious else "No immediate risk indicators found.",
            "ip": req.ip,
        }
        return {"target": req.ip, "analysis_type": "ip", "result_data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/device")
async def analyze_device(req: DeviceRequest):
    try:
        open_ports = [port.strip() for port in (req.openPorts or "").split(",") if port.strip()]
        risky_ports = {"23", "445", "3389"}
        found_risky = any(port in risky_ports for port in open_ports)
        result = {
            "is_malicious": found_risky,
            "confidence": 0.85 if found_risky else 0.25,
            "reason": "Device posture risk detected because of insecure open ports." if found_risky else "No critical device posture issues detected.",
            "open_ports": open_ports,
            "software": req.software,
        }
        return {"target": req.os or "device", "analysis_type": "device", "result_data": result}
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