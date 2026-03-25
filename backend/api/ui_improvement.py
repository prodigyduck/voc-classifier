from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from backend.database.db import get_db
from backend.models.models import UIImprovement, VOCTracking
from backend.models.schemas import UIImprovementCreate, UIImprovement as UIImprovementSchema, VOCTrackingCreate, ReductionAnalysisResponse

router = APIRouter()


@router.get("/", response_model=List[UIImprovementSchema])
def get_ui_improvements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(UIImprovement)
    if status:
        query = query.filter(UIImprovement.status == status)
    improvements = query.offset(skip).limit(limit).all()
    return improvements


@router.get("/{improvement_id}", response_model=UIImprovementSchema)
def get_ui_improvement(improvement_id: int, db: Session = Depends(get_db)):
    improvement = db.query(UIImprovement).filter(UIImprovement.id == improvement_id).first()
    if not improvement:
        raise HTTPException(status_code=404, detail="UI improvement not found")
    return improvement


@router.post("/", response_model=UIImprovementSchema, status_code=201)
def create_ui_improvement(improvement: UIImprovementCreate, db: Session = Depends(get_db)):
    db_improvement = UIImprovement(**improvement.dict())
    db.add(db_improvement)
    db.commit()
    db.refresh(db_improvement)
    return db_improvement


@router.post("/{improvement_id}/track", response_model=ReductionAnalysisResponse)
def track_voc_reduction(improvement_id: int, tracking: VOCTrackingCreate, db: Session = Depends(get_db)):
    improvement = db.query(UIImprovement).filter(UIImprovement.id == improvement_id).first()
    if not improvement:
        raise HTTPException(status_code=404, detail="UI improvement not found")

    tracking_data = tracking.dict()
    tracking_data["ui_improvement_id"] = improvement_id

    db_tracking = VOCTracking(**tracking_data)
    db.add(db_tracking)
    db.commit()
    db.refresh(db_tracking)

    reduction_rate = 0.0
    if db_tracking.voc_count_after:
        if db_tracking.voc_count_before > 0:
            reduction_rate = (db_tracking.voc_count_before - db_tracking.voc_count_after) / db_tracking.voc_count_before

    db_tracking.reduction_rate = reduction_rate
    db.commit()

    return ReductionAnalysisResponse(
        ui_improvement=improvement,
        before_count=db_tracking.voc_count_before,
        after_count=db_tracking.voc_count_after,
        reduction_rate=float(reduction_rate),
        reduction_percentage=float(reduction_rate * 100)
    )


@router.put("/{improvement_id}/complete")
def complete_ui_improvement(improvement_id: int, db: Session = Depends(get_db)):
    improvement = db.query(UIImprovement).filter(UIImprovement.id == improvement_id).first()
    if not improvement:
        raise HTTPException(status_code=404, detail="UI improvement not found")

    improvement.status = "COMPLETED"
    db.commit()
    db.refresh(improvement)
    return improvement
