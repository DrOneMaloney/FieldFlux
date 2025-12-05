from __future__ import annotations

import enum
from datetime import datetime, date
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


class InvoiceStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    partial = "partial"
    paid = "paid"
    overdue = "overdue"


class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)

    fields = relationship("Field", back_populates="farmer", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="farmer", cascade="all, delete-orphan")


class Field(Base):
    __tablename__ = "fields"
    __table_args__ = (UniqueConstraint("name", "farmer_id", name="uq_field_farm"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    acreage = Column(Float, nullable=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False)

    farmer = relationship("Farmer", back_populates="fields")
    invoices = relationship("Invoice", back_populates="field")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="SET NULL"), nullable=True)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.draft, nullable=False)
    issue_date = Column(Date, default=date.today, nullable=False)
    due_date = Column(Date, nullable=True)
    subtotal = Column(Numeric(10, 2), default=0)
    tax_rate = Column(Float, default=0.0)
    discount_rate = Column(Float, default=0.0)
    total = Column(Numeric(10, 2), default=0)
    notes = Column(Text, nullable=True)

    farmer = relationship("Farmer", back_populates="invoices")
    field = relationship("Field", back_populates="invoices")
    line_items = relationship(
        "LineItem", back_populates="invoice", cascade="all, delete-orphan", order_by="LineItem.position"
    )
    payments = relationship(
        "PaymentRecord", back_populates="invoice", cascade="all, delete-orphan", order_by="PaymentRecord.date"
    )

    def outstanding_balance(self) -> float:
        paid_total = sum((payment.amount for payment in self.payments), 0.0)
        return float(self.total) - float(paid_total)


class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    description = Column(String, nullable=False)
    quantity = Column(Float, default=1.0)
    unit_price = Column(Float, default=0.0)
    tax_rate = Column(Float, default=0.0)
    position = Column(Integer, default=0)
    billable_reference = Column(String, nullable=True)

    invoice = relationship("Invoice", back_populates="line_items")

    def line_total(self) -> float:
        base = self.quantity * self.unit_price
        return base + base * self.tax_rate


class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    method = Column(String, nullable=True)
    reference = Column(String, nullable=True)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True)

    invoice = relationship("Invoice", back_populates="payments")
