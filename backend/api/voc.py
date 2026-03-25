from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func
from backend.database.db import get_db
from backend.models.models import VOC
from backend.models.schemas import VOCCreate, VOCUpdate, VOC as VOCSchema
from backend.services.notification import NotificationService

router = APIRouter()
notification_service = NotificationService()


@router.get("/", response_model=List[VOCSchema])
def get_vocs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    ui_related: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(VOC)

    if category_id:
        query = query.filter(VOC.category_id == category_id)
    if status:
        query = query.filter(VOC.status == status)
    if priority:
        query = query.filter(VOC.priority == priority)
    if ui_related is not None:
        query = query.filter(VOC.ui_related == ui_related)

    vocs = query.order_by(VOC.created_at.desc()).offset(skip).limit(limit).all()
    return vocs


@router.get("/{voc_id}", response_model=VOCSchema)
def get_voc(voc_id: int, db: Session = Depends(get_db)):
    voc = db.query(VOC).filter(VOC.id == voc_id).first()
    if not voc:
        raise HTTPException(status_code=404, detail="VOC not found")
    return voc


@router.post("/", response_model=VOCSchema, status_code=201)
def create_voc(voc: VOCCreate, db: Session = Depends(get_db)):
    db_voc = VOC(**voc.dict())
    db.add(db_voc)
    db.commit()
    db.refresh(db_voc)

    notification_service.notify_new_voc(db_voc.id, db_voc.title, db_voc.priority)
    notification_service.notify_high_priority_voc(db_voc.id, db_voc.title, db_voc.priority)

    return db_voc


@router.put("/{voc_id}", response_model=VOCSchema)
def update_voc(voc_id: int, voc_update: VOCUpdate, db: Session = Depends(get_db)):
    voc = db.query(VOC).filter(VOC.id == voc_id).first()
    if not voc:
        raise HTTPException(status_code=404, detail="VOC not found")

    update_data = voc_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(voc, key, value)

    db.commit()
    db.refresh(voc)
    return voc


@router.delete("/{voc_id}")
def delete_voc(voc_id: int, db: Session = Depends(get_db)):
    voc = db.query(VOC).filter(VOC.id == voc_id).first()
    if not voc:
        raise HTTPException(status_code=404, detail="VOC not found")

    db.delete(voc)
    db.commit()
    return {"message": "VOC deleted successfully"}


@router.post("/{voc_id}/resolve")
def resolve_voc(voc_id: int, db: Session = Depends(get_db)):
    voc = db.query(VOC).filter(VOC.id == voc_id).first()
    if not voc:
        raise HTTPException(status_code=404, detail="VOC not found")

    voc.status = "RESOLVED"
    voc.resolved_at = func.now()
    db.commit()
    db.refresh(voc)

    notification_service.notify_voc_resolved(voc.id, voc.title)

    return voc
