from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from .database import SessionLocal, engine
from . import models, schemas, crud

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    print("Database initialized")
    yield
    print("Shutting down")


app = FastAPI(lifespan=lifespan)


SERVICE_NAME = "postgres"  # change per service: mongo, neo4j, redis


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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# USERS
# =========================


@app.post(
    "/users", response_model=schemas.UserResponse, status_code=201, tags=["Users"]
)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)


@app.get("/users", response_model=list[schemas.UserResponse], tags=["Users"])
def get_users(name: str | None = None, db: Session = Depends(get_db)):
    return crud.get_users(db, name)


@app.get("/users/{user_id}", response_model=schemas.UserResponse, tags=["Users"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    return crud.get_user(db, user_id)


@app.patch("/users/{user_id}", response_model=schemas.UserResponse, tags=["Users"])
def update_user(user_id: int, data: schemas.UserUpdate, db: Session = Depends(get_db)):
    return crud.update_user(db, user_id, data)


@app.delete("/users/{user_id}", status_code=204, tags=["Users"])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    crud.delete_user(db, user_id)


# =========================
# PRODUCTS
# =========================


@app.post(
    "/products",
    response_model=schemas.ProductResponse,
    status_code=201,
    tags=["Products"],
)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    return crud.create_product(db, product)


@app.get("/products", response_model=list[schemas.ProductResponse], tags=["Products"])
def get_products(name: str | None = None, db: Session = Depends(get_db)):
    return crud.get_products(db, name)


@app.get(
    "/products/{product_id}", response_model=schemas.ProductResponse, tags=["Products"]
)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return crud.get_product(db, product_id)


@app.patch(
    "/products/{product_id}", response_model=schemas.ProductResponse, tags=["Products"]
)
def update_product(
    product_id: int, data: schemas.ProductUpdate, db: Session = Depends(get_db)
):
    return crud.update_product(db, product_id, data)


@app.delete("/products/{product_id}", status_code=204, tags=["Products"])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    crud.delete_product(db, product_id)


# =========================
# ORDERS
# =========================


@app.post(
    "/orders", response_model=schemas.OrderResponse, status_code=201, tags=["Orders"]
)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    return crud.create_order(db, order)


@app.get("/orders", response_model=list[schemas.OrderResponse], tags=["Orders"])
def get_orders(user_id: int | None = None, db: Session = Depends(get_db)):
    return crud.get_orders(db, user_id)


@app.get("/orders/{order_id}", response_model=schemas.OrderResponse, tags=["Orders"])
def get_order(order_id: int, db: Session = Depends(get_db)):
    return crud.get_order(db, order_id)


@app.patch("/orders/{order_id}", response_model=schemas.OrderResponse, tags=["Orders"])
def update_order(
    order_id: int, data: schemas.OrderUpdate, db: Session = Depends(get_db)
):
    return crud.update_order(db, order_id, data)


@app.delete("/orders/{order_id}", status_code=204, tags=["Orders"])
def delete_order(order_id: int, db: Session = Depends(get_db)):
    crud.delete_order(db, order_id)


@app.get("/", status_code=200)
def main_url():
    return "Postgres Ecommerce"
