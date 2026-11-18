"""Pydantic schemas for calculations."""
import math
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CalculationType(str, Enum):
    """Allowed calculation types. Values are what clients send and what is stored."""

    ADD = "Add"
    SUB = "Sub"
    MULTIPLY = "Multiply"
    DIVIDE = "Divide"

    @classmethod
    def from_value(cls, value: "CalculationType | str") -> "CalculationType":
        """Case-insensitive lookup: 'add', 'ADD' and 'Add' all map to ADD."""
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            cleaned = value.strip().lower()
            for member in cls:
                if member.value.lower() == cleaned:
                    return member
        allowed = ", ".join(m.value for m in cls)
        raise ValueError(f"type must be one of: {allowed}")


class CalculationBase(BaseModel):
    a: float = Field(..., description="First operand", examples=[10])
    b: float = Field(..., description="Second operand", examples=[5])
    type: CalculationType = Field(..., description="Add, Sub, Multiply or Divide", examples=["Add"])


class CalculationCreate(CalculationBase):
    """Incoming payload for creating a calculation."""

    model_config = ConfigDict(
        extra="forbid",  # reject unknown fields such as a client-supplied 'result'
        json_schema_extra={"example": {"a": 10, "b": 5, "type": "Divide"}},
    )

    @field_validator("a", "b", mode="before")
    @classmethod
    def reject_non_numbers(cls, value: Any) -> Any:
        # bool is a subclass of int in Python, so True would silently become 1.0.
        if isinstance(value, bool):
            raise ValueError("operands must be numbers, not booleans")
        if value is None:
            raise ValueError("operand is required")
        return value

    @field_validator("a", "b")
    @classmethod
    def reject_non_finite(cls, value: float) -> float:
        if math.isnan(value) or math.isinf(value):
            raise ValueError("operands must be finite numbers")
        return value

    @field_validator("type", mode="before")
    @classmethod
    def normalise_type(cls, value: Any) -> CalculationType:
        return CalculationType.from_value(value)

    @model_validator(mode="after")
    def no_zero_divisor(self) -> "CalculationCreate":
        if self.type is CalculationType.DIVIDE and self.b == 0:
            raise ValueError("Cannot divide by zero: b must be non-zero for Divide")
        return self


class CalculationRead(CalculationBase):
    """Outgoing representation of a stored calculation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    result: float
    created_at: datetime
