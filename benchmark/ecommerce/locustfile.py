import json
import random
from pathlib import Path

from faker import Faker
from locust import HttpUser, task, between, events

fake = Faker()

CATEGORIES = ["Electronics", "Clothing", "Food", "Books", "Sports"]
GENDERS = ["MALE", "FEMALE", "NON_BINARY"]
STATUSES = ["PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"]

MIN_POOL_SIZE = 20  # never delete below this threshold

# =========================
# SEED DATA
# =========================

seed_data: dict = {}


@events.init.add_listener
def load_seed_data(environment, **kwargs):
    global seed_data
    seed_file = Path(__file__).parent / "seed_data.json"
    if not seed_file.exists():
        raise FileNotFoundError("seed_data.json not found — run seed.py first")
    seed_data = json.loads(seed_file.read_text())
    print("Seed data loaded")


# =========================
# HELPERS
# =========================


def make_user_payload():
    return {
        "email": fake.unique.email(),
        "name": fake.name(),
        "username": fake.unique.user_name(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "gender": random.choice(GENDERS),
        "age": random.randint(18, 70),
        "phone": fake.phone_number()[:20],
    }


def make_product_payload():
    return {
        "name": fake.word().capitalize() + " " + fake.word().capitalize(),
        "price": round(random.uniform(1.0, 999.99), 2),
        "description": fake.sentence(),
        "category": random.choice(CATEGORIES),
        "characteristics": {
            "color": fake.color_name(),
            "weight": f"{random.randint(1, 100)}kg",
        },
    }


# =========================
# BASE USER CLASS
# =========================


class EcommerceUser(HttpUser):
    abstract = True
    wait_time = between(0.5, 2)
    db_name: str = None

    def on_start(self):
        self.created_user_ids = []
        self.created_product_ids = []
        self.created_order_ids = []

    def _pool(self, key: str) -> list:
        return seed_data.get(self.db_name, {}).get(key, [])

    def _random_id(self, key: str) -> str | None:
        pool = self._pool(key)
        if not pool:
            return None
        return random.choice(pool)

    def _all_user_ids(self) -> list:
        return self._pool("user_ids") + self.created_user_ids

    def _all_product_ids(self) -> list:
        return self._pool("product_ids") + self.created_product_ids

    def _all_order_ids(self) -> list:
        return self._pool("order_ids") + self.created_order_ids

    # =========================
    # READ TASKS (high frequency)
    # =========================

    @task(10)
    def get_users(self):
        self.client.get("/users", name=f"[{self.db_name}] GET /users")

    @task(10)
    def get_products(self):
        self.client.get("/products", name=f"[{self.db_name}] GET /products")

    @task(10)
    def get_orders(self):
        self.client.get("/orders", name=f"[{self.db_name}] GET /orders")

    @task(8)
    def get_user_by_id(self):
        uid = self._random_id("user_ids")
        if uid:
            self.client.get(f"/users/{uid}", name=f"[{self.db_name}] GET /users/[id]")

    @task(8)
    def get_product_by_id(self):
        pid = self._random_id("product_ids")
        if pid:
            self.client.get(
                f"/products/{pid}", name=f"[{self.db_name}] GET /products/[id]"
            )

    @task(8)
    def get_order_by_id(self):
        oid = self._random_id("order_ids")
        if oid:
            self.client.get(f"/orders/{oid}", name=f"[{self.db_name}] GET /orders/[id]")

    # =========================
    # WRITE TASKS (medium frequency)
    # =========================

    @task(4)
    def create_user(self):
        r = self.client.post(
            "/users", json=make_user_payload(), name=f"[{self.db_name}] POST /users"
        )
        if r.status_code == 201:
            self.created_user_ids.append(str(r.json()["id"]))

    @task(4)
    def create_product(self):
        r = self.client.post(
            "/products",
            json=make_product_payload(),
            name=f"[{self.db_name}] POST /products",
        )
        if r.status_code == 201:
            self.created_product_ids.append(str(r.json()["id"]))

    @task(6)
    def create_order(self):
        user_ids = self._all_user_ids()
        product_ids = self._all_product_ids()
        if not user_ids or not product_ids:
            return
        payload = {
            "user_id": random.choice(user_ids),
            "items": [
                {
                    "product_id": random.choice(product_ids),
                    "quantity": random.randint(1, 10),
                }
                for _ in range(random.randint(1, 5))
            ],
        }
        r = self.client.post(
            "/orders", json=payload, name=f"[{self.db_name}] POST /orders"
        )
        if r.status_code == 201:
            self.created_order_ids.append(str(r.json()["id"]))

    @task(3)
    def update_user(self):
        all_ids = self._all_user_ids()
        if not all_ids:
            return
        uid = random.choice(all_ids)
        self.client.patch(
            f"/users/{uid}",
            json={"first_name": fake.first_name(), "age": random.randint(18, 70)},
            name=f"[{self.db_name}] PATCH /users/[id]",
        )

    @task(3)
    def update_product(self):
        all_ids = self._all_product_ids()
        if not all_ids:
            return
        pid = random.choice(all_ids)
        self.client.patch(
            f"/products/{pid}",
            json={"price": round(random.uniform(1.0, 999.99), 2)},
            name=f"[{self.db_name}] PATCH /products/[id]",
        )

    @task(3)
    def update_order(self):
        all_ids = self._all_order_ids()
        if not all_ids:
            return
        oid = random.choice(all_ids)
        self.client.patch(
            f"/orders/{oid}",
            json={"status": random.choice(STATUSES)},
            name=f"[{self.db_name}] PATCH /orders/[id]",
        )

    # =========================
    # DELETE TASKS (low frequency)
    # =========================

    # @task(1)
    # def delete_user(self):
    #     # prefer deleting locust-created users, fall back to seeded pool if above threshold
    #     if self.created_user_ids:
    #         uid = self.created_user_ids.pop(random.randrange(len(self.created_user_ids)))
    #     elif len(self._pool("user_ids")) > MIN_POOL_SIZE:
    #         uid = self._pool("user_ids").pop(random.randrange(len(self._pool("user_ids"))))
    #     else:
    #         return
    #     self.client.delete(f"/users/{uid}", name=f"[{self.db_name}] DELETE /users/[id]")

    # @task(1)
    # def delete_product(self):
    #     if self.created_product_ids:
    #         pid = self.created_product_ids.pop(random.randrange(len(self.created_product_ids)))
    #     elif len(self._pool("product_ids")) > MIN_POOL_SIZE:
    #         pid = self._pool("product_ids").pop(random.randrange(len(self._pool("product_ids"))))
    #     else:
    #         return
    #     self.client.delete(f"/products/{pid}", name=f"[{self.db_name}] DELETE /products/[id]")

    # @task(1)
    # def delete_order(self):
    #     if self.created_order_ids:
    #         oid = self.created_order_ids.pop(random.randrange(len(self.created_order_ids)))
    #     elif len(self._pool("order_ids")) > MIN_POOL_SIZE:
    #         oid = self._pool("order_ids").pop(random.randrange(len(self._pool("order_ids"))))
    #     else:
    #         return
    #     self.client.delete(f"/orders/{oid}", name=f"[{self.db_name}] DELETE /orders/[id]")


# =========================
# DB-SPECIFIC USER CLASSES
# =========================


class PostgresUser(EcommerceUser):
    host = "http://localhost:8001"
    db_name = "postgres"


class MongoUser(EcommerceUser):
    host = "http://localhost:8002"
    db_name = "mongo"


class Neo4jUser(EcommerceUser):
    host = "http://localhost:8003"
    db_name = "neo4j"


class RedisUser(EcommerceUser):
    host = "http://localhost:8004"
    db_name = "redis"
