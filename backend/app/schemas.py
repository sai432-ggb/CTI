from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class URLRequest(BaseModel):
    url: str

class ReportRequest(BaseModel):
    report: str

class IPRequest(BaseModel):
    ip: str

class DeviceRequest(BaseModel):
    os: str
    lastSeen: Optional[str] = None
    openPorts: Optional[str] = None
    software: Optional[str] = None

class AnalysisResult(BaseModel):
    target: str
    analysis_type: str
    result_data: Dict[str, Any]
    
class HistoryResponse(AnalysisResult):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True