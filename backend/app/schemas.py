from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

RoleName = Literal["employee", "manager", "admin", "vendor"]
Name = Annotated[str, Field(min_length=1, max_length=120)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Register(Input):
    full_name: Name
    email: EmailStr
    password: str = Field(min_length=10, max_length=72)

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes")
        if not any(c.isupper() for c in value) or not any(c.isdigit() for c in value):
            raise ValueError("Password must contain an uppercase letter and a number")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class Login(Input):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    email: str
    role: RoleName
    is_active: bool
    created_at: datetime
    manager_id: int | None
    supplier_id: int | None


class UserUpdate(Input):
    role: RoleName
    is_active: bool
    manager_id: int | None = None
    supplier_id: int | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class RequestInput(Input):
    title: Name
    description: str = Field(min_length=10, max_length=5000)
    category: str = Field(min_length=1, max_length=80)
    estimated_budget: Decimal = Field(gt=0, le=Decimal("9999999999.99"), decimal_places=2)
    quantity: int = Field(gt=0, le=1000000)
    target_delivery_date: date

    @field_validator("target_delivery_date")
    @classmethod
    def future_delivery(cls, value: date) -> date:
        if value < datetime.now(UTC).date():
            raise ValueError("Target delivery date cannot be in the past")
        return value


class RequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    category: str
    estimated_budget: Decimal
    quantity: int
    target_delivery_date: date
    status: str
    requested_by: int
    created_at: datetime
    updated_at: datetime


class ApprovalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    actor_id: int
    decision: str
    reason: str
    created_at: datetime


class RequestDetail(RequestOut):
    history: list[ApprovalOut]


class Decision(Input):
    decision: Literal["approved", "rejected", "revision"]
    reason: str = Field(default="", max_length=2000)
