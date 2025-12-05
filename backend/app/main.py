from __future__ import annotations

from datetime import date
from io import BytesIO
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fpdf import FPDF
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FieldFlux Billing")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _calculate_totals(invoice: models.Invoice):
    subtotal = sum(item.quantity * item.unit_price for item in invoice.line_items)
    tax_amount = subtotal * (invoice.tax_rate or 0)
    discount_amount = subtotal * (invoice.discount_rate or 0)
    invoice.subtotal = round(subtotal, 2)
    invoice.total = round(subtotal + tax_amount - discount_amount, 2)

    if invoice.status == models.InvoiceStatus.sent and invoice.due_date and invoice.due_date < date.today():
        invoice.status = models.InvoiceStatus.overdue


@app.post("/farmers", response_model=schemas.FarmerOut)
def create_farmer(farmer: schemas.FarmerCreate, db: Session = Depends(get_db)):
    farmer_obj = models.Farmer(**farmer.dict())
    db.add(farmer_obj)
    db.commit()
    db.refresh(farmer_obj)
    return farmer_obj


@app.post("/fields", response_model=schemas.FieldOut)
def create_field(field: schemas.FieldCreate, db: Session = Depends(get_db)):
    if not db.get(models.Farmer, field.farmer_id):
        raise HTTPException(status_code=404, detail="Farmer not found")
    field_obj = models.Field(**field.dict())
    db.add(field_obj)
    db.commit()
    db.refresh(field_obj)
    return field_obj


def _hydrate_billable_line_items(field_applications: List[str], start_position: int = 0):
    line_items = []
    for index, entry in enumerate(field_applications, start=start_position):
        line_items.append(
            models.LineItem(
                description=f"Field application - {entry}",
                quantity=1,
                unit_price=0.0,
                position=index,
                tax_rate=0.0,
                billable_reference=entry,
            )
        )
    return line_items


