# Reusable GitHub Actions

This repository hosts reusable workflows used by the Paidiver service repositories. Caller repositories keep their event triggers and project-specific inputs while common implementation remains here.

## Available workflows

| Workflow | Purpose | Important inputs |
| --- | --- | --- |
| `reusable-docker-build.yml` | Build a Docker image without publishing it. | `dockerfile`, `context` |
| `reusable-docker-push.yml` | Build and publish commit and release/latest tags to GHCR. | `dockerfile`, `context`, `tag_prefix` |
| `reusable-helm-lint.yml` | Run Helm chart-testing lint checks. | `chart_dirs`, `only_changed` |
| `reusable-helm-publish.yml` | Derive a semantic version, package charts, and publish a Helm repository release. | `chart_file`, `charts_dir`, `tag_prefix`, `release_name_template` |
| `reusable-python-django-ci.yml` | Run Ruff/tox and Django tests with PostgreSQL/PostGIS. | `postgres_database`, `postgres_image`, `install_gdal` |
| `reusable-python-tox-ci.yml` | Run a configurable tox environment matrix. | `environments`, `python_version`, `uv_version` |
| `reusable-schemaspy.yml` | Run migrations, generate SchemaSpy/SQL documentation, and preserve Helm files on `gh-pages`. | Compose service names, database values, exclusions |

## Example caller

Reusable workflows are called at job level:

```yaml
name: Build Docker image

on:
  pull_request:

jobs:
  build:
    permissions:
      contents: read
    uses: paidiver/brokerage-service/.github/workflows/reusable-docker-build.yml@main
    with:
      dockerfile: docker/Dockerfile
      context: .
```

Publishing callers must explicitly grant the required token permissions. Docker publishing needs `packages: write`; Helm and SchemaSpy publication need `contents: write`.

## Versioning and access

The examples currently use `@main`. For stable consumers, create a release tag in this repository and reference that tag or, for the strongest supply-chain guarantee, a full commit SHA.

All related repositories are public, so callers do not need cross-repository credentials or an Actions access exception. The caller's automatically generated `GITHUB_TOKEN` is used for writes to the caller repository.

## Responsibilities that remain local

Keep these in the caller repository:

* `push`, `pull_request`, tag, and manual triggers.
* Minimal token permissions.
* Concurrency groups such as `gh-pages`.
* Chart and Dockerfile locations.
* Database/Compose service names and table exclusions.
* Service-specific jobs such as the WoRMS Taxamatch image tests.
