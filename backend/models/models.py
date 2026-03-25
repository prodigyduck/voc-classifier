from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, DECIMAL, ForeignKey, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.database.db import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    is_ai_generated = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    vocs = relationship("VOC", back_populates="category")
    ai_suggested_vocs = relationship("VOC", foreign_keys="VOC.ai_suggested_category_id", back_populates="ai_suggested_category")


class VOC(Base):
    __tablename__ = "vocs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    ai_suggested_category_id = Column(Integer, ForeignKey("categories.id"))
    confidence_score = Column(DECIMAL(5, 4))
    status = Column(String(50), default="PENDING")
    priority = Column(String(20), default="MEDIUM")
    submitted_by = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True))
    ui_related = Column(Boolean, default=False)
    ui_improvement_action = Column(Text)

    category = relationship("Category", foreign_keys=[category_id], back_populates="vocs")
    ai_suggested_category = relationship("Category", foreign_keys=[ai_suggested_category_id], back_populates="ai_suggested_vocs")
    topic_results = relationship("TopicResult", back_populates="voc")
    tracking_records = relationship("VOCTracking", back_populates="voc")


class UIImprovement(Base):
    __tablename__ = "ui_improvements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    related_categories = Column(ARRAY(Integer))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    status = Column(String(50), default="IN_PROGRESS")

    tracking_records = relationship("VOCTracking", back_populates="ui_improvement")


class VOCTracking(Base):
    __tablename__ = "voc_tracking"

    id = Column(Integer, primary_key=True, index=True)
    ui_improvement_id = Column(Integer, ForeignKey("ui_improvements.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    voc_id = Column(Integer, ForeignKey("vocs.id"))
    voc_count_before = Column(Integer, nullable=False)
    voc_count_after = Column(Integer)
    reduction_rate = Column(DECIMAL(5, 4))
    tracking_date = Column(DateTime(timezone=True), server_default=func.now())

    ui_improvement = relationship("UIImprovement", back_populates="tracking_records")
    category = relationship("Category")
    voc = relationship("VOC", back_populates="tracking_records")


class TopicResult(Base):
    __tablename__ = "topic_results"

    id = Column(Integer, primary_key=True, index=True)
    voc_id = Column(Integer, ForeignKey("vocs.id"))
    topic_id = Column(Integer)
    topic_name = Column(Text)
    probability = Column(DECIMAL(5, 4))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    voc = relationship("VOC", back_populates="topic_results")
