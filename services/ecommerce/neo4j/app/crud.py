from datetime import datetime, timezone
import json
from fastapi import HTTPException
from neo4j import AsyncDriver

from . import schemas


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# =========================
# USERS
# =========================


async def create_user(
    driver: AsyncDriver, user: schemas.UserCreate
) -> schemas.UserResponse:
    async with driver.session() as session:
        result = await session.run(
            """
            CREATE (u:User {
                email: $email,
                name: $name,
                username: $username,
                first_name: $first_name,
                last_name: $last_name,
                gender: $gender,
                age: $age,
                phone: $phone,
                created_at: $created_at,
                updated_at: $updated_at
            })
            RETURN elementId(u) AS id, u.email AS email, u.name AS name,
                   u.username AS username, u.first_name AS first_name,
                   u.last_name AS last_name, u.gender AS gender,
                   u.age AS age, u.phone AS phone,
                   u.created_at AS created_at, u.updated_at AS updated_at
            """,
            email=user.email,
            name=user.name,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            gender=user.gender.value if user.gender else None,
            age=user.age,
            phone=user.phone,
            created_at=_now(),
            updated_at=_now(),
        )
        record = await result.single()
        return schemas.UserResponse(**record.data())


async def get_users(
    driver: AsyncDriver, name: str | None = None
) -> list[schemas.UserResponse]:
    async with driver.session() as session:
        if name:
            result = await session.run(
                """
                MATCH (u:User)
                WHERE toLower(u.name) CONTAINS toLower($name)
                RETURN elementId(u) AS id, u.email AS email, u.name AS name,
                       u.username AS username, u.first_name AS first_name,
                       u.last_name AS last_name, u.gender AS gender,
                       u.age AS age, u.phone AS phone,
                       u.created_at AS created_at, u.updated_at AS updated_at
                """,
                name=name,
            )
        else:
            result = await session.run("""
                MATCH (u:User)
                RETURN elementId(u) AS id, u.email AS email, u.name AS name,
                       u.username AS username, u.first_name AS first_name,
                       u.last_name AS last_name, u.gender AS gender,
                       u.age AS age, u.phone AS phone,
                       u.created_at AS created_at, u.updated_at AS updated_at
                """)
        records = await result.data()
        return [schemas.UserResponse(**r) for r in records]


async def get_user(driver: AsyncDriver, user_id: str) -> schemas.UserResponse:
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (u:User) WHERE elementId(u) = $user_id
            RETURN elementId(u) AS id, u.email AS email, u.name AS name,
                   u.username AS username, u.first_name AS first_name,
                   u.last_name AS last_name, u.gender AS gender,
                   u.age AS age, u.phone AS phone,
                   u.created_at AS created_at, u.updated_at AS updated_at
            """,
            user_id=user_id,
        )
        record = await result.single()
        if not record:
            raise HTTPException(status_code=404, detail="User not found")
        return schemas.UserResponse(**record.data())


async def update_user(
    driver: AsyncDriver, user_id: str, data: schemas.UserUpdate
) -> schemas.UserResponse:
    async with driver.session() as session:
        # check exists
        check = await session.run(
            "MATCH (u:User) WHERE elementId(u) = $user_id RETURN u", user_id=user_id
        )
        if not await check.single():
            raise HTTPException(status_code=404, detail="User not found")

        updates = data.model_dump(exclude_none=True)
        if "gender" in updates:
            updates["gender"] = updates["gender"].value
        updates["updated_at"] = _now()

        result = await session.run(
            """
            MATCH (u:User) WHERE elementId(u) = $user_id
            SET u += $updates
            RETURN elementId(u) AS id, u.email AS email, u.name AS name,
                   u.username AS username, u.first_name AS first_name,
                   u.last_name AS last_name, u.gender AS gender,
                   u.age AS age, u.phone AS phone,
                   u.created_at AS created_at, u.updated_at AS updated_at
            """,
            user_id=user_id,
            updates=updates,
        )
        record = await result.single()
        return schemas.UserResponse(**record.data())


async def delete_user(driver: AsyncDriver, user_id: str) -> None:
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (u:User) WHERE elementId(u) = $user_id
            OPTIONAL MATCH (o:Order)-[:BY]->(u)
            DETACH DELETE o, u
            RETURN count(u) AS deleted
            """,
            user_id=user_id,
        )
        record = await result.single()
        if not record or record["deleted"] == 0:
            raise HTTPException(status_code=404, detail="User not found")


# =========================
# PRODUCTS
# =========================


async def create_product(
    driver: AsyncDriver, product: schemas.ProductCreate
) -> schemas.ProductResponse:
    async with driver.session() as session:
        result = await session.run(
            """
            CREATE (p:Product {
                name: $name,
                price: $price,
                description: $description,
                category: $category,
                characteristics: $characteristics,
                created_at: $created_at,
                updated_at: $updated_at
            })
            RETURN elementId(p) AS id, p.name AS name, p.price AS price,
                   p.description AS description, p.category AS category,
                   p.characteristics AS characteristics,
                   p.created_at AS created_at, p.updated_at AS updated_at
            """,
            name=product.name,
            price=product.price,
            description=product.description,
            category=product.category,
            characteristics=(
                json.dumps(product.characteristics) if product.characteristics else None
            ),
            created_at=_now(),
            updated_at=_now(),
        )
        record = await result.single()
        data = record.data()
        if data.get("characteristics"):
            data["characteristics"] = json.loads(data["characteristics"])
        return schemas.ProductResponse(**data)


