from enum import Enum as PyEnum
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, Enum
from datetime import datetime

class MetricType(str, PyEnum):
    COUNT = "count"
    DURATION = "duration"
    PERCENTAGE = "percentage"
    
class MetricsBase(SQLModel):
    name: str = Field(primary_key=True, unique=True)
    value: float = Field()
    type: MetricType = Field(default=MetricType.COUNT, sa_column=Column(Enum(MetricType)))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class MetricsCreate(MetricsBase):
    name: str
    value: float
    type: MetricType = Field(default=MetricType.COUNT)
    
class Metrics(MetricsBase, table=True):
    __tablename__ = "metrics"