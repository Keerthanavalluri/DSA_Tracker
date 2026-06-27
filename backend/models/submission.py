from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from backend.database import Base


class VerdictEnum(str, enum.Enum):
    AC = "AC"            # Accepted
    WA = "WA"            # Wrong Answer
    TLE = "TLE"          # Time Limit Exceeded
    MLE = "MLE"          # Memory Limit Exceeded
    RE = "RE"            # Runtime Error
    CE = "CE"            # Compilation Error
    PARTIAL = "PARTIAL"  # Partial (CodeChef)
    SKIPPED = "SKIPPED"  # Skipped
    OTHER = "OTHER"


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)
    platform_submission_id = Column(String, nullable=True, index=True)  # original platform ID (for dedup)
    status = Column(Enum(VerdictEnum), nullable=False, default=VerdictEnum.OTHER)
    language = Column(String, nullable=True)
    time_ms = Column(Integer, nullable=True)
    memory_kb = Column(Integer, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="submissions")
    problem = relationship("Problem", back_populates="submissions")
