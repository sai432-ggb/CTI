from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import AnalysisHistory
from ..schemas import HistoryResponse

router = APIRouter(prefix="/history", tags=["History"])

@router.get("/", response_model=List[HistoryResponse])
def get_analysis_history(limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve the latest analysis history."""
    history = db.query(AnalysisHistory).order_by(AnalysisHistory.created_at.desc()).limit(limit).all()
    return history

@router.post("/")
def save_history(target: str, analysis_type: str, result_data: dict, db: Session = Depends(get_db)):
    """Manually save an analysis result to history."""
    new_record = AnalysisHistory(
        target=target,
        analysis_type=analysis_type,
        result_data=result_data,
        # user_id=1 # Uncomment and link to auth user in production
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return {"status": "success", "id": new_record.id}