@app.post("/invoices", response_model=schemas.InvoiceOut)
def create_invoice(invoice: schemas.InvoiceCreate, db: Session = Depends(get_db)):
    farmer = db.get(models.Farmer, invoice.farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    if invoice.field_id and not db.get(models.Field, invoice.field_id):
        raise HTTPException(status_code=404, detail="Field not found")

    invoice_obj = models.Invoice(
        farmer_id=invoice.farmer_id,
        field_id=invoice.field_id,
        status=invoice.status,
        issue_date=invoice.issue_date or date.today(),
        due_date=invoice.due_date,
        tax_rate=invoice.tax_rate,
        discount_rate=invoice.discount_rate,
        notes=invoice.notes,
    )

    for position, item in enumerate(invoice.line_items):
        invoice_obj.line_items.append(
            models.LineItem(
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                tax_rate=item.tax_rate,
                position=position,
                billable_reference=item.billable_reference,
            )
        )

    if invoice.field_applications:
        auto_items = _hydrate_billable_line_items(invoice.field_applications, start_position=len(invoice_obj.line_items))
        invoice_obj.line_items.extend(auto_items)

    _calculate_totals(invoice_obj)
    db.add(invoice_obj)
    db.commit()
    db.refresh(invoice_obj)
    return invoice_obj


@app.get("/invoices", response_model=List[schemas.InvoiceOut])
def list_invoices(db: Session = Depends(get_db)):
    invoices = db.query(models.Invoice).all()
    for inv in invoices:
        _calculate_totals(inv)
    return invoices


@app.get("/invoices/{invoice_id}", response_model=schemas.InvoiceOut)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.get(models.Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    _calculate_totals(invoice)
    return invoice


@app.patch("/invoices/{invoice_id}/status", response_model=schemas.InvoiceOut)
def update_invoice_status(invoice_id: int, status_update: schemas.InvoiceStatusUpdate, db: Session = Depends(get_db)):
    invoice = db.get(models.Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice.status = status_update.status
    _calculate_totals(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@app.post("/invoices/{invoice_id}/payments", response_model=schemas.InvoiceOut)
def record_payment(invoice_id: int, payment: schemas.PaymentCreate, db: Session = Depends(get_db)):
    invoice = db.get(models.Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    payment_obj = models.PaymentRecord(
        invoice_id=invoice_id,
        amount=payment.amount,
        method=payment.method,
        reference=payment.reference,
        notes=payment.notes,
    )
    db.add(payment_obj)
    db.flush()

    remaining = invoice.outstanding_balance()
    if payment.amount >= remaining:
        invoice.status = models.InvoiceStatus.paid
    else:
        invoice.status = models.InvoiceStatus.partial

    _calculate_totals(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@app.get("/farmers/{farmer_id}/balance")
def farmer_balance(farmer_id: int, db: Session = Depends(get_db)):
    farmer = db.get(models.Farmer, farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    total_due = 0.0
    for invoice in farmer.invoices:
        _calculate_totals(invoice)
        total_due += invoice.outstanding_balance()
    return {"farmer_id": farmer_id, "outstanding_balance": round(total_due, 2)}


def _invoice_html(invoice: models.Invoice) -> str:
    _calculate_totals(invoice)
    items_html = "".join(
        f"<tr><td>{item.description}</td><td>{item.quantity}</td><td>${item.unit_price:.2f}</td><td>${item.line_total():.2f}</td></tr>"
        for item in invoice.line_items
    )
    payments_html = "".join(
        f"<li>{payment.date.date()} - ${payment.amount:.2f} via {payment.method or 'N/A'}</li>"
        for payment in invoice.payments
    )
    return f"""
    <html>
        <head><title>Invoice #{invoice.id}</title></head>
        <body>
            <h1>Invoice #{invoice.id}</h1>
            <p>Status: {invoice.status.value.title()}</p>
            <p>Farmer: {invoice.farmer.name} ({invoice.farmer.email or 'no email'})</p>
            <p>Field: {invoice.field.name if invoice.field else 'N/A'}</p>
            <p>Issue Date: {invoice.issue_date} | Due: {invoice.due_date or 'N/A'}</p>
            <table border="1" cellspacing="0" cellpadding="4">
                <tr><th>Description</th><th>Qty</th><th>Unit Price</th><th>Total</th></tr>
                {items_html}
            </table>
            <p>Subtotal: ${invoice.subtotal:.2f}</p>
            <p>Tax Rate: {invoice.tax_rate * 100:.1f}% | Discount: {invoice.discount_rate * 100:.1f}%</p>
            <p><strong>Amount Due: ${invoice.total:.2f}</strong></p>
            <p>Payments:</p>
            <ul>{payments_html or '<li>No payments yet</li>'}</ul>
            <p>Notes: {invoice.notes or 'None'}</p>
        </body>
    </html>
    """


@app.get("/invoices/{invoice_id}/html", response_class=HTMLResponse)
def invoice_html(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.get(models.Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return HTMLResponse(content=_invoice_html(invoice))


@app.get("/invoices/{invoice_id}/pdf")
def invoice_pdf(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.get(models.Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(40, 10, f"Invoice #{invoice.id}")
    pdf.ln(12)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Farmer: {invoice.farmer.name}", ln=True)
    pdf.cell(0, 10, f"Field: {invoice.field.name if invoice.field else 'N/A'}", ln=True)
    pdf.cell(0, 10, f"Status: {invoice.status.value}", ln=True)

    pdf.ln(5)
    for item in invoice.line_items:
        pdf.cell(0, 8, f"- {item.description} ({item.quantity} @ ${item.unit_price:.2f})", ln=True)
    pdf.ln(3)
    pdf.cell(0, 8, f"Subtotal: ${invoice.subtotal:.2f}", ln=True)
    pdf.cell(0, 8, f"Tax: {invoice.tax_rate*100:.1f}% | Discount: {invoice.discount_rate*100:.1f}%", ln=True)
    pdf.cell(0, 8, f"Total Due: ${invoice.total:.2f}", ln=True)

    buffer = BytesIO(pdf.output(dest="S").encode("latin-1"))
    headers = {"Content-Disposition": f"inline; filename=invoice-{invoice.id}.pdf"}
    return StreamingResponse(buffer, media_type="application/pdf", headers=headers)