async def get_products(
    driver: AsyncDriver, name: str | None = None
) -> list[schemas.ProductResponse]:

    async with driver.session() as session:

        if name:
            result = await session.run(
                """
                MATCH (p:Product)
                WHERE toLower(p.name) CONTAINS toLower($name)

                RETURN elementId(p) AS id,
                       p.name AS name,
                       p.price AS price,
                       p.description AS description,
                       p.category AS category,
                       p.characteristics AS characteristics,
                       p.created_at AS created_at,
                       p.updated_at AS updated_at
                """,
                name=name,
            )

        else:
            result = await session.run("""
                MATCH (p:Product)

                RETURN elementId(p) AS id,
                       p.name AS name,
                       p.price AS price,
                       p.description AS description,
                       p.category AS category,
                       p.characteristics AS characteristics,
                       p.created_at AS created_at,
                       p.updated_at AS updated_at
                """)

        # <-- moved OUTSIDE else block

        records = await result.data()

        products = []

        for r in records:

            if r.get("characteristics"):
                r["characteristics"] = json.loads(r["characteristics"])

            products.append(schemas.ProductResponse(**r))

        return products


async def get_product(driver: AsyncDriver, product_id: str) -> schemas.ProductResponse:
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (p:Product) WHERE elementId(p) = $product_id
            RETURN elementId(p) AS id, p.name AS name, p.price AS price,
                   p.description AS description, p.category AS category,
                   p.characteristics AS characteristics,
                   p.created_at AS created_at, p.updated_at AS updated_at
            """,
            product_id=product_id,
        )
        record = await result.single()
        if not record:
            raise HTTPException(status_code=404, detail="Product not found")
        data = record.data()
        if data.get("characteristics"):
            data["characteristics"] = json.loads(data["characteristics"])

        return schemas.ProductResponse(**data)


async def update_product(
    driver: AsyncDriver, product_id: str, data: schemas.ProductUpdate
) -> schemas.ProductResponse:
    async with driver.session() as session:
        check = await session.run(
            "MATCH (p:Product) WHERE elementId(p) = $product_id RETURN p",
            product_id=product_id,
        )
        if not await check.single():
            raise HTTPException(status_code=404, detail="Product not found")

        updates = data.model_dump(exclude_none=True)
        updates["updated_at"] = _now()
        if "characteristics" in updates:
            updates["characteristics"] = json.dumps(updates["characteristics"])

        result = await session.run(
            """
            MATCH (p:Product) WHERE elementId(p) = $product_id
            SET p += $updates
            RETURN elementId(p) AS id, p.name AS name, p.price AS price,
                   p.description AS description, p.category AS category,
                   p.characteristics AS characteristics,
                   p.created_at AS created_at, p.updated_at AS updated_at
            """,
            product_id=product_id,
            updates=updates,
        )
        record = await result.single()
        data = record.data()
        if data.get("characteristics"):
            data["characteristics"] = json.loads(data["characteristics"])
        return schemas.ProductResponse(**data)


async def delete_product(driver: AsyncDriver, product_id: str) -> None:
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (p:Product) WHERE elementId(p) = $product_id
            OPTIONAL MATCH (o:Order)-[:CONTAINS]->(p)
            DETACH DELETE o, p
            RETURN count(p) AS deleted
            """,
            product_id=product_id,
        )
        record = await result.single()
        if not record or record["deleted"] == 0:
            raise HTTPException(status_code=404, detail="Product not found")


# =========================
# ORDERS
# =========================


