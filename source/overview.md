# Platform overview

The Paidiver Image Brokerage Service makes independently operated image-annotation APIs discoverable through one federated API and user interface. Data owners retain their own annotation database and deployment while the brokerage service provides a common point for discovery and search.

## Components

| Component | Responsibility |
| --- | --- |
| [Brokerage Service API](https://github.com/paidiver/brokerage-service-api) | Discovers configured sources, federates searches, monitors source health, and caches search sessions in Redis. |
| [Brokerage Service UI](https://github.com/paidiver/brokerage-service-ui) | User-facing search and discovery interface. |
| [Annotations API](https://github.com/paidiver/annotations-api) | Stores image, annotation, label, and related metadata in PostgreSQL/PostGIS. Each organisation can operate its own instance. |
| [WoRMS Cache](https://github.com/paidiver/worms-cache) | Caches marine taxonomy, classification, synonyms, vernacular names, and name indexes used by annotation workflows. |
| [Paidiverpy](https://github.com/paidiver/paidiverpy) | Processing tools used elsewhere in the Paidiver ecosystem. |

## Data flow

1. A data provider deploys an Annotations API and PostgreSQL/PostGIS database.
2. The Annotations API uses the WoRMS Cache to resolve and ingest taxonomic labels.
3. The provider imports imagery metadata and annotations into its API.
4. A source entry is added to the Brokerage Service API configuration.
5. The brokerage validates the source and includes it in discovery and federated searches.
6. Users access the source through the Brokerage API or UI while the provider remains responsible for its own data and service.

## Documentation model

This site combines hand-written cross-service guides with documentation imported from every public repository in [`repos.yaml`](https://github.com/paidiver/brokerage-service/blob/main/repos.yaml). Each build imports root Markdown files and all Markdown below `docs/` and `deployment/`, so repository documentation remains close to its implementation.
