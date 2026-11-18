from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.calculation import CalculationCreate, CalculationRead, CalculationType


# ---------- CalculationCreate: valid input ----------

@pytest.mark.parametrize("calc_type", ["Add", "Sub", "Multiply", "Divide"])
def test_create_accepts_each_type(calc_type):
    calc = CalculationCreate(a=10, b=5, type=calc_type)
    assert calc.type == CalculationType(calc_type)
    assert calc.a == 10.0 and calc.b == 5.0


@pytest.mark.parametrize("raw, expected", [("add", "Add"), ("MULTIPLY", "Multiply"), (" sub ", "Sub")])
def test_create_normalises_type_case(raw, expected):
    assert CalculationCreate(a=1, b=2, type=raw).type.value == expected


def test_create_accepts_enum_member_and_numeric_strings():
    calc = CalculationCreate(a="3.5", b="2", type=CalculationType.MULTIPLY)
    assert calc.a == 3.5 and calc.b == 2.0


def test_create_allows_zero_b_for_non_divide():
    for t in ("Add", "Sub", "Multiply"):
        assert CalculationCreate(a=1, b=0, type=t).b == 0


def test_create_from_json():
    calc = CalculationCreate.model_validate_json('{"a": 8, "b": 2, "type": "Divide"}')
    assert calc.type is CalculationType.DIVIDE


# ---------- CalculationCreate: invalid input ----------

def test_create_rejects_zero_divisor():
    with pytest.raises(ValidationError, match="Cannot divide by zero"):
        CalculationCreate(a=10, b=0, type="Divide")


def test_create_rejects_negative_zero_divisor():
    with pytest.raises(ValidationError, match="Cannot divide by zero"):
        CalculationCreate(a=10, b=-0.0, type="Divide")


@pytest.mark.parametrize("bad_type", ["Power", "Modulus", "", "+", 1, None])
def test_create_rejects_invalid_type(bad_type):
    with pytest.raises(ValidationError, match="type must be one of"):
        CalculationCreate(a=1, b=2, type=bad_type)


@pytest.mark.parametrize("field", ["a", "b"])
@pytest.mark.parametrize("bad_value", ["abc", None, [1], {"x": 1}, True])
def test_create_rejects_non_numeric_operands(field, bad_value):
    payload = {"a": 1, "b": 2, "type": "Add", field: bad_value}
    with pytest.raises(ValidationError):
        CalculationCreate(**payload)


@pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), float("-inf")])
def test_create_rejects_non_finite(bad_value):
    with pytest.raises(ValidationError, match="finite"):
        CalculationCreate(a=bad_value, b=1, type="Add")


@pytest.mark.parametrize("missing", ["a", "b", "type"])
def test_create_requires_all_fields(missing):
    payload = {"a": 1, "b": 2, "type": "Add"}
    payload.pop(missing)
    with pytest.raises(ValidationError):
        CalculationCreate(**payload)


def test_create_forbids_extra_fields():
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CalculationCreate(a=1, b=2, type="Add", result=999)


# ---------- CalculationRead ----------

def test_read_serialises_from_orm_like_object():
    now = datetime.now(timezone.utc)
    obj = SimpleNamespace(id=1, user_id=7, a=6.0, b=3.0, type=CalculationType.DIVIDE, result=2.0,
                          created_at=now, secret="should-not-leak")
    data = CalculationRead.model_validate(obj).model_dump(mode="json")
    assert data == {
        "id": 1, "user_id": 7, "a": 6.0, "b": 3.0, "type": "Divide", "result": 2.0,
        "created_at": now.isoformat().replace("+00:00", "Z"),
    }
    assert "secret" not in data


def test_read_requires_result():
    with pytest.raises(ValidationError):
        CalculationRead(id=1, user_id=1, a=1, b=1, type="Add", created_at=datetime.now())
