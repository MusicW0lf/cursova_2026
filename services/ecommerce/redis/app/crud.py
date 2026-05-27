import json
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as aioredis
from fastapi import HTTPException

from . import schemas


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_user(uid: str, data: dict) -> schemas.UserResponse:
    return schemas.UserResponse(
        id=uid,
        email=data["email"],
        name=data["name"],
        username=data.get("username"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        gender=data.get("gender"),
        age=int(data["age"]) if data.get("age") else None,
        phone=data.get("phone"),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def _parse_product(pid: str, data: dict) -> schemas.ProductResponse:
    return schemas.ProductResponse(
        id=pid,
        name=data["name"],
        price=float(data["price"]),
        description=data.get("description"),
        category=data.get("category"),
        characteristics=(
            json.loads(data["characteristics"]) if data.get("characteristics") else None
        ),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def _parse_order(oid: str, data: dict, items: list[dict]) -> schemas.OrderResponse:

    return schemas.OrderResponse(
        id=oid,
        user_id=data["user_id"],
        items=[
            schemas.OrderItemResponse(
                product_id=item["product_id"], quantity=int(item["quantity"])
            )
            for item in items
        ],
        status=data["status"],
        total_price=float(data["total_price"]),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


# =========================
# USERS
# =========================


async def create_user(
    r: aioredis.Redis, user: schemas.UserCreate
) -> schemas.UserResponse:
    user_id = await r.incr("user:counter")
    now = _now()

    mapping = {
        "email": user.email,
        "name": user.name,
        "created_at": now,
        "updated_at": now,
    }
    if user.username is not None:
        mapping["username"] = user.username
    if user.first_name is not None:
        mapping["first_name"] = user.first_name
    if user.last_name is not None:
        mapping["last_name"] = user.last_name
    if user.gender is not None:
        mapping["gender"] = user.gender.value
    if user.age is not None:
        mapping["age"] = user.age
    if user.phone is not None:
        mapping["phone"] = user.phone

    async with r.pipeline() as pipe:
        await pipe.hset(f"user:{user_id}", mapping=mapping)
        await pipe.sadd("users:all", user_id)
        await pipe.execute()

    return _parse_user(str(user_id), mapping)


async def get_users(
    r: aioredis.Redis, name: str | None = None
) -> list[schemas.UserResponse]:
    user_ids = list(await r.smembers("users:all"))
    if not user_ids:
        return []

    async with r.pipeline() as pipe:
        for uid in user_ids:
            await pipe.hgetall(f"user:{uid}")
        results = await pipe.execute()

    users = []
    for uid, data in zip(user_ids, results):
        if not data:
            continue
        if name and name.lower() not in data["name"].lower():
            continue
        users.append(_parse_user(str(uid), data))
    return users


async def get_user(r: aioredis.Redis, user_id: str) -> schemas.UserResponse:
    data = await r.hgetall(f"user:{user_id}")
    if not data:
        raise HTTPException(status_code=404, detail="User not found")
    return _parse_user(user_id, data)


async def update_user(
    r: aioredis.Redis, user_id: str, data: schemas.UserUpdate
) -> schemas.UserResponse:
    existing = await r.hgetall(f"user:{user_id}")
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    updates = data.model_dump(exclude_none=True)
    updates["updated_at"] = _now()

    if "gender" in updates:
        updates["gender"] = updates["gender"].value

    await r.hset(f"user:{user_id}", mapping=updates)
    updated = await r.hgetall(f"user:{user_id}")
    return _parse_user(user_id, updated)


async def delete_user(r: aioredis.Redis, user_id: str) -> None:
    existing = await r.hgetall(f"user:{user_id}")
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    # cascade delete all orders for this user
    order_ids = await r.smembers(f"orders:user:{user_id}")
    async with r.pipeline() as pipe:
        for oid in order_ids:
            await pipe.delete(f"order:{oid}:items")
            await pipe.delete(f"order:{oid}")
            await pipe.srem("orders:all", oid)
        await pipe.delete(f"orders:user:{user_id}")
        await pipe.delete(f"user:{user_id}")
        await pipe.srem("users:all", user_id)
        await pipe.execute()


# =========================
# PRODUCTS
# =========================


async def create_product(
    r: aioredis.Redis, product: schemas.ProductCreate
) -> schemas.ProductResponse:
    product_id = await r.incr("product:counter")
    now = _now()

    mapping = {
        "name": product.name,
        "price": product.price,
        "created_at": now,
        "updated_at": now,
    }
    if product.description is not None:
        mapping["description"] = product.description
    if product.category is not None:
        mapping["category"] = product.category
    if product.characteristics is not None:
        mapping["characteristics"] = json.dumps(product.characteristics)

    async with r.pipeline() as pipe:
        await pipe.hset(f"product:{product_id}", mapping=mapping)
        await pipe.sadd("products:all", product_id)
        await pipe.execute()

    return _parse_product(str(product_id), mapping)


async def get_products(
    r: aioredis.Redis, name: str | None = None
) -> list[schemas.ProductResponse]:
    product_ids = list(await r.smembers("products:all"))
    if not product_ids:
        return []

    async with r.pipeline() as pipe:
        for pid in product_ids:
            await pipe.hgetall(f"product:{pid}")
        results = await pipe.execute()

    products = []
    for pid, data in zip(product_ids, results):
        if not data:
            continue
        if name and name.lower() not in data["name"].lower():
            continue
        products.append(_parse_product(str(pid), data))
    return products


async def get_product(r: aioredis.Redis, product_id: str) -> schemas.ProductResponse:
    data = await r.hgetall(f"product:{product_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Product not found")
    return _parse_product(product_id, data)


async def update_product(
    r: aioredis.Redis, product_id: str, data: schemas.ProductUpdate
) -> schemas.ProductResponse:
    existing = await r.hgetall(f"product:{product_id}")
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    updates = data.model_dump(exclude_none=True)
    updates["updated_at"] = _now()

    if "characteristics" in updates:
        updates["characteristics"] = json.dumps(updates["characteristics"])

    await r.hset(f"product:{product_id}", mapping=updates)
    updated = await r.hgetall(f"product:{product_id}")
    return _parse_product(product_id, updated)


async def delete_product(r: aioredis.Redis, product_id: str) -> None:
    existing = await r.hgetall(f"product:{product_id}")
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    order_ids = await r.smembers(f"orders:product:{product_id}")
    async with r.pipeline() as pipe:
        for oid in order_ids:

            data = await r.hgetall(f"order:{oid}")

            raw_items = await r.lrange(f"order:{oid}:items", 0, -1)

            items = [json.loads(item) for item in raw_items]

            await pipe.delete(f"order:{oid}")
            await pipe.delete(f"order:{oid}:items")

            await pipe.srem("orders:all", oid)

            await pipe.srem(f"orders:user:{data.get('user_id')}", oid)

            for item in items:
                await pipe.srem(f"orders:product:{item['product_id']}", oid)
        await pipe.delete(f"orders:product:{product_id}")
        await pipe.delete(f"product:{product_id}")
        await pipe.srem("products:all", product_id)
        await pipe.execute()


# =========================
# ORDERS
# =========================


async def create_order(
    r: aioredis.Redis, order: schemas.OrderCreate
) -> schemas.OrderResponse:

    user = await r.hgetall(f"user:{order.user_id}")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    total_price = 0.0

    # validate all products
    for item in order.items:

        product = await r.hgetall(f"product:{item.product_id}")

        if not product:
            raise HTTPException(
                status_code=404, detail=f"Product {item.product_id} not found"
            )

        total_price += float(product["price"]) * item.quantity

    order_id = await r.incr("order:counter")

    now = _now()

    mapping = {
        "user_id": order.user_id,
        "status": schemas.OrderStatus.PENDING.value,
        "total_price": total_price,
        "created_at": now,
        "updated_at": now,
    }

    async with r.pipeline() as pipe:

        # order hash
        await pipe.hset(f"order:{order_id}", mapping=mapping)

        # order items
        for item in order.items:

            item_data = json.dumps(
                {"product_id": item.product_id, "quantity": item.quantity}
            )

            await pipe.rpush(f"order:{order_id}:items", item_data)

            # reverse product lookup
            await pipe.sadd(f"orders:product:{item.product_id}", order_id)

        await pipe.sadd("orders:all", order_id)

        await pipe.sadd(f"orders:user:{order.user_id}", order_id)

        await pipe.execute()

    return schemas.OrderResponse(
        id=str(order_id),
        user_id=order.user_id,
        items=[
            schemas.OrderItemResponse(product_id=i.product_id, quantity=i.quantity)
            for i in order.items
        ],
        status=schemas.OrderStatus.PENDING,
        total_price=total_price,
        created_at=now,
        updated_at=now,
    )


async def get_orders(
    r: aioredis.Redis, user_id: str | None = None
) -> list[schemas.OrderResponse]:

    if user_id:
        order_ids = await r.smembers(f"orders:user:{user_id}")
    else:
        order_ids = await r.smembers("orders:all")

    if not order_ids:
        return []

    order_ids = list(order_ids)

    # batch all reads in a single pipeline round-trip
    async with r.pipeline() as pipe:
        for oid in order_ids:
            await pipe.hgetall(f"order:{oid}")
            await pipe.lrange(f"order:{oid}:items", 0, -1)
        results = await pipe.execute()

    # results is a flat list: [hgetall_0, lrange_0, hgetall_1, lrange_1, ...]
    orders = []
    for i, oid in enumerate(order_ids):
        data = results[i * 2]
        raw_items = results[i * 2 + 1]

        if not data:
            continue

        items = [json.loads(item) for item in raw_items]
        orders.append(_parse_order(str(oid), data, items))

    return orders


async def get_order(r: aioredis.Redis, order_id: str) -> schemas.OrderResponse:

    data = await r.hgetall(f"order:{order_id}")

    if not data:
        raise HTTPException(status_code=404, detail="Order not found")

    raw_items = await r.lrange(f"order:{order_id}:items", 0, -1)

    items = [json.loads(item) for item in raw_items]

    return _parse_order(order_id, data, items)


async def update_order(
    r: aioredis.Redis, order_id: str, data: schemas.OrderUpdate
) -> schemas.OrderResponse:

    existing = await r.hgetall(f"order:{order_id}")

    if not existing:
        raise HTTPException(status_code=404, detail="Order not found")

    updates = data.model_dump(exclude_none=True)

    updates["updated_at"] = _now()

    if "status" in updates:
        updates["status"] = updates["status"].value

    await r.hset(f"order:{order_id}", mapping=updates)

    return await get_order(r, order_id)


async def delete_order(r: aioredis.Redis, order_id: str) -> None:

    existing = await r.hgetall(f"order:{order_id}")

    if not existing:
        raise HTTPException(status_code=404, detail="Order not found")

    user_id = existing.get("user_id")

    raw_items = await r.lrange(f"order:{order_id}:items", 0, -1)

    items = [json.loads(item) for item in raw_items]

    async with r.pipeline() as pipe:

        await pipe.delete(f"order:{order_id}")

        await pipe.delete(f"order:{order_id}:items")

        await pipe.srem("orders:all", order_id)

        if user_id:
            await pipe.srem(f"orders:user:{user_id}", order_id)

        for item in items:

            await pipe.srem(f"orders:product:{item['product_id']}", order_id)

        await pipe.execute()
