# Resources and live services

## Source repositories

| Resource | Repository |
| --- | --- |
| Documentation portal and reusable CI | [paidiver/brokerage-service](https://github.com/paidiver/brokerage-service) |
| Brokerage API | [paidiver/brokerage-service-api](https://github.com/paidiver/brokerage-service-api) |
| Brokerage UI | [paidiver/brokerage-service-ui](https://github.com/paidiver/brokerage-service-ui) |
| Annotations API | [paidiver/annotations-api](https://github.com/paidiver/annotations-api) |
| WoRMS Cache | [paidiver/worms-cache](https://github.com/paidiver/worms-cache) |
| Paidiverpy | [paidiver/paidiverpy](https://github.com/paidiver/paidiverpy) |

The [repository documentation](repos/index) section contains automatically imported READMEs, root Markdown files, and Markdown from each repository's `docs/` and `deployment/` directories.

## Example websites and APIs

| Environment | URL |
| --- | --- |
| Brokerage API, live | <https://brokerage-service-api.paidiver.site> |
| Brokerage API, development | <https://brokerage-service-api-dev.paidiver.site> |
| Brokerage API documentation, live | <https://brokerage-service-api.paidiver.site/docs/> |
| Brokerage API documentation, development | <https://brokerage-service-api-dev.paidiver.site/docs/> |

Deployments may be unavailable during maintenance. Use the health endpoint (`/health/`) to distinguish availability from an API error.

## Database documentation

| Database | SchemaSpy documentation | Schema SQL |
| --- | --- | --- |
| Annotations API | <https://paidiver.github.io/annotations-api/database/> | <https://paidiver.github.io/annotations-api/database/schema.sql> |
| WoRMS Cache | <https://paidiver.github.io/worms-cache/database/> | <https://paidiver.github.io/worms-cache/database/schema.sql> |

## Packages, images, and Helm repositories

Container images are published under the repositories' GitHub Container Registry packages. Helm repositories are served from each project's GitHub Pages root:

```bash
helm repo add annotations-api https://paidiver.github.io/annotations-api
helm repo add worms-cache https://paidiver.github.io/worms-cache
helm repo add brokerage-service-api https://paidiver.github.io/brokerage-service-api
helm repo update
```

Use each imported deployment guide for supported image tags, chart versions, and environment-specific configuration.
