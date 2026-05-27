import os
from neo4j import AsyncGraphDatabase

NEO4J_URL = os.getenv("NEO4J_URL", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

driver = None


async def init_db():
    global driver
    driver = AsyncGraphDatabase.driver(
        NEO4J_URL,
        auth=(NEO4J_USER, NEO4J_PASSWORD),
        max_connection_pool_size=50,
        connection_timeout=30,
        max_transaction_retry_time=15,
    )
    await driver.verify_connectivity()
    await _create_indexes()
    print("Neo4j connected")


async def _create_indexes():
    async with driver.session() as session:
        await session.run(
            "CREATE INDEX user_email IF NOT EXISTS FOR (u:User) ON (u.email)"
        )
        await session.run(
            "CREATE INDEX user_name IF NOT EXISTS FOR (u:User) ON (u.name)"
        )
        await session.run(
            "CREATE INDEX product_name IF NOT EXISTS FOR (p:Product) ON (p.name)"
        )
        await session.run(
            "CREATE INDEX product_category IF NOT EXISTS FOR (p:Product) ON (p.category)"
        )
        await session.run(
            "CREATE INDEX order_status IF NOT EXISTS FOR (o:Order) ON (o.status)"
        )
    print("Neo4j indexes created")


async def close_db():
    if driver:
        await driver.close()


def get_driver():
    return driver
