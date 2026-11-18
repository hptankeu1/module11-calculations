"""Integration tests: Calculation model against a real PostgreSQL database."""
import pytest
from pydantic import ValidationError
from sqlalchemy import select, text
from sqlalchemy.exc import DataError, IntegrityError, StatementError

from app import crud
from app.models import Calculation, User
from app.schemas import CalculationCreate, CalculationRead, CalculationType


# ---------- happy paths ----------

@pytest.mark.parametrize(
    "calc_type, a, b, expected",
    [("Add", 10, 5, 15), ("Sub", 10, 5, 5), ("Multiply", 10, 5, 50), ("Divide", 10, 4, 2.5)],
)
def test_insert_calculation_stores_correct_data(db_session, user, calc_type, a, b, expected):
    calc = crud.create_calculation(db_session, user.id, CalculationCreate(a=a, b=b, type=calc_type))
    db_session.expire_all()  # force a real round-trip to Postgres

    stored = db_session.get(Calculation, calc.id)
    assert stored is not None
    assert (stored.a, stored.b, stored.type, stored.result) == (a, b, CalculationType(calc_type), expected)
    assert stored.user_id == user.id
    assert stored.created_at is not None


def test_enum_is_stored_as_readable_string(db_session, user):
    calc = crud.create_calculation(db_session, user.id, CalculationCreate(a=1, b=2, type="multiply"))
    raw = db_session.execute(
        text("SELECT type::text FROM calculations WHERE id = :id"), {"id": calc.id}
    ).scalar_one()
    assert raw == "Multiply"


def test_schema_model_schema_roundtrip(db_session, user):
    calc = crud.create_calculation(db_session, user.id, CalculationCreate(a=9, b=3, type="Divide"))
    out = CalculationRead.model_validate(calc).model_dump(mode="json")
    assert out["result"] == 3.0 and out["type"] == "Divide" and out["user_id"] == user.id


def test_user_relationship_and_listing(db_session, user):
    for t in ("Add", "Sub", "Multiply"):
        crud.create_calculation(db_session, user.id, CalculationCreate(a=2, b=1, type=t))
    db_session.refresh(user)
    assert len(user.calculations) == 3
    assert [c.type.value for c in crud.list_calculations_for_user(db_session, user.id)] == ["Add", "Sub", "Multiply"]
    assert crud.get_calculation(db_session, user.calculations[0].id).user is user


def test_recompute_after_edit(db_session, user):
    calc = crud.create_calculation(db_session, user.id, CalculationCreate(a=2, b=3, type="Add"))
    calc.type = CalculationType.MULTIPLY
    calc.recompute()
    db_session.commit()
    db_session.expire_all()
    assert db_session.get(Calculation, calc.id).result == 6


def test_create_user_via_crud_hashes_password(db_session):
    from app.schemas import UserCreate

    u = crud.create_user(db_session, UserCreate(username="bob", email="bob@example.com", password="Secret123"))
    assert u.id is not None and u.password_hash != "Secret123"


# ---------- foreign key / constraint behaviour ----------

def test_foreign_key_rejects_unknown_user(db_session):
    db_session.add(Calculation.create(user_id=999_999, a=1, b=1, calc_type="Add"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_user_id_is_required(db_session):
    calc = Calculation(a=1, b=1, type=CalculationType.ADD, result=2)
    db_session.add(calc)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_deleting_user_cascades_to_calculations(db_session, user):
    calc = crud.create_calculation(db_session, user.id, CalculationCreate(a=1, b=1, type="Add"))
    calc_id = calc.id
    db_session.delete(user)
    db_session.commit()
    db_session.expunge_all()  # drop cached objects so we read what Postgres actually holds
    assert db_session.get(Calculation, calc_id) is None
    assert db_session.scalar(select(User).where(User.username == "alice")) is None


def test_db_level_cascade_with_raw_delete(db_session, user):
    """ondelete=CASCADE is enforced by Postgres itself, not just the ORM."""
    crud.create_calculation(db_session, user.id, CalculationCreate(a=1, b=1, type="Add"))
    db_session.execute(text("DELETE FROM users WHERE id = :id"), {"id": user.id})
    count = db_session.execute(
        text("SELECT count(*) FROM calculations WHERE user_id = :id"), {"id": user.id}
    ).scalar_one()
    assert count == 0


# ---------- error cases ----------

def test_invalid_type_rejected_by_schema_before_db():
    with pytest.raises(ValidationError):
        CalculationCreate(a=1, b=2, type="Power")


def test_invalid_type_rejected_by_model(user):
    with pytest.raises(ValueError):
        Calculation.create(user_id=user.id, a=1, b=2, calc_type="Power")


def test_invalid_type_rejected_by_database_enum(db_session, user):
    """Even raw SQL can't store a value outside the Postgres enum."""
    with pytest.raises((DataError, StatementError)):
        db_session.execute(
            text("INSERT INTO calculations (user_id, a, b, type, result) VALUES (:u, 1, 2, 'Power', 0)"),
            {"u": user.id},
        )


def test_divide_by_zero_rejected_by_schema():
    with pytest.raises(ValidationError, match="divide by zero"):
        CalculationCreate(a=5, b=0, type="Divide")


def test_divide_by_zero_rejected_by_model(user):
    with pytest.raises((ValueError, ZeroDivisionError)):
        Calculation.create(user_id=user.id, a=5, b=0, calc_type="Divide")


@pytest.mark.parametrize("order", ["b_first", "type_first"])
def test_model_validator_catches_zero_divisor_regardless_of_order(order):
    calc = Calculation()
    with pytest.raises(ValueError, match="divide by zero"):
        if order == "b_first":
            calc.b = 0
            calc.type = "Divide"
        else:
            calc.type = "Divide"
            calc.b = 0


def test_nothing_persisted_after_failed_insert(db_session, user):
    with pytest.raises(ValidationError):
        crud.create_calculation(db_session, user.id, CalculationCreate(a=1, b=0, type="Divide"))
    assert crud.list_calculations_for_user(db_session, user.id) == []
