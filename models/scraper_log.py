from enum import Enum as PyEnum
from datetime import datetime
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, Enum, Float, Computed, Integer

class ScraperStatus(str, PyEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ScraperLogBase(SQLModel):
    id: int = Field(sa_column=Column(Integer, primary_key=True, autoincrement=True))
    status: ScraperStatus =  Field(default=ScraperStatus.RUNNING, sa_column=Column(Enum(ScraperStatus)))
    scraper: str = Field(max_length=255)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: datetime | None = Field(default=None)
    duration: float | None = Field(
    sa_column=Column(
        Float,
        Computed(
            "EXTRACT(EPOCH FROM (end_time - start_time))"
            )
        )
    )

class ScraperLogCreate(SQLModel):
    scraper: str

class ScraperLog(ScraperLogBase, table=True):
    __tablename__ = "scraper_logs"