FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app

# Установка системных зависимостей и Nginx
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Установка пакетного менеджера uv
RUN pip install --no-cache-dir uv

# Копирование зависимостей и установка
COPY requirements.txt ./
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Копирование исходного кода, моделей, данных
COPY scripts/ ./scripts/
COPY data/ ./data/
COPY ranker.pkl ./

# Копирование фронтенда и конфигурации Nginx
COPY frontend/index.html /usr/share/nginx/html/index.html
COPY frontend/default.conf /etc/nginx/conf.d/default.conf

# Удаление дефолтного конфига nginx
RUN rm -f /etc/nginx/sites-enabled/default

# Копирование и права на entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Yandex Serverless Containers принимают трафик на порту 8080
EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]