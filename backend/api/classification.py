from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database.db import get_db
from backend.models.models import VOC, TopicResult, Category
from backend.models.schemas import ClassificationResult, TopicResult as TopicResultSchema
from backend.ml.classifier import VOCClassifier

router = APIRouter()

classifier = VOCClassifier()


@router.post("/train")
def train_classifier(db: Session = Depends(get_db)):
    vocs = db.query(VOC).filter(VOC.status == "PENDING").all()

    if not vocs:
        raise HTTPException(status_code=400, detail="No VOCs to train on")

    documents = [f"{voc.title}. {voc.content}" for voc in vocs]

    try:
        topics, probs = classifier.fit(documents)
        return {"message": f"Model trained on {len(documents)} documents", "topics": len(set(topics))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.post("/classify/{voc_id}", response_model=ClassificationResult)
def classify_voc(voc_id: int, db: Session = Depends(get_db)):
    voc = db.query(VOC).filter(VOC.id == voc_id).first()
    if not voc:
        raise HTTPException(status_code=404, detail="VOC not found")

    result = classifier.classify_voc(voc.title, voc.content)

    category = db.query(Category).filter(Category.name == result["category"]).first()
    category_id = category.id if category else None

    voc.ai_suggested_category_id = category_id
    voc.confidence_score = result["confidence"]
    voc.status = "ANALYZED"
    db.commit()

    topic_result = TopicResult(
        voc_id=voc_id,
        topic_id=result["topic_id"],
        topic_name=result["category"],
        probability=result["confidence"]
    )
    db.add(topic_result)
    db.commit()

    return ClassificationResult(
        voc_id=voc_id,
        suggested_category=result["category"],
        suggested_category_id=category_id,
        confidence_score=result["confidence"],
        topic_results=[
            TopicResultSchema(
                voc_id=voc_id,
                topic_id=result["topic_id"],
                topic_name=result["category"],
                probability=result["confidence"]
            )
        ]
    )


@router.post("/classify-batch")
def classify_batch(
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    vocs = db.query(VOC).filter(VOC.status == "PENDING").limit(limit).all()

    if not vocs:
        raise HTTPException(status_code=400, detail="No pending VOCs to classify")

    voc_data = [{"id": voc.id, "title": voc.title, "content": voc.content} for voc in vocs]

    try:
        results = classifier.batch_classify(voc_data)

        updated_count = 0
        for result in results:
            voc = db.query(VOC).filter(VOC.id == result["voc_id"]).first()
            if voc:
                category = db.query(Category).filter(Category.name == result["category"]).first()
                category_id = category.id if category else None

                voc.ai_suggested_category_id = category_id
                voc.confidence_score = result["confidence"]
                voc.status = "ANALYZED"

                topic_result = TopicResult(
                    voc_id=voc.id,
                    topic_id=result["topic_id"],
                    topic_name=result["category"],
                    probability=result["confidence"]
                )
                db.add(topic_result)
                updated_count += 1

        db.commit()
        return {"message": f"Classified {updated_count} VOCs successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.get("/topics")
def get_topics():
    try:
        topics = classifier.get_topic_info()
        return topics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get topics: {str(e)}")
