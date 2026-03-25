from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from backend.database.db import get_db
from backend.models.models import UIImprovement, VOCTracking, Category
from backend.models.schemas import UIImprovementCreate, UIImprovement as UIImprovementSchema, VOCTrackingCreate, ReductionAnalysisResponse, ImprovementReductionData, ImprovementAnalyticsResponse
from backend.services.notification import NotificationService

router = APIRouter()
notification_service = NotificationService()


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
    improvement.completed_at = func.now()
    db.commit()
    db.refresh(improvement)

    tracking_records = db.query(VOCTracking).filter(
        VOCTracking.ui_improvement_id == improvement_id
    ).order_by(VOCTracking.tracking_date.desc()).first()

    if tracking_records and tracking_records.reduction_rate:
        notification_service.notify_ui_improvement_completed(
            improvement.id,
            improvement.name,
            float(tracking_records.reduction_rate)
        )

    return improvement


@router.get("/analytics/overview", response_model=ImprovementAnalyticsResponse)
def get_improvement_analytics(db: Session = Depends(get_db)):
    improvements = db.query(UIImprovement).all()

    total = len(improvements)
    completed = len([imp for imp in improvements if imp.status == "COMPLETED"])

    reductions = []
    category_stats = {}

    for imp in improvements:
        tracking_records = db.query(VOCTracking).filter(
            VOCTracking.ui_improvement_id == imp.id
        ).order_by(VOCTracking.tracking_date.desc()).first()

        before_count = 0
        after_count = 0
        reduction_rate = 0.0
        category_name = None

        if tracking_records:
            before_count = tracking_records.voc_count_before
            after_count = tracking_records.voc_count_after or 0
            reduction_rate = float(tracking_records.reduction_rate) if tracking_records.reduction_rate else 0.0

            if imp.related_categories and len(imp.related_categories) > 0:
                category = db.query(Category).filter(Category.id == imp.related_categories[0]).first()
                if category:
                    category_name = category.name
                    if category_name not in category_stats:
                        category_stats[category_name] = []
                    category_stats[category_name].append(reduction_rate)

        reductions.append(ImprovementReductionData(
            improvement_id=imp.id,
            improvement_name=imp.name,
            before_count=before_count,
            after_count=after_count,
            reduction_rate=reduction_rate,
            reduction_percentage=reduction_rate * 100,
            category_name=category_name
        ))

    avg_reduction = 0.0
    if reductions:
        avg_reduction = sum(r.reduction_rate for r in reductions) / len(reductions)

    avg_by_category = {}
    for cat_name, rates in category_stats.items():
        if rates:
            avg_by_category[cat_name] = sum(rates) / len(rates)

    return ImprovementAnalyticsResponse(
        total_improvements=total,
        completed_improvements=completed,
        average_reduction_rate=avg_reduction,
        reductions=reductions,
        by_category=avg_by_category
    )
