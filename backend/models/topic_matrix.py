from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base


class TopicMatrix(Base):
    __tablename__ = "topic_matrix"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    topic = Column(String, nullable=False, index=True)
    solved_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    avg_difficulty = Column(Float, default=0.0)
    last_practiced_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="topic_matrices")


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    weak_topics = Column(String, nullable=True)       # JSON array stored as string
    strength_topics = Column(String, nullable=True)   # JSON array stored as string
    suggested_problems = Column(String, nullable=True)  # JSON stored as string
    study_hints = Column(String, nullable=True)         # JSON stored as string
    weekly_goal = Column(String, nullable=True)
    raw_response = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="ai_recommendations")
