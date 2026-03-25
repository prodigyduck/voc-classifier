from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class CategoryBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    is_ai_generated: bool = False


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VOCBase(BaseModel):
    title: str = Field(..., max_length=500)
    content: str
    category_id: Optional[int] = None
    priority: str = "MEDIUM"
    submitted_by: Optional[str] = None


class VOCCreate(VOCBase):
    pass


class VOCUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[int] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    ui_related: Optional[bool] = None
    ui_improvement_action: Optional[str] = None


class VOC(VOCBase):
    id: int
    ai_suggested_category_id: Optional[int] = None
    confidence_score: Optional[Decimal] = None
    status: str
    submitted_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    ui_related: bool
    ui_improvement_action: Optional[str] = None
    category: Optional[Category] = None

    class Config:
        from_attributes = True


class UIImprovementBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    related_categories: Optional[List[int]] = None


class UIImprovementCreate(UIImprovementBase):
    pass


class UIImprovement(UIImprovementBase):
    id: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    status: str

    class Config:
        from_attributes = True


class VOCTrackingCreate(BaseModel):
    ui_improvement_id: int
    category_id: int
    voc_count_before: int


class VOCTracking(VOCTrackingCreate):
    id: int
    voc_count_after: Optional[int] = None
    reduction_rate: Optional[Decimal] = None
    tracking_date: datetime

    class Config:
        from_attributes = True


class TopicResult(BaseModel):
    voc_id: int
    topic_id: int
    topic_name: str
    probability: Decimal

    class Config:
        from_attributes = True


class ClassificationResult(BaseModel):
    voc_id: int
    suggested_category: Optional[str] = None
    suggested_category_id: Optional[int] = None
    confidence_score: float
    topic_results: List[TopicResult]


class AnalyticsResponse(BaseModel):
    total_vocs: int
    by_category: dict
    by_status: dict
    by_priority: dict
    ui_related_count: int
    monthly_trend: List[dict]


class ReductionAnalysisResponse(BaseModel):
    ui_improvement: UIImprovement
    before_count: int
    after_count: int
    reduction_rate: float
    reduction_percentage: float


class ImprovementReductionData(BaseModel):
    improvement_id: int
    improvement_name: str
    before_count: int
    after_count: int
    reduction_rate: float
    reduction_percentage: float
    category_name: Optional[str] = None


class ImprovementAnalyticsResponse(BaseModel):
    total_improvements: int
    completed_improvements: int
    average_reduction_rate: float
    reductions: List[ImprovementReductionData]
    by_category: dict
