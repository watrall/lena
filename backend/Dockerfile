# syntax=docker/dockerfile:1.6

FROM python:3.11-slim AS base

# Create non-root user for security
RUN groupadd --gid 1000 lena && \
    useradd --uid 1000 --gid lena --shell /bin/bash --create-home lena

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Switch to non-root user
USER lena

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
