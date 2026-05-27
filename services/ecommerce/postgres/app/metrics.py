from prometheus_client import Summary, Counter, Gauge

from prometheus_client import Histogram

DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds",
    "Time spent executing DB query",
    ["service", "endpoint", "method"],
    buckets=[
        0.001,
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        30.0,
        60.0,
    ],
)

HTTP_REQUEST_COUNT = Counter(
    "http_request_total",
    "Total HTTP requests",
    ["service", "endpoint", "method", "status_code"],
)

HTTP_REQUEST_ERRORS = Counter(
    "http_request_errors_total",
    "Total HTTP request errors",
    ["service", "endpoint", "method"],
)

ACTIVE_REQUESTS = Gauge(
    "http_active_requests", "Currently active requests", ["service"]
)
