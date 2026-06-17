FROM python:3.12-slim

# System libraries required by GeoDjango (PostGIS backend) plus the
# PostgreSQL client used by the entrypoint to wait for the database.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        binutils \
        libproj-dev \
        gdal-bin \
        libgdal-dev \
        libgeos-dev \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Run via bash explicitly so the entrypoint works even when the source tree is
# bind-mounted over the image (host file permissions may differ).
ENTRYPOINT ["bash", "/app/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
