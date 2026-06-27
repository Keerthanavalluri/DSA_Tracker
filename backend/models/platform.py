from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from backend.database import Base


class PlatformEnum(str, enum.Enum):
    codeforces = "codeforces"
    leetcode = "leetcode"
    codechef = "codechef"


class PlatformAccount(Base):
    __tablename__ = "platform_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    platform = Column(Enum(PlatformEnum), nullable=False)
    handle = Column(String, nullable=False)
    cookies_json = Column(Text, nullable=True)  # For LC session cookies
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="platform_accounts")
