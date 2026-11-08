FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY requirements.txt ./
RUN uv pip install --system --no-cache-dir -r requirements.txt

COPY scripts/ ./scripts/
COPY data/item_features.parquet ./data/item_features.parquet
COPY ranker.pkl ./

COPY frontend/index.html /usr/share/nginx/html/index.html
COPY frontend/default.conf /etc/nginx/conf.d/default.conf

RUN rm -f /etc/nginx/sites-enabled/default

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]