from sqlalchemy import Column, Integer, String, Float, Enum, JSON
from sqlalchemy.orm import relationship
import enum
from backend.database import Base


class DifficultyEnum(int, enum.Enum):
    easy = 1
    medium = 2
    hard = 3


class PlatformEnum(str, enum.Enum):
    codeforces = "codeforces"
    leetcode = "leetcode"
    codechef = "codechef"


class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(Enum(PlatformEnum), nullable=False, index=True)
    platform_problem_id = Column(String, nullable=False, index=True)  # CF: "1234A", LC: "two-sum"
    slug = Column(String, nullable=False, index=True)                  # canonical slug
    title = Column(String, nullable=False)
    difficulty = Column(Integer, nullable=True)                        # 1=easy, 2=medium, 3=hard
    tags = Column(JSON, default=list)                                  # ["dp", "graphs", ...]
    url = Column(String, nullable=True)
    cf_rating = Column(Integer, nullable=True)                         # original CF numeric rating

    # Relationships
    submissions = relationship("Submission", back_populates="problem")
