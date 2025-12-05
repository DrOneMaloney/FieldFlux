from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, validator
from pydantic import Field as PydanticField

from .models import InvoiceStatus


class FarmerCreate(BaseModel):
    name: str
    email: Optional[str] = None


class FarmerOut(FarmerCreate):
    id: int

    class Config:
        orm_mode = True


class FieldCreate(BaseModel):
    name: str
    acreage: Optional[float] = None
    farmer_id: int


class FieldOut(FieldCreate):
    id: int

    class Config:
        orm_mode = True


class LineItemBase(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    tax_rate: float = 0.0
    billable_reference: Optional[str] = None
    position: int = 0

    @validator("quantity", "unit_price", pre=True)
    def ensure_positive(cls, value):
        return float(value)


class LineItemCreate(LineItemBase):
    pass


class LineItemOut(LineItemBase):
    id: int
    line_total: float = PydanticField(..., alias="line_total")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class PaymentCreate(BaseModel):
    amount: float
    method: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


class PaymentOut(PaymentCreate):
    id: int
    date: datetime

    class Config:
        orm_mode = True


class InvoiceCreate(BaseModel):
    farmer_id: int
    field_id: Optional[int] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    status: InvoiceStatus = InvoiceStatus.draft
    tax_rate: float = 0.0
    discount_rate: float = 0.0
    notes: Optional[str] = None
    line_items: List[LineItemCreate] = []
    field_applications: List[str] = []


class InvoiceStatusUpdate(BaseModel):
    status: InvoiceStatus


class InvoiceOut(BaseModel):
    id: int
    farmer: FarmerOut
    field: Optional[FieldOut]
    status: InvoiceStatus
    issue_date: date
    due_date: Optional[date]
    subtotal: float
    tax_rate: float
    discount_rate: float
    total: float
    notes: Optional[str]
    line_items: List[LineItemOut]
    payments: List[PaymentOut]
    outstanding_balance: float = PydanticField(..., alias="outstanding_balance")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
