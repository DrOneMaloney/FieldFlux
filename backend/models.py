from datetime import date
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class FieldBase(SQLModel):
    name: str
    location: Optional[str] = None


class Field(FieldBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    events: list["ApplicationEvent"] = Relationship(back_populates="field")


class FieldCreate(FieldBase):
    pass


class FieldRead(FieldBase):
    id: int


class ApplicationEventBase(SQLModel):
    date: date
    product: str
    rate: float
    operator: str
    notes: Optional[str] = None


class ApplicationEvent(ApplicationEventBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    field_id: int = Field(foreign_key="field.id")

    field: Optional[Field] = Relationship(back_populates="events")


class ApplicationEventCreate(ApplicationEventBase):
    field_id: Optional[int] = None


class ApplicationEventRead(ApplicationEventBase):
    id: int
    field_id: int


class ApplicationEventSummary(SQLModel):
    season: int
    product: str
    total_rate: float
    event_count: int
