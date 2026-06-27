from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base

class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    duration_days = Column(Integer, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Store the exact JSON response from the AI
    plan_data = Column(String, nullable=False)
    
    user = relationship("User", back_populates="study_plans")
