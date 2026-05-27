from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException

from .database import init_db, close_db, get_redis
from . import schemas, crud


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


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
import re

SERVICE_NAME = "redis"  # change per service: mongo, neo4j, redis


def normalize_path(path: str) -> str:
    # replace numeric IDs: /users/123 → /users/{id}
    path = re.sub(r"/\d+", "/{id}", path)
    # replace mongo/neo4j string IDs: /users/6a03f1... → /users/{id}
    path = re.sub(r"/[a-f0-9]{24}", "/{id}", path)
    # replace neo4j element IDs: /users/4:abc:1 → /users/{id}
    path = re.sub(r"/\d+:[a-f0-9-]+:\d+", "/{id}", path)
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
    return "Redis Ecommerce"


# =========================
# USERS
# =========================


@app.post(
    "/users", response_model=schemas.UserResponse, status_code=201, tags=["Users"]
)
async def create_user(user: schemas.UserCreate):
    return await crud.create_user(get_redis(), user)


@app.get("/users", response_model=list[schemas.UserResponse], tags=["Users"])
async def get_users(name: str | None = None):
    return await crud.get_users(get_redis(), name)


@app.get("/users/{user_id}", response_model=schemas.UserResponse, tags=["Users"])
async def get_user(user_id: str):
    return await crud.get_user(get_redis(), user_id)


@app.patch("/users/{user_id}", response_model=schemas.UserResponse, tags=["Users"])
async def update_user(user_id: str, data: schemas.UserUpdate):
    return await crud.update_user(get_redis(), user_id, data)


@app.delete("/users/{user_id}", status_code=204, tags=["Users"])
async def delete_user(user_id: str):
    await crud.delete_user(get_redis(), user_id)


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
    return await crud.create_product(get_redis(), product)


@app.get("/products", response_model=list[schemas.ProductResponse], tags=["Products"])
async def get_products(name: str | None = None):
    return await crud.get_products(get_redis(), name)


@app.get(
    "/products/{product_id}", response_model=schemas.ProductResponse, tags=["Products"]
)
async def get_product(product_id: str):
    return await crud.get_product(get_redis(), product_id)


@app.patch(
    "/products/{product_id}", response_model=schemas.ProductResponse, tags=["Products"]
)
async def update_product(product_id: str, data: schemas.ProductUpdate):
    return await crud.update_product(get_redis(), product_id, data)


@app.delete("/products/{product_id}", status_code=204, tags=["Products"])
async def delete_product(product_id: str):
    await crud.delete_product(get_redis(), product_id)


# =========================
# ORDERS
# =========================


@app.post(
    "/orders", response_model=schemas.OrderResponse, status_code=201, tags=["Orders"]
)
async def create_order(order: schemas.OrderCreate):
    return await crud.create_order(get_redis(), order)


@app.get("/orders", response_model=list[schemas.OrderResponse], tags=["Orders"])
async def get_orders(user_id: str | None = None):
    return await crud.get_orders(get_redis(), user_id)


@app.get("/orders/{order_id}", response_model=schemas.OrderResponse, tags=["Orders"])
async def get_order(order_id: str):
    return await crud.get_order(get_redis(), order_id)


@app.patch("/orders/{order_id}", response_model=schemas.OrderResponse, tags=["Orders"])
async def update_order(order_id: str, data: schemas.OrderUpdate):
    return await crud.update_order(get_redis(), order_id, data)


@app.delete("/orders/{order_id}", status_code=204, tags=["Orders"])
async def delete_order(order_id: str):
    await crud.delete_order(get_redis(), order_id)


@app.get("/")
async def main_url():
    return "Redis Ecommerce"
