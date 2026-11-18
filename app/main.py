"""FastAPI application entry point.

Module 11 focuses on modelling and validation; the calculation BREAD routes
arrive in Module 12. The app currently exposes a health check that also
verifies the database connection, which the Docker HEALTHCHECK uses.
"""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.schemas import CalculationType


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Calculator API", version="0.11.0", lifespan=lifespan)


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


@app.get("/calculation-types")
def calculation_types() -> list[str]:
    return [t.value for t in CalculationType]
