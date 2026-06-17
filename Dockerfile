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

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Dev/test/profiling dependencies are installed only when INSTALL_DEV=true
# (e.g. for local Docker Compose). Production builds stay lean.
ARG INSTALL_DEV=false
RUN if [ "$INSTALL_DEV" = "true" ]; then pip install --no-cache-dir -r requirements-dev.txt; fi

COPY . .

EXPOSE 8000

# Run via bash explicitly so the entrypoint works even when the source tree is
# bind-mounted over the image (host file permissions may differ).
ENTRYPOINT ["bash", "/app/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
