# Paidiver Image Brokerage Service documentation

This repository provides the Sphinx documentation portal for the Paidiver image-annotation ecosystem and hosts its reusable GitHub Actions workflows.

The portal combines original cross-service guides with Markdown imported from the public repositories listed in [`repos.yaml`](repos.yaml). For each repository, it imports:

* `README.md` or `README.rst` from the repository root.
* Every Markdown file below `docs/`.
* Every Markdown file below `deployment/`.

## Documentation content

The hand-written guides cover:

* Platform architecture and related resources.
* Two integration paths: a custom contract-compatible API or the provided data stack.
* A downloadable OpenAPI contract for custom annotation sources.
* Repositories, APIs, example sites, database documentation, images, and Helm repositories.
* Local deployment of WoRMS Cache and an independently managed Annotations API.
* Taxonomy, imagery, and annotation ingestion.
* Registering a new Annotations API as a brokerage source.
* Reusing the shared GitHub Actions workflows.

## Build locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
make html-with-repos
python -m http.server --directory build/html 8000
```

Open <http://localhost:8000>.

Use `make html` when editing only local pages and `make html-with-repos` when you also want a fresh copy of related-repository documentation.

## GitHub Pages

The `docs.yml` workflow builds every pull request and deploys the `main` branch through GitHub Pages. Configure the repository's Pages source as **GitHub Actions**.

## Reusable automation

Reusable workflows live in [`.github/workflows`](.github/workflows). See the [reusable CI guide](source/reusable-ci.md) for the workflow catalogue, permissions, inputs, and a caller example.

## Configuration

Edit [`repos.yaml`](repos.yaml) to add, remove, or rename a public GitHub repository. Categories are intentionally not used; every repository appears directly under the repository documentation section.
