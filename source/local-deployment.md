# Deploy a local annotation source

This guide provides two paths. Use the complete demonstration stack to explore everything quickly, or run one Annotations API with one WoRMS Cache when preparing a source that you control.

## Prerequisites

Install Git, Docker Engine, and Docker Compose v2. Allow enough disk space for PostgreSQL/PostGIS images and persistent volumes.

## Option A: complete demonstration stack

The Brokerage Service API repository contains a Compose stack with the broker, Redis, WoRMS Cache, Taxamatch, two example Annotations APIs, their databases, migrations, and sample-data ingestion.

```bash
git clone https://github.com/paidiver/brokerage-service-api.git
cd brokerage-service-api
cp .env.example .env
docker network create shared_services || true
docker compose -f docker/docker-compose.yml up --build
```

When startup completes, open:

* Brokerage API: <http://localhost:8020/>
* Interactive API documentation: <http://localhost:8020/docs/>
* Example annotation sources: <http://localhost:8018/api/> and <http://localhost:8019/api/>

Inspect progress or diagnose startup ordering with:

```bash
docker compose -f docker/docker-compose.yml ps
docker compose -f docker/docker-compose.yml logs -f app
```

Stop containers without deleting database data:

```bash
docker compose -f docker/docker-compose.yml down
```

Add `--volumes` only when you intentionally want to erase the demonstration databases.

## Option B: one independently managed source

Clone the two data services beside each other:

```bash
git clone https://github.com/paidiver/worms-cache.git
git clone https://github.com/paidiver/annotations-api.git
docker network create shared_services || true
```

### Start WoRMS Cache

```bash
cd worms-cache
cp .env.example .env
docker compose -f docker/docker-compose.yml up -d --build
```

The API is available at <http://localhost:8001/api/>. Its PostgreSQL database is exposed on host port `5460`; containers use `worms-db:5432` on the Compose network.

Before production use, replace development passwords, `DJANGO_SECRET_KEY`, and `INGEST_API_TOKEN` in `.env`.

### Start Annotations API

In `annotations-api/.env`, point the cached taxonomy client at the WoRMS Cache service on the shared network:

```env
CACHED_WORMS_API_BASE_URL=http://worms-cache:8000/api
CACHED_WORMS_API_TOKEN=mysecrettoken
```

The token must match `INGEST_API_TOKEN` in `worms-cache/.env`.

```bash
cd ../annotations-api
cp .env.example .env
# Edit .env with the two values above and production-safe secrets.
docker compose -f docker/docker-compose.yml up -d --build
```

The Annotations API is available at <http://localhost:8000/api/>, with interactive documentation at <http://localhost:8000/api/docs/>. Its PostgreSQL/PostGIS database is exposed on host port `5440`; containers use `db:5432`.

### Verify the source

```bash
curl --fail http://localhost:8001/api/health/
curl --fail http://localhost:8000/api/health/
```

After both checks succeed, continue to [data ingestion](data-ingestion) and then [register the source](register-source).

## Production direction

Compose is intended for local development and evaluation. For a durable deployment, use the Helm charts under each repository's `deployment/charts/` directory, external secret management, persistent storage, TLS ingress, backups, monitoring, and pinned image/chart versions. The imported deployment guides document the project-specific release conventions.
