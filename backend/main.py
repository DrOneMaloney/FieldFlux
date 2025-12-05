from datetime import date
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from sqlmodel import Session, select, col

from .database import create_db_and_tables, get_session
from .models import (
    ApplicationEvent,
    ApplicationEventCreate,
    ApplicationEventRead,
    ApplicationEventSummary,
    Field,
    FieldCreate,
    FieldRead,
)

app = FastAPI(title="FieldFlux API")


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


def require_role(allowed_roles: list[str]):
    def verifier(role: Annotated[Optional[str], Header(None, alias="X-Role")]):
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role for this action",
            )

    return verifier


@app.post("/fields", response_model=FieldRead, dependencies=[Depends(require_role(["admin", "manager"]))])
def create_field(field: FieldCreate, session: Session = Depends(get_session)) -> Field:
    new_field = Field.from_orm(field)
    session.add(new_field)
    session.commit()
    session.refresh(new_field)
    return new_field


@app.get("/fields", response_model=list[FieldRead])
def list_fields(session: Session = Depends(get_session)) -> list[Field]:
    return session.exec(select(Field)).all()


@app.post(
    "/fields/{field_id}/events",
    response_model=ApplicationEventRead,
    dependencies=[Depends(require_role(["admin", "manager"]))],
)
def add_event(field_id: int, event: ApplicationEventCreate, session: Session = Depends(get_session)) -> ApplicationEvent:
    field = session.get(Field, field_id)
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")

    payload = event.dict()
    payload["field_id"] = field_id
    db_event = ApplicationEvent(**payload)
    session.add(db_event)
    session.commit()
    session.refresh(db_event)
    return db_event


@app.get("/fields/{field_id}/events", response_model=list[ApplicationEventRead])
def list_events(
    field_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    product: Optional[str] = None,
    operator: Optional[str] = None,
    session: Session = Depends(get_session),
) -> list[ApplicationEvent]:
    field = session.get(Field, field_id)
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")

    query = select(ApplicationEvent).where(ApplicationEvent.field_id == field_id)

    if start_date:
        query = query.where(ApplicationEvent.date >= start_date)
    if end_date:
        query = query.where(ApplicationEvent.date <= end_date)
    if product:
        query = query.where(col(ApplicationEvent.product).ilike(f"%{product}%"))
    if operator:
        query = query.where(col(ApplicationEvent.operator).ilike(f"%{operator}%"))

    return session.exec(query.order_by(ApplicationEvent.date)).all()


@app.get("/fields/{field_id}/events/summary", response_model=list[ApplicationEventSummary])
def summarize_events(field_id: int, session: Session = Depends(get_session)) -> list[ApplicationEventSummary]:
    field = session.get(Field, field_id)
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")

    query = (
        select(
            ApplicationEvent.date,
            ApplicationEvent.product,
            ApplicationEvent.rate,
        )
        .where(ApplicationEvent.field_id == field_id)
        .order_by(ApplicationEvent.date)
    )

    rows = session.exec(query).all()
    summaries: dict[tuple[int, str], ApplicationEventSummary] = {}
    for event_date, product, rate in rows:
        season = event_date.year
        key = (season, product)
        summary = summaries.setdefault(
            key,
            ApplicationEventSummary(season=season, product=product, total_rate=0.0, event_count=0),
        )
        summary.total_rate += rate
        summary.event_count += 1

    return list(summaries.values())


@app.get("/reports/field/{field_id}")
def field_report(field_id: int, session: Session = Depends(get_session)):
    events = list_events(field_id=field_id, session=session)
    summaries = summarize_events(field_id=field_id, session=session)
    return {"events": events, "summaries": summaries}
