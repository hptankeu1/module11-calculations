import pytest

from app.operations.factory import (
    AddOperation,
    CalculationFactory,
    DivideOperation,
    MultiplyOperation,
    Operation,
    SubOperation,
)
from app.schemas.calculation import CalculationType


@pytest.mark.parametrize(
    "calc_type, expected_cls",
    [
        (CalculationType.ADD, AddOperation),
        (CalculationType.SUB, SubOperation),
        (CalculationType.MULTIPLY, MultiplyOperation),
        (CalculationType.DIVIDE, DivideOperation),
    ],
)
def test_factory_chooses_correct_operation(calc_type, expected_cls):
    op = CalculationFactory.create(calc_type)
    assert isinstance(op, expected_cls)
    assert isinstance(op, Operation)


@pytest.mark.parametrize("raw", ["Add", "add", "ADD", "  add  "])
def test_factory_accepts_case_insensitive_strings(raw):
    assert isinstance(CalculationFactory.create(raw), AddOperation)


@pytest.mark.parametrize(
    "calc_type, a, b, expected",
    [("Add", 6, 3, 9), ("Sub", 6, 3, 3), ("Multiply", 6, 3, 18), ("Divide", 6, 3, 2)],
)
def test_factory_compute(calc_type, a, b, expected):
    assert CalculationFactory.compute(calc_type, a, b) == expected


@pytest.mark.parametrize("bad", ["Power", "", "plus", None, 42])
def test_factory_rejects_unknown_type(bad):
    with pytest.raises(ValueError, match="Unsupported calculation type"):
        CalculationFactory.create(bad)


def test_divide_operation_by_zero():
    with pytest.raises(ZeroDivisionError):
        CalculationFactory.compute(CalculationType.DIVIDE, 1, 0)


def test_operation_symbols_and_repr():
    assert [CalculationFactory.create(t).symbol for t in CalculationType] == ["+", "-", "*", "/"]
    assert repr(AddOperation()) == "<AddOperation '+'>"


def test_operation_is_abstract():
    with pytest.raises(TypeError):
        Operation()  # type: ignore[abstract]


def test_register_custom_operation_and_restore():
    class DoubleAdd(Operation):
        symbol = "++"

        def compute(self, a, b):
            return 2 * (a + b)

    original = CalculationFactory._registry[CalculationType.ADD]
    try:
        CalculationFactory.register(CalculationType.ADD, DoubleAdd)
        assert CalculationFactory.compute("Add", 1, 2) == 6
    finally:
        CalculationFactory.register(CalculationType.ADD, original)
    assert CalculationFactory.compute("Add", 1, 2) == 3


def test_register_rejects_non_operation():
    with pytest.raises(TypeError):
        CalculationFactory.register(CalculationType.ADD, dict)  # type: ignore[arg-type]
