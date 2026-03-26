from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from backend.database.db import get_db
from backend.models.models import VOC, Category
from backend.models.schemas import AnalyticsResponse

router = APIRouter()


@router.get("/overview", response_model=AnalyticsResponse)
def get_analytics_overview(db: Session = Depends(get_db)):
    total_vocs = db.query(func.count(VOC.id)).scalar()

    by_category = db.query(
        Category.name,
        func.count(VOC.id).label("count")
    ).outerjoin(VOC, VOC.category_id == Category.id).group_by(Category.name).all()
    by_category_dict = {row[0]: row[1] for row in by_category}

    by_status = db.query(
        VOC.status,
        func.count(VOC.id).label("count")
    ).group_by(VOC.status).all()
    by_status_dict = {row[0]: row[1] for row in by_status}

    by_priority = db.query(
        VOC.priority,
        func.count(VOC.id).label("count")
    ).group_by(VOC.priority).all()
    by_priority_dict = {row[0]: row[1] for row in by_priority}

    ui_related_count = db.query(func.count(VOC.id)).filter(VOC.ui_related == True).scalar()

    monthly_trend = db.query(
        func.date_trunc('month', VOC.created_at).label("month"),
        func.count(VOC.id).label("count")
    ).group_by(func.date_trunc('month', VOC.created_at)).order_by(func.date_trunc('month', VOC.created_at)).limit(12).all()
    monthly_trend_dict = [{"month": str(row[0]), "count": row[1]} for row in monthly_trend]

    category_trend = db.query(
        func.date_trunc('month', VOC.created_at).label("month"),
        Category.name.label("category"),
        func.count(VOC.id).label("count")
    ).join(Category, VOC.category_id == Category.id).group_by(
        func.date_trunc('month', VOC.created_at),
        Category.name
    ).order_by(func.date_trunc('month', VOC.created_at), Category.name).limit(84).all()

    category_trend_dict = {}
    for row in category_trend:
        month_str = str(row[0])
        if month_str not in category_trend_dict:
            category_trend_dict[month_str] = {}
        category_trend_dict[month_str][row[1]] = row[2]

    return AnalyticsResponse(
        total_vocs=total_vocs,
        by_category=by_category_dict,
        by_status=by_status_dict,
        by_priority=by_priority_dict,
        ui_related_count=ui_related_count,
        monthly_trend=monthly_trend_dict,
        category_trend=category_trend_dict
    )
