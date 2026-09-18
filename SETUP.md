# Documentation setup

## Requirements

* Python 3.10 or newer
* GNU Make, or `sphinx-build` directly on Windows
* Internet access to public GitHub repositories

No access token is required because every configured repository is public.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1`.

## Commands

| Command | Description |
| --- | --- |
| `make html` | Build hand-written local documentation. |
| `make fetch-repos` | Refresh imported Markdown from repositories in `repos.yaml`. |
| `make html-with-repos` | Refresh imported documentation and build the complete site. |
| `make clean-repos` | Remove generated `source/repos/` content. |
| `make clean` | Remove Sphinx build output. |

Preview a completed build with:

```bash
python -m http.server --directory build/html 8000
```

## Add portal content

Create Markdown or reStructuredText under `source/`, then add it to a toctree in `source/index.rst`.

## Add a repository

Add an entry to `repos.yaml`:

```yaml
repositories:
  - path: paidiver/example-repository
    name: example-repository
    title: Example Repository
    branch: main
    source: github
```

The importer copies only `README.md` or `README.rst` from the repository root, plus every Markdown file below `docs/` and `deployment/`. Other repository files remain linked to their source on GitHub.

## Refresh documentation after source-repository changes

The source repositories call `.github/workflows/reusable-trigger-docs.yml` after a push to `main`. The reusable workflow sends a `source-docs-updated` repository dispatch to this repository, which starts the normal documentation build and deployment.

Create a fine-grained personal access token or GitHub App token with **Contents: read and write** access to `paidiver/brokerage-service`. Add it as an Actions secret named `BROKERAGE_DOCS_TOKEN` to each source repository, or as an organization secret shared with these repositories:

* `paidiver/brokerage-service-api`
* `paidiver/brokerage-service-ui`
* `paidiver/worms-cache`
* `paidiver/annotations-api`

The repositories are public, so the documentation importer needs no credentials. The token is required only because GitHub does not allow a repository's built-in `GITHUB_TOKEN` to dispatch an event to another repository.