async def create_order(
    driver: AsyncDriver, order: schemas.OrderCreate
) -> schemas.OrderResponse:

    async with driver.session() as session:

        items_data = [
            {"product_id": item.product_id, "quantity": item.quantity}
            for item in order.items
        ]

        created_at = _now()
        updated_at = _now()

        result = await session.run(
            """
            MATCH (u:User) WHERE elementId(u) = $user_id

            CREATE (o:Order {
                status: $status,
                total_price: 0,
                created_at: $created_at,
                updated_at: $updated_at
            })
            CREATE (o)-[:BY]->(u)

            WITH o, u

            UNWIND $items AS item
            MATCH (p:Product) WHERE elementId(p) = item.product_id

            CREATE (o)-[:CONTAINS {quantity: item.quantity}]->(p)

            WITH o, u, collect({
                product_id: elementId(p),
                quantity: item.quantity,
                price: p.price
            }) AS resolved

            SET o.total_price = reduce(total = 0.0, i IN resolved | total + i.price * i.quantity)

            RETURN
                elementId(o) AS id,
                elementId(u) AS user_id,
                o.status AS status,
                o.total_price AS total_price,
                o.created_at AS created_at,
                o.updated_at AS updated_at,
                resolved AS items
            """,
            user_id=order.user_id,
            items=items_data,
            status=schemas.OrderStatus.PENDING.value,
            created_at=created_at,
            updated_at=updated_at,
        )

        record = await result.single()

        if not record:
            raise HTTPException(status_code=404, detail="User not found")

        data = record.data()

        return schemas.OrderResponse(
            id=data["id"],
            user_id=data["user_id"],
            items=[
                schemas.OrderItemResponse(
                    product_id=i["product_id"], quantity=i["quantity"]
                )
                for i in data["items"]
            ],
            status=data["status"],
            total_price=data["total_price"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


async def get_order(driver: AsyncDriver, order_id: str) -> schemas.OrderResponse:
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (o:Order) WHERE elementId(o) = $order_id
            MATCH (o)-[:BY]->(u:User)
            OPTIONAL MATCH (o)-[r:CONTAINS]->(p:Product)
            RETURN
                elementId(o) AS id,
                elementId(u) AS user_id,
                o.status AS status,
                o.total_price AS total_price,
                o.created_at AS created_at,
                o.updated_at AS updated_at,
                collect({
                    product_id: elementId(p),
                    quantity: r.quantity
                }) AS items
            """,
            order_id=order_id,
        )
        record = await result.single()
        if not record:
            raise HTTPException(status_code=404, detail="Order not found")

        data = record.data()
        items = [
            schemas.OrderItemResponse(**item)
            for item in data["items"]
            if item["product_id"] is not None
        ]
        return schemas.OrderResponse(
            id=data["id"],
            user_id=data["user_id"],
            items=items,
            status=data["status"],
            total_price=data["total_price"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


async def get_orders(
    driver: AsyncDriver, user_id: str | None = None
) -> list[schemas.OrderResponse]:
    async with driver.session() as session:
        if user_id:
            result = await session.run(
                """
                MATCH (u:User) WHERE elementId(u) = $user_id
                MATCH (o:Order)-[:BY]->(u)
                WITH o, u
                OPTIONAL MATCH (o)-[r:CONTAINS]->(p:Product)
                RETURN
                    elementId(o) AS id,
                    elementId(u) AS user_id,
                    o.status AS status,
                    o.total_price AS total_price,
                    o.created_at AS created_at,
                    o.updated_at AS updated_at,
                    collect({product_id: elementId(p), quantity: r.quantity}) AS items
                """,
                user_id=user_id,
            )
        else:
            result = await session.run(
                """
                MATCH (o:Order)-[:BY]->(u:User)
                WITH o, u
                OPTIONAL MATCH (o)-[r:CONTAINS]->(p:Product)
                RETURN
                    elementId(o) AS id,
                    elementId(u) AS user_id,
                    o.status AS status,
                    o.total_price AS total_price,
                    o.created_at AS created_at,
                    o.updated_at AS updated_at,
                    collect({product_id: elementId(p), quantity: r.quantity}) AS items
                """
            )

        records = await result.data()
        if not records:
            return []

        orders = []
        for r in records:
            items = [
                schemas.OrderItemResponse(**item)
                for item in r["items"]
                if item["product_id"] is not None
            ]
            orders.append(
                schemas.OrderResponse(
                    id=r["id"],
                    user_id=r["user_id"],
                    items=items,
                    status=r["status"],
                    total_price=r["total_price"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
            )
        return orders


async def update_order(
    driver: AsyncDriver, order_id: str, data: schemas.OrderUpdate
) -> schemas.OrderResponse:

    async with driver.session() as session:

        updates = data.model_dump(exclude_none=True)

        if "status" in updates:
            updates["status"] = updates["status"].value

        updates["updated_at"] = _now()

        result = await session.run(
            """
            MATCH (o:Order)
            WHERE elementId(o) = $order_id

            SET o += $updates

            WITH o

            MATCH (o)-[:BY]->(u:User)
            OPTIONAL MATCH (o)-[r:CONTAINS]->(p:Product)

            RETURN
                elementId(o) AS id,
                elementId(u) AS user_id,
                o.status AS status,
                o.total_price AS total_price,
                o.created_at AS created_at,
                o.updated_at AS updated_at,
                collect({
                    product_id: elementId(p),
                    quantity: r.quantity
                }) AS items
            """,
            order_id=order_id,
            updates=updates,
        )

        record = await result.single()

        if not record:
            raise HTTPException(status_code=404, detail="Order not found")

        data = record.data()

        items = [
            schemas.OrderItemResponse(**item)
            for item in data["items"]
            if item["product_id"] is not None
        ]

        return schemas.OrderResponse(
            id=data["id"],
            user_id=data["user_id"],
            items=items,
            status=data["status"],
            total_price=data["total_price"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


async def delete_order(driver: AsyncDriver, order_id: str) -> None:

    async with driver.session() as session:

        result = await session.run(
            """
            MATCH (o:Order)
            WHERE elementId(o) = $order_id

            DETACH DELETE o

            RETURN count(o) AS deleted
            """,
            order_id=order_id,
        )

        record = await result.single()

        if not record or record["deleted"] == 0:
            raise HTTPException(status_code=404, detail="Order not found")
