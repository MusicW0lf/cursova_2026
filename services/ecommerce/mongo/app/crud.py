from datetime import datetime, timezone

from beanie import PydanticObjectId
from fastapi import HTTPException
from bson.errors import InvalidId

from . import models, schemas


def _now() -> datetime:
    return datetime.now(timezone.utc)


# =========================
# USERS
# =========================


async def create_user(user: schemas.UserCreate) -> models.User:
    now = _now()
    db_user = models.User(**user.model_dump(), created_at=now, updated_at=now)
    await db_user.insert()
    return db_user


async def get_users(name: str | None = None) -> list[models.User]:
    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    return await models.User.find(query).to_list()


async def get_user(user_id: str) -> models.User:
    try:
        user = await models.User.get(PydanticObjectId(user_id))
    except InvalidId:
        raise HTTPException(status_code=422, detail="Invalid user_id format")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def update_user(user_id: str, data: schemas.UserUpdate) -> models.User:
    user = await get_user(user_id)
    update_data = data.model_dump(exclude_none=True)
    update_data["updated_at"] = _now()
    await user.set(update_data)
    return user


async def delete_user(user_id: str) -> None:
    user = await get_user(user_id)
    # cascade delete all orders for this user
    await models.Order.find({"user_id": user_id}).delete()
    await user.delete()


# =========================
# PRODUCTS
# =========================


async def create_product(product: schemas.ProductCreate) -> models.Product:
    now = _now()
    db_product = models.Product(**product.model_dump(), created_at=now, updated_at=now)
    await db_product.insert()
    return db_product


async def get_products(name: str | None = None) -> list[models.Product]:
    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    return await models.Product.find(query).to_list()


async def get_product(product_id: str) -> models.Product:
    try:
        product = await models.Product.get(PydanticObjectId(product_id))
    except InvalidId:
        raise HTTPException(status_code=422, detail="Invalid product_id format")
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


async def update_product(
    product_id: str, data: schemas.ProductUpdate
) -> models.Product:
    product = await get_product(product_id)
    update_data = data.model_dump(exclude_none=True)
    update_data["updated_at"] = _now()
    await product.set(update_data)
    return product


async def delete_product(product_id: str) -> None:
    product = await get_product(product_id)
    # cascade delete all orders for this product
    await models.Order.find({"items.product_id": product_id}).delete()
    await product.delete()


# =========================
# ORDERS
# =========================


async def create_order(order: schemas.OrderCreate) -> models.Order:

    # validate user
    try:
        user = await models.User.get(PydanticObjectId(order.user_id))
    except InvalidId:
        raise HTTPException(status_code=422, detail="Invalid user_id format")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    total_price = 0.0

    # validate all products + calculate total
    for item in order.items:

        try:
            product = await models.Product.get(PydanticObjectId(item.product_id))

        except InvalidId:
            raise HTTPException(
                status_code=422, detail=f"Invalid product_id format: {item.product_id}"
            )

        if not product:
            raise HTTPException(
                status_code=404, detail=f"Product not found: {item.product_id}"
            )

        total_price += product.price * item.quantity

    now = _now()

    db_order = models.Order(
        user_id=order.user_id,
        items=[
            models.OrderItem(product_id=item.product_id, quantity=item.quantity)
            for item in order.items
        ],
        total_price=total_price,
        status=models.OrderStatus.PENDING,
        created_at=now,
        updated_at=now,
    )

    await db_order.insert()

    return db_order


async def get_orders(user_id: str | None = None) -> list[models.Order]:

    query = {}

    if user_id:
        query["user_id"] = user_id

    return await models.Order.find(query).to_list()


async def get_order(order_id: str) -> models.Order:

    try:
        order = await models.Order.get(PydanticObjectId(order_id))

    except InvalidId:
        raise HTTPException(status_code=422, detail="Invalid order_id format")

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order


async def update_order(order_id: str, data: schemas.OrderUpdate) -> models.Order:

    order = await get_order(order_id)

    update_data = data.model_dump(exclude_none=True)

    if "status" in update_data:
        update_data["status"] = update_data["status"].value

    update_data["updated_at"] = _now()

    await order.set(update_data)

    return order


async def delete_order(order_id: str) -> None:

    order = await get_order(order_id)

    await order.delete()
