"""Calculation ORM model.

Design decision: the result is computed once (via the factory) when the record
is created and stored in the ``result`` column. Calculations are immutable
history entries, so storing the value makes reads cheap and lets us query or
sort by result. If ``a``, ``b`` or ``type`` change later (Module 12 Edit),
``recompute()`` refreshes it.
"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.operations.factory import CalculationFactory
from app.schemas.calculation import CalculationType

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Calculation(Base):
    __tablename__ = "calculations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    a: Mapped[float] = mapped_column(Float, nullable=False)
    b: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[CalculationType] = mapped_column(
        Enum(
            CalculationType,
            name="calculation_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
    )
    result: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="calculations")

    # --- ORM-level guards (defence in depth behind the Pydantic schema) ---
    @validates("type")
    def _validate_type(self, _key: str, value: CalculationType | str) -> CalculationType:
        calc_type = CalculationType.from_value(value)
        # b may have been assigned before type, so check the pair from both sides.
        if calc_type is CalculationType.DIVIDE and self.b == 0:
            raise ValueError("Cannot divide by zero")
        return calc_type

    @validates("b")
    def _validate_b(self, _key: str, value: float) -> float:
        if value == 0 and self.type is CalculationType.DIVIDE:
            raise ValueError("Cannot divide by zero")
        return value

    # --- construction helpers ---
    @classmethod
    def create(cls, *, user_id: int, a: float, b: float, calc_type: CalculationType | str) -> "Calculation":
        """Build a Calculation and compute its result with the factory."""
        calc_type = CalculationType.from_value(calc_type)
        result = CalculationFactory.compute(calc_type, a, b)
        return cls(user_id=user_id, a=a, b=b, type=calc_type, result=result)

    def recompute(self) -> float:
        """Recalculate and store the result from the current operands."""
        self.result = CalculationFactory.compute(self.type, self.a, self.b)
        return self.result

    def __repr__(self) -> str:
        type_value = self.type.value if self.type else None
        return f"<Calculation id={self.id} {self.a} {type_value} {self.b} = {self.result}>"
