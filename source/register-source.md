# Register an annotation source

The current Brokerage Service API uses version-controlled source configuration. Adding a source therefore requires a small code change and a brokerage deployment. The source API remains independently hosted and may be either a custom [contract implementation](api-contract) or the provided Annotations API stack.

## Requirements for a source

Before registration, the source should:

* Implement the machine-readable [Annotations Source API contract](api-contract).
* Expose a reachable `/api/health/` endpoint.
* Support the search ordering and pagination contract documented by the Brokerage Service API.
* Use HTTPS and a stable base URL in deployed environments.
* Return public data without sharing administrative or ingestion credentials with the broker.

## 1. Add the source definition

Fork or clone [brokerage-service-api](https://github.com/paidiver/brokerage-service-api), then add an entry to `src/brokerage_service_api/fixtures/source.yaml`:

```yaml
sources:
  my_institute:
    source_name: "my_institute"
    label: "My Institute Annotations"
    base_url: "MY_INSTITUTE_ANNOTATIONS_API_URL"
    enabled: true
    kind: "annotations_v1"
    timeout:
      connect: 5.0
      read: 30.0
      write: 30.0
      pool: 5.0
```

Use a stable lowercase identifier for the YAML key and `source_name`.

## 2. Register the environment mapping

Add the corresponding mapping to `src/brokerage_service_api/fixtures/constants.py`:

```python
ENV_SOURCE_URL_MAP = {
    # Existing mappings...
    "my_institute": (
        "MY_INSTITUTE_ANNOTATIONS_API_URL",
        "http://annotations-api:8000/api/",
    ),
}
```

The first value names the production environment variable. The second is a local-development fallback.

## 3. Configure the base URL

Set the variable in the brokerage deployment, including the `/api/` prefix:

```env
MY_INSTITUTE_ANNOTATIONS_API_URL=https://annotations.example.org/api/
```

For Docker Compose, add the variable to `.env`. For Helm, add it through the chart values/secret mechanism described in the imported deployment documentation.

## 4. Test and deploy

```bash
uv run --locked --no-default-groups --group test tox -e lint
uv run --locked --no-default-groups --group test tox -e py313
```

Restart or deploy the Brokerage Service API, then verify discovery:

```bash
curl --fail http://localhost:8020/api/sources/
```

Confirm that the new source is reported as healthy and run a federated annotation search that explicitly selects it. If the broker reports `upstream_invalid` or `upstream_ordering`, compare the source implementation with the imported search-session ordering contract.

## 5. Submit the source upstream

When the source should appear in the shared public brokerage deployment, open a pull request against `paidiver/brokerage-service-api` containing:

* The source definition and environment mapping.
* Tests for configuration loading and source discovery.
* The public base URL and an operational contact.
* Evidence that health, pagination, ordering, and search responses satisfy the contract.

Do not commit API tokens, database passwords, or other source secrets.
