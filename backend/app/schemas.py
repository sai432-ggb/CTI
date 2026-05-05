from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class URLRequest(BaseModel):
    url: str

class AnalysisResult(BaseModel):
    target: str
    analysis_type: str
    result_data: Dict[str, Any]
    
class HistoryResponse(AnalysisResult):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True