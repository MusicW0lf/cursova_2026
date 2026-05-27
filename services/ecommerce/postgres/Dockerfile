FROM python:3.11-slim

WORKDIR /app

# install uv
RUN pip install uv

# copy dependency files first (for caching)
COPY pyproject.toml uv.lock ./

ARG EXTRA
RUN uv pip install --system ".[postgres]"

# copy service code
COPY services/ecommerce/postgres/app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]