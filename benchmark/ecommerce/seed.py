import argparse
import json
import random
from pathlib import Path

import httpx
from faker import Faker

fake = Faker()

APIS = {
    "postgres": "http://localhost:8001",
    "mongo": "http://localhost:8002",
    "neo4j": "http://localhost:8003",
    "redis": "http://localhost:8004",
}

NUM_USERS = 100
NUM_PRODUCTS = 50
NUM_ORDERS = 500

CATEGORIES = ["Electronics", "Clothing", "Food", "Books", "Sports"]
GENDERS = ["MALE", "FEMALE", "NON_BINARY"]


def make_user():
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


def make_product():
    return {
        "name": f"{fake.word().capitalize()} {random.randint(1, 999999)}",
        "price": round(random.uniform(1.0, 999.99), 2),
        "description": fake.sentence(),
        "category": random.choice(CATEGORIES),
        "characteristics": {
            "color": fake.color_name(),
            "weight": f"{random.randint(1, 100)}kg",
        },
    }


def make_order(user_ids: list, product_ids: list):
    return {
        "user_id": random.choice(user_ids),
        "items": [
            {
                "product_id": random.choice(product_ids),
                "quantity": random.randint(1, 10),
            }
            for _ in range(random.randint(1, 5))
        ],
    }


def seed_db(name: str, base_url: str, users: list, products: list) -> dict:
    print(f"\nSeeding {name}...")

    ids = {"user_ids": [], "product_ids": [], "order_ids": []}

    with httpx.Client(base_url=base_url, timeout=30) as client:

        # USERS
        for u in users:
            r = client.post("/users", json=u)
            r.raise_for_status()
            ids["user_ids"].append(str(r.json()["id"]))

        print(f"  {len(ids['user_ids'])} users created")

        # PRODUCTS
        for p in products:
            r = client.post("/products", json=p)
            r.raise_for_status()
            ids["product_ids"].append(str(r.json()["id"]))

        print(f"  {len(ids['product_ids'])} products created")

        # ORDERS
        for _ in range(NUM_ORDERS):
            order = make_order(ids["user_ids"], ids["product_ids"])

            r = client.post("/orders", json=order)
            r.raise_for_status()

            ids["order_ids"].append(str(r.json()["id"]))

        print(f"  {len(ids['order_ids'])} orders created")

    return ids


def parse_args():
    parser = argparse.ArgumentParser(description="Seed ecommerce databases")

    parser.add_argument(
        "--postgres", action="store_true", help="Seed PostgreSQL database"
    )

    parser.add_argument("--mongo", action="store_true", help="Seed MongoDB database")

    parser.add_argument("--neo4j", action="store_true", help="Seed Neo4j database")

    parser.add_argument("--redis", action="store_true", help="Seed Redis database")

    return parser.parse_args()


def get_selected_apis(args):
    selected = {}

    if args.postgres:
        selected["postgres"] = APIS["postgres"]

    if args.mongo:
        selected["mongo"] = APIS["mongo"]

    if args.neo4j:
        selected["neo4j"] = APIS["neo4j"]

    if args.redis:
        selected["redis"] = APIS["redis"]

    # if no flags passed -> seed all
    if not selected:
        selected = APIS

    return selected


def main():

    args = parse_args()
    selected_apis = get_selected_apis(args)

    print("\nSelected databases:")
    for name in selected_apis:
        print(f" - {name}")

    # generate same dataset for consistency
    users = [make_user() for _ in range(NUM_USERS)]
    products = [make_product() for _ in range(NUM_PRODUCTS)]

    seed_data = {}

    for name, url in selected_apis.items():
        seed_data[name] = seed_db(name, url, users, products)

    out = Path(__file__).parent / "seed_data.json"

    out.write_text(json.dumps(seed_data, indent=2))

    print(f"\nSeed data saved to {out}")


if __name__ == "__main__":
    main()
