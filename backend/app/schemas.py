from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

RoleName = Literal["employee", "manager", "admin", "vendor"]
Name = Annotated[str, Field(min_length=1, max_length=120)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Register(Input):
    full_name: Name
    email: EmailStr
    password: Annotated[str, StringConstraints(strip_whitespace=False)] = Field(
        min_length=10, max_length=72
    )

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
    password: Annotated[str, StringConstraints(strip_whitespace=False)] = Field(
        min_length=1, max_length=72
    )


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


class SupplierInput(Input):
    company_name: Name
    category: str = Field(min_length=1, max_length=80)
    rating: Decimal = Field(ge=0, le=5, decimal_places=2)
    average_price_score: Decimal = Field(ge=0, le=100, decimal_places=2)
    average_delivery_days: int = Field(ge=1, le=365)
    reliability_score: Decimal = Field(ge=0, le=100, decimal_places=2)
    contact_person: Name
    email: EmailStr


class SupplierOut(SupplierInput):
    model_config = ConfigDict(from_attributes=True)
    id: int


class CategoryInput(Input):
    name: str = Field(min_length=1, max_length=80)


class RecommendationOut(BaseModel):
    supplier: SupplierOut
    score: Decimal
    contributions: dict[str, Decimal]
    explanation: str


class OrderInput(Input):
    request_id: int = Field(gt=0)
    supplier_id: int = Field(gt=0)


class OrderStatus(Input):
    status: Literal["processing", "shipped", "delivered"]


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    request_id: int
    supplier_id: int
    approved_by: int
    status: str
    amount: Decimal
    order_date: datetime
    delivery_date: datetime | None
    updated_at: datetime


class OrderEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    actor_id: int
    status: str
    created_at: datetime


class OrderDetail(OrderOut):
    request_title: str
    supplier_name: str
    history: list[OrderEventOut]


class CommentEdit(Input):
    content: str = Field(min_length=1, max_length=5000)


class CommentInput(CommentEdit):
    parent_comment_id: int | None = Field(default=None, gt=0)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    request_id: int
    user_id: int
    parent_comment_id: int | None
    content: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    author_name: str
    reply_count: int


class MonthlySpend(BaseModel):
    month: str
    amount: Decimal


class StatusCount(BaseModel):
    status: str
    count: int


class SupplierSpend(BaseModel):
    supplier: str
    amount: Decimal


class DashboardOut(BaseModel):
    total_requests: int
    total_suppliers: int
    approved_orders: int
    pending_approvals: int
    procurement_spend: Decimal
    monthly_spending: list[MonthlySpend]
    approval_status: list[StatusCount]
    top_suppliers: list[SupplierSpend]


class CategorySpend(BaseModel):
    category: str
    amount: Decimal
    orders: int


class SupplierPerformance(BaseModel):
    supplier_id: int
    supplier: str
    rating: Decimal
    reliability_score: Decimal
    total_orders: int
    delivered_orders: int
    delivered_value: Decimal
    average_actual_delivery_days: float | None


class MonthlyTrend(MonthlySpend):
    requests: int
    delivered_orders: int


class ApprovalTurnaround(BaseModel):
    category: str
    decided_requests: int
    average_hours: float


class ReportsOut(BaseModel):
    spending_by_category: list[CategorySpend]
    supplier_performance: list[SupplierPerformance]
    monthly_trends: list[MonthlyTrend]
    approval_turnaround: list[ApprovalTurnaround]
