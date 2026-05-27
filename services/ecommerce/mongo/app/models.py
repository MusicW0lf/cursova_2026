from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel
from beanie import Document
from pydantic import EmailStr


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


class User(Document):
    email: EmailStr
    name: str
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    gender: Gender | None = None
    age: int | None = None
    phone: str | None = None
    created_at: datetime = None
    updated_at: datetime = None

    class Settings:
        name = "users"


class Product(Document):
    name: str
    price: float
    description: str | None = None
    category: str | None = None
    characteristics: dict[str, Any] | None = None
    created_at: datetime = None
    updated_at: datetime = None

    class Settings:
        name = "products"


class OrderItem(BaseModel):
    product_id: str
    quantity: int


class Order(Document):
    user_id: str
    items: list[OrderItem]
    status: OrderStatus = OrderStatus.PENDING
    total_price: float
    created_at: datetime = None
    updated_at: datetime = None

    class Settings:
        name = "orders"
