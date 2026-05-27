To run locust tests: uv run locust -f benchmark/ecommerce/locustfile.py --headless --users 100 --spawn-rate 10 --run-time 5m --csv=benchmark/ecommerce/results --csv-full-history



Postgres — user: postgres, password: postgres
MongoDB — no auth configured
Neo4j — user: neo4j, password: password
Redis — no auth configured

APIs:
http://localhost:8001  → Postgres FastAPI
http://localhost:8002  → Mongo FastAPI
http://localhost:8003  → Neo4j FastAPI
http://localhost:8004  → Redis FastAPI
DB UIs:
http://localhost:8080  → pgAdmin (admin@admin.com / admin)
http://localhost:8081  → mongo-express
http://localhost:7474  → Neo4j Browser (neo4j / password)
Monitoring:
http://localhost:9090  → Prometheus
http://localhost:9090/targets  → Prometheus targets 

http://localhost:3000  → Grafana (admin / admin)
http://localhost:2004/metrics  → Neo4j raw metrics
http://localhost:9187/metrics  → Postgres exporter raw metrics
http://localhost:9216/metrics  → MongoDB exporter raw metrics
http://localhost:9121/metrics  → Redis exporter raw metrics