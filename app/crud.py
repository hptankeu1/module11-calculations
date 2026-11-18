"""Data-access helpers used by tests now and by the BREAD routes in Module 12."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Calculation, User
from app.schemas import CalculationCreate, UserCreate
from app.security import hash_password


def create_user(db: Session, data: UserCreate) -> User:
    user = User(username=data.username, email=data.email, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_calculation(db: Session, user_id: int, data: CalculationCreate) -> Calculation:
    calc = Calculation.create(user_id=user_id, a=data.a, b=data.b, calc_type=data.type)
    db.add(calc)
    db.commit()
    db.refresh(calc)
    return calc


def get_calculation(db: Session, calc_id: int) -> Calculation | None:
    return db.get(Calculation, calc_id)


def list_calculations_for_user(db: Session, user_id: int) -> list[Calculation]:
    stmt = select(Calculation).where(Calculation.user_id == user_id).order_by(Calculation.id)
    return list(db.scalars(stmt))
