# Brokerage Service shared automation

This repository hosts reusable GitHub Actions workflows for the Paidiver
services. Callers reference workflows from `.github/workflows` using:

```yaml
jobs:
  build:
    uses: paidiver/brokerage-service/.github/workflows/reusable-docker-build.yml@main
```

Available workflows cover Docker builds and pushes, Helm linting and releases,
Django/tox CI, generic tox matrices, and SchemaSpy database documentation.

If this repository is private, enable access under **Settings → Actions →
General → Access** so the other repositories in the `paidiver` organization can
call these workflows. Once the workflows are stable, create a release tag and
pin callers to that tag instead of `main`.
