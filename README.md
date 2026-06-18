# Wingz — Ride Management API

A RESTful API built with **Django REST Framework** that manages ride information
(`Ride`, `User`, `RideEvent`). It is admin-gated with JWT authentication, ships with
Docker Compose + PostGIS, and is tuned so the Ride List endpoint runs in a fixed,
small number of SQL queries even as the data grows.

---

## Table of contents

- [Tech stack](#tech-stack)
- [Quick start (Docker)](#quick-start-docker)
- [Demo data](#demo-data)
- [Environment variables](#environment-variables)
- [Authentication & roles](#authentication--roles)
- [API reference](#api-reference)
- [Running the tests](#running-the-tests)
- [Linting & formatting](#linting--formatting)
- [Query profiling (dev)](#query-profiling-dev)
- [Bonus: reporting SQL](#bonus-reporting-sql)
- [Architecture & design decisions](#architecture--design-decisions)
- [Project structure](#project-structure)
- [Notes & challenges](#notes--challenges)

---

## Tech stack

- **Python 3.12**, **Django 5.1**, **Django REST Framework**
- **PostgreSQL 16 + PostGIS 3.4** (GeoDjango) — for efficient distance sorting
- **djangorestframework-simplejwt** — JWT auth
- **django-filter** — filtering, **drf-spectacular** — OpenAPI schema/docs
- **Docker / Docker Compose**
- **pytest** + factory_boy (tests), **Ruff** (lint + format), **pre-commit**

---

## Quick start (Docker)

Prerequisites: Docker and Docker Compose.

```bash
# 1. Configure environment (defaults work out of the box for local dev)
cp .env.example .env

# 2. Build and start the stack (db + web). The web container waits for the
#    database, applies migrations, then serves on :8000.
docker compose up --build

# 3. In another shell, create an admin user (role is forced to 'admin')
docker compose exec web python manage.py createsuperuser
```

The API is now at `http://localhost:8000/`.

- Health check: `GET http://localhost:8000/api/health/`
- Interactive docs (Swagger UI): `http://localhost:8000/api/docs/`
- OpenAPI schema: `http://localhost:8000/api/schema/`
- Django admin: `http://localhost:8000/admin/`

Stop the stack with `docker compose down` (add `-v` to also drop the database volume).

---

## Demo data

To populate realistic demo data (~500 rides with events, a pool of riders/drivers, and two known
login users), run the seed command:

```bash
make seed                                  # ~500 rides; no-op if rides already exist
make seed ARGS="--flush --rides 1000"      # wipe and re-seed with a custom volume
# equivalently: docker compose exec web python manage.py seed_demo --flush --rides 1000
```

It can also run automatically on startup (dev only): set `DJANGO_SEED_DEMO=1` in `.env` before
`docker compose up`. It is idempotent, so it never duplicates data on restarts.

The seed creates two known users:

| Role | Email | Password |
|------|-------|----------|
| admin | `admin@example.com` | `AdminPass123` |
| non-admin (rider) | `rider@example.com` | `RiderPass123` |

The non-admin is handy for demonstrating that only admins may call the API (it receives `403`).

---

## Environment variables

Configured via `.env` (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | `change-me-in-production` | Django secret key. **Use a long random value in production.** |
| `DJANGO_DEBUG` | `1` | Debug mode (set `0` in production). |
| `DJANGO_ALLOWED_HOSTS` | `*` | Comma-separated allowed hosts. |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | `wingz` | Database credentials. |
| `POSTGRES_HOST` / `POSTGRES_PORT` | `db` / `5432` | Database host/port (`db` is the compose service). |

---

## Authentication & roles

Authentication is **JWT** (access + refresh). **Every API endpoint requires an
authenticated user whose `role` is `admin`** — non-admins receive `403`, anonymous
requests receive `401`. The only public endpoints are the token endpoints, the health
check, and the schema/docs.

The `User` model has a `role` field (`admin`, `driver`, `rider`). `createsuperuser`
creates an `admin`. Riders and drivers are referenced by rides but cannot call the API.

```bash
# Obtain a token pair
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "your-password"}'
# -> {"access": "<jwt>", "refresh": "<jwt>"}

# Use it
TOKEN="<access token>"
curl http://localhost:8000/api/rides/ -H "Authorization: Bearer $TOKEN"

# Refresh the access token
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<refresh token>"}'
```

The access token also carries a `role` claim.

---

## API reference

All business endpoints live under `/api/` and require a `Bearer` admin token.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/auth/token/` | Obtain access + refresh tokens (public) |
| `POST` | `/api/auth/token/refresh/` | Refresh the access token (public) |
| `GET` / `POST` | `/api/rides/` | List / create rides |
| `GET` / `PATCH` / `DELETE` | `/api/rides/{id}/` | Retrieve / update / delete a ride |
| `GET` / `POST` | `/api/ride-events/` | List / create ride events |
| `GET` / `PATCH` / `DELETE` | `/api/ride-events/{id}/` | Retrieve / update / delete a ride event |
| `GET` / `POST` | `/api/users/` | List / create users |
| `GET` / `PATCH` / `DELETE` | `/api/users/{id}/` | Retrieve / update / delete a user |

### Ride List endpoint

`GET /api/rides/` returns paginated rides. Each ride includes the related **rider** and
**driver** (both as `id_rider` / `id_driver` and as nested objects) and
**`todays_ride_events`** — the ride's events from the last 24 hours only.

Query parameters:

| Parameter | Example | Description |
|-----------|---------|-------------|
| `status` | `?status=pickup` | Filter by ride status (`en-route`, `pickup`, `dropoff`). |
| `rider_email` | `?rider_email=jane@example.com` | Filter by the rider's email (case-insensitive). |
| `ordering` | `?ordering=pickup_time` | Sort by `pickup_time` or `distance` (prefix `-` for descending). |
| `lat`, `lng` | `?ordering=distance&lat=37.77&lng=-122.41` | Target point — **required** when `ordering=distance`. |
| `page`, `page_size` | `?page=2&page_size=50` | Pagination (default size 20, max 100). |

```bash
# Filter by status, then sort by proximity to a GPS point
curl "http://localhost:8000/api/rides/?status=pickup&ordering=distance&lat=37.77&lng=-122.41" \
  -H "Authorization: Bearer $TOKEN"

# Create a ride
curl -X POST http://localhost:8000/api/rides/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
        "status": "en-route",
        "id_rider": 1,
        "id_driver": 2,
        "pickup_latitude": 37.7749,
        "pickup_longitude": -122.4194,
        "dropoff_latitude": 37.8044,
        "dropoff_longitude": -122.2712,
        "pickup_time": "2026-06-17T12:00:00Z"
      }'
```

When `ordering=distance`, each ride also includes a `distance` field (meters to the
target point). Requesting distance ordering without `lat`/`lng` returns `400`.

---

## Running the tests

```bash
make test
```

This runs the pytest suite inside an ephemeral container (it installs the dev
dependencies and uses a dedicated PostGIS test database). The suite covers:

- the **authorization matrix** for every endpoint (admin → `2xx`, non-admin → `403`, anonymous → `401`);
- the JWT login/refresh flow and the `role` claim;
- the Ride List shape, the 24-hour `todays_ride_events` window, filtering, sorting and pagination;
- a **query-count regression test** proving the Ride List uses exactly **3 queries**;
- the bonus reporting SQL.

---

## Linting & formatting

[Ruff](https://docs.astral.sh/ruff/) handles both linting and formatting.

```bash
make install-dev        # install ruff + pre-commit (+ test deps) locally
make lint               # check
make format             # auto-fix + format
make precommit-install  # run Ruff automatically on every commit
```

---

## Query profiling (dev)

[django-silk](https://github.com/jazzband/django-silk) is bundled as an optional,
**dev-only** profiler that records the SQL query count (and the exact SQL) for each request —
handy for confirming the Ride List runs in 3 queries. It is disabled by default and gated
behind an env flag, so it never runs in production.

```bash
# in .env
DJANGO_ENABLE_SILK=1

docker compose up --build   # installs silk and migrates its tables
```

Call any endpoint (e.g. `GET /api/rides/`), then open the profiler at
`http://localhost:8000/silk/`: each request is listed with its query count — click a request
and open the **SQL** tab to inspect the individual queries. Leave `DJANGO_ENABLE_SILK=0` (the
default) for normal use; the test suite always runs with silk off.

> An authenticated `GET /api/rides/` shows **4** queries in silk: one is JWT authentication
> loading the user from the token, and the other **3** are the Ride List itself — the `COUNT`,
> the rides with `rider`/`driver` joined via `select_related`, and the prefetched today's
> events. The query-count test isolates the view (via `force_authenticate`) to assert exactly
> those 3.

---

## Bonus: reporting SQL

Raw SQL that returns the count of trips whose duration (pickup → dropoff) exceeded one
hour, grouped by month and driver. A trip's duration is the time between its
`'Status changed to pickup'` and `'Status changed to dropoff'` `RideEvent`s. The driver
label is the first name plus the last-name initial (e.g. `Chris H`).

The canonical query lives in [`reports/trips_over_one_hour.sql`](reports/trips_over_one_hour.sql):

```sql
SELECT
    to_char(pickup.created_at, 'YYYY-MM')                      AS month,
    concat(driver.first_name, ' ', left(driver.last_name, 1))  AS driver,
    count(*)                                                   AS trips_over_one_hour
FROM rides r
JOIN ride_events pickup
    ON pickup.id_ride = r.id_ride AND pickup.description = 'Status changed to pickup'
JOIN ride_events dropoff
    ON dropoff.id_ride = r.id_ride AND dropoff.description = 'Status changed to dropoff'
JOIN users driver
    ON driver.id_user = r.id_driver
WHERE dropoff.created_at - pickup.created_at > interval '1 hour'
GROUP BY month, driver
ORDER BY month, driver;
```

Run it through the bundled management command:

```bash
docker compose exec web python manage.py trips_over_one_hour
```

Sample output:

```
Month     Driver                Count of Trips > 1 hr
2024-01   Chris H               2
2024-02   Chris H               1
```

> The query assumes one pickup and one dropoff event per ride (per the brief). If a ride
> could have duplicate status events, swap the self-joins for a per-ride aggregate using
> `min(created_at) FILTER (WHERE description = ...)` (noted inside the `.sql` file).

---

## Architecture & design decisions

- **Distance sorting with PostGIS (KNN).** The brief requires distance sorting to be
  efficient on a very large table. `Ride` carries a derived `pickup_point` geography
  column with a **GiST index**; sorting uses the PostGIS KNN operator (`pickup_point <-> point`),
  which is index-assisted, instead of `ST_Distance` (which would scan the whole table).
  `pickup_point` is kept in sync from the latitude/longitude columns in `Ride.save()`;
  the `backfill_pickup_points` management command fills it for bulk-loaded rows.

- **`todays_ride_events` in a fixed query budget.** The Ride List never loads the full
  `RideEvent` table. It uses `select_related("rider", "driver")` (one query, both FKs
  joined) plus a filtered `Prefetch(..., to_attr="todays_events")` for the last-24h events
  (one query). With the pagination `COUNT`, the endpoint is **3 queries total**, regardless
  of page size — enforced by an automated `django_assert_num_queries(3)` test.

- **JWT + role-based authorization.** A single `IsAdminRole` permission gates every
  business ViewSet. JWT is configured with `USER_ID_FIELD = "id_user"` because the custom
  `User` model's primary key is `id_user` (there is no default `id`).

- **Custom `User` model.** Email is the login identifier (the brief has no username), and
  the `role` field is the source of truth for authorization. It is the project's
  `AUTH_USER_MODEL`, set before the first migration.

- **Schema fidelity.** Models use the exact field names from the brief
  (`id_user`, `id_ride`, `id_rider`, `id_driver`, `id_ride_event`) and explicit table names
  (`users`, `rides`, `ride_events`), which keeps the bonus SQL clean. Primary keys are
  `BigAutoField` (BIGINT) given the "very large table" emphasis.

- **Serializers.** Read / Create / Update serializers are separate, fields are listed
  explicitly (never `__all__`), and write serializers reject unknown input fields
  (`StrictFieldsModelSerializer`).

- **Plain DRF JSON** (not JSON:API) and Django-default trailing-slash URLs, for simplicity
  and broad tooling compatibility.

---

## Project structure

```
wingz_api/
├── config/                 # project settings, root urls, wsgi/asgi, health view
├── accounts/               # custom User model, JWT auth, IsAdminRole, UserViewSet
├── rides/                  # Ride & RideEvent models, serializers, filters, viewsets
│   └── management/commands/  # backfill_pickup_points, trips_over_one_hour
├── common/                 # shared base serializer, pagination, test factories
├── reports/                # trips_over_one_hour.sql (bonus)
├── conftest.py             # shared pytest fixtures
├── docker-compose.yml, Dockerfile, entrypoint.sh
├── requirements.txt, requirements-dev.txt
├── pyproject.toml          # Ruff + pytest config
└── Makefile                # lint / format / test / pre-commit helpers
```

---

## Notes & challenges

- **PostGIS KNN needs table statistics.** The GiST index is used for distance ordering
  once PostgreSQL has statistics for the table; on a brand-new, never-analyzed table the
  planner may fall back to a sequential scan. Autovacuum/`ANALYZE` keeps statistics fresh
  in normal operation, so the index is used as the table grows. (Verified with
  `EXPLAIN`: after `ANALYZE`, the plan is an `Index Scan ... Order By: (pickup_point <-> ...)`.)

- **Secret key.** The default dev `DJANGO_SECRET_KEY` is short and triggers a JWT key-length
  warning in tests; set a long, random key in any real deployment.

- **PostGIS extension.** The initial `rides` migration runs `CreateExtension("postgis")`, so
  the project also works on a plain PostgreSQL image (the `postgis/postgis` image already
  provides the extension).

- **Apple Silicon.** The `postgis/postgis` image is `amd64`; on arm64 hosts it runs under
  emulation (works, just slightly slower).
```
