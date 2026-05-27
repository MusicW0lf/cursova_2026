from contextlib import asynccontextmanager
from fastapi import FastAPI

from .database import init_db, close_db
from . import models, schemas, crud


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db([models.User, models.Product, models.Order])
    print("MongoDB initialized")
    yield
    await close_db()
    print("Shutting down")


def _user_response(u: models.User) -> schemas.UserResponse:
    return schemas.UserResponse(
        id=str(u.id),
        email=u.email,
        name=u.name,
        username=u.username,
        first_name=u.first_name,
        last_name=u.last_name,
        gender=u.gender,
        age=u.age,
        phone=u.phone,
        created_at=u.created_at,
        updated_at=u.updated_at,
    )


def _product_response(p: models.Product) -> schemas.ProductResponse:
    return schemas.ProductResponse(
        id=str(p.id),
        name=p.name,
        price=p.price,
        description=p.description,
        category=p.category,
        characteristics=p.characteristics,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _order_response(o: models.Order) -> schemas.OrderResponse:
    return schemas.OrderResponse(
        id=str(o.id),
        user_id=o.user_id,
        items=[
            schemas.OrderItemResponse(
                product_id=item.product_id, quantity=item.quantity
            )
            for item in o.items
        ],
        status=o.status,
        total_price=o.total_price,
        created_at=o.created_at,
        updated_at=o.updated_at,
    )


app = FastAPI(lifespan=lifespan)


import time
from prometheus_client import make_asgi_app
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from .metrics import (
    DB_QUERY_DURATION,
    HTTP_REQUEST_COUNT,
    HTTP_REQUEST_ERRORS,
    ACTIVE_REQUESTS,
)

SERVICE_NAME = "mongo"  # change per service: mongo, neo4j, redis
import re


def normalize_path(path: str) -> str:
    # mongo ObjectIds first (24-char hex) — before numeric check
    path = re.sub(r"/[a-f0-9]{24}", "/{id}", path, flags=re.IGNORECASE)
    # neo4j element IDs: 4:abc123:1
    path = re.sub(r"/\d+:[a-f0-9-]+:\d+", "/{id}", path)
    # numeric IDs last
    path = re.sub(r"/\d+", "/{id}", path)
    return path


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        endpoint = normalize_path(request.url.path)
        method = request.method

        if endpoint.startswith("/metrics"):
            return await call_next(request)

        ACTIVE_REQUESTS.labels(service=SERVICE_NAME).inc()
        start = time.perf_counter()

        try:
            response = await call_next(request)
            duration = time.perf_counter() - start

            DB_QUERY_DURATION.labels(
                service=SERVICE_NAME, endpoint=endpoint, method=method
            ).observe(duration)

            HTTP_REQUEST_COUNT.labels(
                service=SERVICE_NAME,
                endpoint=endpoint,
                method=method,
                status_code=response.status_code,
            ).inc()

            # count 4xx and 5xx as errors
            if response.status_code >= 400:
                HTTP_REQUEST_ERRORS.labels(
                    service=SERVICE_NAME, endpoint=endpoint, method=method
                ).inc()

            return response

        except Exception as e:
            HTTP_REQUEST_ERRORS.labels(
                service=SERVICE_NAME, endpoint=endpoint, method=method
            ).inc()
            raise e

        finally:
            ACTIVE_REQUESTS.labels(service=SERVICE_NAME).dec()


app.add_middleware(MetricsMiddleware)

# mount /metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/", status_code=200)
async def root():
    return "Mongo Ecommerce"


# =========================
# USERS
# =========================


@app.post(
    "/users", response_model=schemas.UserResponse, status_code=201, tags=["Users"]
)
async def create_user(user: schemas.UserCreate):
    return _user_response(await crud.create_user(user))


@app.get("/users", response_model=list[schemas.UserResponse], tags=["Users"])
async def get_users(name: str | None = None):
    return [_user_response(u) for u in await crud.get_users(name)]


@app.get("/users/{user_id}", response_model=schemas.UserResponse, tags=["Users"])
async def get_user(user_id: str):
    return _user_response(await crud.get_user(user_id))


@app.patch("/users/{user_id}", response_model=schemas.UserResponse, tags=["Users"])
async def update_user(user_id: str, data: schemas.UserUpdate):
    return _user_response(await crud.update_user(user_id, data))


@app.delete("/users/{user_id}", status_code=204, tags=["Users"])
async def delete_user(user_id: str):
    await crud.delete_user(user_id)


# =========================
# PRODUCTS
# =========================
@app.post(
    "/products",
    response_model=schemas.ProductResponse,
    status_code=201,
    tags=["Products"],
)
async def create_product(product: schemas.ProductCreate):
    return _product_response(await crud.create_product(product))


@app.get("/products", response_model=list[schemas.ProductResponse], tags=["Products"])
async def get_products(name: str | None = None):
    return [_product_response(p) for p in await crud.get_products(name)]


@app.get(
    "/products/{product_id}", response_model=schemas.ProductResponse, tags=["Products"]
)
async def get_product(product_id: str):
    return _product_response(await crud.get_product(product_id))


@app.patch(
    "/products/{product_id}", response_model=schemas.ProductResponse, tags=["Products"]
)
async def update_product(product_id: str, data: schemas.ProductUpdate):
    return _product_response(await crud.update_product(product_id, data))


@app.delete("/products/{product_id}", status_code=204, tags=["Products"])
async def delete_product(product_id: str):
    await crud.delete_product(product_id)


# =========================
# ORDERS
# =========================


@app.post(
    "/orders", response_model=schemas.OrderResponse, status_code=201, tags=["Orders"]
)
async def create_order(order: schemas.OrderCreate):
    return _order_response(await crud.create_order(order))


@app.get("/orders", response_model=list[schemas.OrderResponse], tags=["Orders"])
async def get_orders(user_id: str | None = None):
    return [_order_response(o) for o in await crud.get_orders(user_id)]


@app.get("/orders/{order_id}", response_model=schemas.OrderResponse, tags=["Orders"])
async def get_order(order_id: str):
    return _order_response(await crud.get_order(order_id))


@app.patch("/orders/{order_id}", response_model=schemas.OrderResponse, tags=["Orders"])
async def update_order(order_id: str, data: schemas.OrderUpdate):
    return _order_response(await crud.update_order(order_id, data))


@app.delete("/orders/{order_id}", status_code=204, tags=["Orders"])
async def delete_order(order_id: str):
    await crud.delete_order(order_id)


@app.get("/")
async def main_url():
    return "Mongodb Ecommerce"
