import json
from pathlib import Path

import httpx

APIS = {
    "postgres": "http://localhost:8001",
    "mongo": "http://localhost:8002",
    "neo4j": "http://localhost:8003",
    "redis": "http://localhost:8004",
}


def cleanup_db(name: str, base_url: str):
    print(f"\nCleaning {name}...")
    with httpx.Client(base_url=base_url, timeout=30) as client:
        # delete all orders first (FK constraints)
        orders = client.get("/orders").json()
        for o in orders:
            client.delete(f"/orders/{o['id']}")
        print(f"  {len(orders)} orders deleted")

        # delete all users (cascades remaining orders)
        users = client.get("/users").json()
        for u in users:
            client.delete(f"/users/{u['id']}")
        print(f"  {len(users)} users deleted")

        # delete all products
        products = client.get("/products").json()
        for p in products:
            client.delete(f"/products/{p['id']}")
        print(f"  {len(products)} products deleted")


def main():
    for name, url in APIS.items():
        cleanup_db(name, url)

    # remove seed file if exists
    seed_file = Path(__file__).parent / "seed_data.json"
    if seed_file.exists():
        seed_file.unlink()
        print("\nseed_data.json removed.")

    print("\nCleanup done.")


if __name__ == "__main__":
    main()
