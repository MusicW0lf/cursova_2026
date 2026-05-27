from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, EmailStr

# =========================
# ENUMS
# =========================


class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    NON_BINARY = "NON_BINARY"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


# =========================
# USER
# =========================


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    gender: Gender | None = None
    age: int | None = None
    phone: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    gender: Gender | None = None
    age: int | None = None
    phone: str | None = None


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    username: str | None
    first_name: str | None
    last_name: str | None
    gender: Gender | None
    age: int | None
    phone: str | None
    created_at: datetime
    updated_at: datetime


# =========================
# PRODUCT
# =========================


class ProductCreate(BaseModel):
    name: str
    price: float
    description: str | None = None
    category: str | None = None
    characteristics: dict[str, Any] | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    description: str | None = None
    category: str | None = None
    characteristics: dict[str, Any] | None = None


class ProductResponse(BaseModel):
    id: str
    name: str
    price: float
    description: str | None
    category: str | None
    characteristics: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


# =========================
# ORDER
# =========================


class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int


class OrderItemResponse(BaseModel):
    product_id: str
    quantity: int


class OrderCreate(BaseModel):
    user_id: str
    items: list[OrderItemCreate]


class OrderUpdate(BaseModel):
    status: OrderStatus | None = None
    total_price: float | None = None


class OrderResponse(BaseModel):
    id: str
    user_id: str
    items: list[OrderItemResponse]
    status: OrderStatus
    total_price: float
    created_at: datetime
    updated_at: datetime
