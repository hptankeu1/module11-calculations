"""Factory pattern for calculation logic.

Each operation is a small strategy class. ``CalculationFactory`` maps a
``CalculationType`` to the right class, so the model and services never need an
if/elif chain. Adding a new operation (e.g. Power) means writing one class and
registering it — no existing code changes (open/closed principle).
"""
from abc import ABC, abstractmethod

from app import operations
from app.schemas.calculation import CalculationType


class Operation(ABC):
    """Common interface for every calculation strategy."""

    symbol: str = "?"

    @abstractmethod
    def compute(self, a: float, b: float) -> float:
        """Return the result of applying this operation to a and b."""

    def __repr__(self) -> str:
        return f"<{type(self).__name__} '{self.symbol}'>"


class AddOperation(Operation):
    symbol = "+"

    def compute(self, a: float, b: float) -> float:
        return operations.add(a, b)


class SubOperation(Operation):
    symbol = "-"

    def compute(self, a: float, b: float) -> float:
        return operations.subtract(a, b)


class MultiplyOperation(Operation):
    symbol = "*"

    def compute(self, a: float, b: float) -> float:
        return operations.multiply(a, b)


class DivideOperation(Operation):
    symbol = "/"

    def compute(self, a: float, b: float) -> float:
        return operations.divide(a, b)


class CalculationFactory:
    """Creates the correct ``Operation`` instance for a calculation type."""

    _registry: dict[CalculationType, type[Operation]] = {
        CalculationType.ADD: AddOperation,
        CalculationType.SUB: SubOperation,
        CalculationType.MULTIPLY: MultiplyOperation,
        CalculationType.DIVIDE: DivideOperation,
    }

    @classmethod
    def register(cls, calc_type: CalculationType, operation_cls: type[Operation]) -> None:
        """Register (or replace) the operation class used for ``calc_type``."""
        if not (isinstance(operation_cls, type) and issubclass(operation_cls, Operation)):
            raise TypeError("operation_cls must be a subclass of Operation")
        cls._registry[calc_type] = operation_cls

    @classmethod
    def create(cls, calc_type: CalculationType | str) -> Operation:
        """Return an ``Operation`` for ``calc_type`` (enum member or its string value)."""
        try:
            key = CalculationType.from_value(calc_type)
        except ValueError as exc:
            raise ValueError(f"Unsupported calculation type: {calc_type!r}") from exc
        operation_cls = cls._registry.get(key)
        if operation_cls is None:
            raise ValueError(f"No operation registered for {key.value!r}")
        return operation_cls()

    @classmethod
    def compute(cls, calc_type: CalculationType | str, a: float, b: float) -> float:
        """Convenience: pick the operation and run it in one call."""
        return cls.create(calc_type).compute(a, b)
