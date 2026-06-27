from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)  # computed on end

    # Relationships
    user = relationship("User", back_populates="study_sessions")
    heartbeats = relationship("Heartbeat", back_populates="session", cascade="all, delete-orphan")


class Heartbeat(Base):
    __tablename__ = "heartbeats"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("study_sessions.id"), nullable=False)
    pinged_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("StudySession", back_populates="heartbeats")


class Streak(Base):
    __tablename__ = "streaks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_active_date = Column(String, nullable=True)  # YYYY-MM-DD string in UTC
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="streak")
