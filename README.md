# DB Benchmark — Cursova 2026

Comparative benchmarking of PostgreSQL, MongoDB, Neo4j, and Redis via four FastAPI microservices with a shared eCommerce domain model.

## Running the Benchmark

```bash
uv run locust -f benchmark/ecommerce/locustfile.py \
  --headless --users 100 --spawn-rate 10 --run-time 5m \
  --csv=benchmark/ecommerce/results --csv-full-history
```

## Services

| Service | URL |
|---|---|
| Postgres API | http://localhost:8001 |
| MongoDB API | http://localhost:8002 |
| Neo4j API | http://localhost:8003 |
| Redis API | http://localhost:8004 |

## Database Credentials

| DB | User | Password |
|---|---|---|
| PostgreSQL | `postgres` | `postgres` |
| MongoDB | — | — |
| Neo4j | `neo4j` | `password` |
| Redis | — | — |

## DB UIs

| Tool | URL | Credentials |
|---|---|---|
| pgAdmin | http://localhost:8080 | `admin@admin.com` / `admin` |
| mongo-express | http://localhost:8081 | — |
| Neo4j Browser | http://localhost:7474 | `neo4j` / `password` |

## Monitoring

| Tool | URL |
|---|---|
| Prometheus | http://localhost:9090 |
| Prometheus Targets | http://localhost:9090/targets |
| Grafana | http://localhost:3000 (`admin` / `admin`) |

### Raw Exporter Metrics

| Exporter | URL |
|---|---|
| Neo4j | http://localhost:2004/metrics |
| PostgreSQL | http://localhost:9187/metrics |
| MongoDB | http://localhost:9216/metrics |
| Redis | http://localhost:9121/metrics |
