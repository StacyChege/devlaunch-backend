# DevLaunch backend — Django + Gunicorn
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Build deps for mysqlclient + Pillow. build-essential/pkg-config/headers are
# only needed to compile the wheels; keep them out of the final layer.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        default-libmysqlclient-dev \
        libjpeg62-turbo-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Collect static now so the image is self-contained; DB isn't touched here.
RUN SECRET_KEY=build DEBUG=False ALLOWED_HOSTS=localhost \
    DB_NAME=x DB_USER=x DB_PASSWORD=x DB_HOST=x DB_PORT=3306 \
    CORS_ALLOWED_ORIGINS=http://localhost \
    STRIPE_SECRET_KEY=x MPESA_CONSUMER_KEY=x MPESA_CONSUMER_SECRET=x \
    python manage.py collectstatic --noinput

RUN chmod +x entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
