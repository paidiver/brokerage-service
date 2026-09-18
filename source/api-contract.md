# Annotation source API contract

Use this integration path when you already operate a database or annotation service. The database engine, schema, programming language, and hosting platform are your choice. Compatibility is defined at the HTTP boundary.

:::{important}
The canonical machine-readable contract is [`annotations-source-openapi.json`](_static/annotations-source-openapi.json). Download it and use it for implementation, mock generation, validation, and contract tests.
:::

The contract is a focused OpenAPI 3.0.3 subset based on the reference Annotations API OpenAPI document and the typed client used by the Brokerage Service API. Extra response fields are allowed, so an implementation can expose a richer API without breaking brokerage compatibility.

## Required endpoints

All paths are relative to the source base URL.

| Endpoint | Brokerage use |
| --- | --- |
| `GET /health/` | Availability and source discovery. |
| `GET /annotations/search/` | Flat federated annotation search. |
| `GET /annotations/search/grouped/` | Search grouped by annotation set. |
| `GET /annotations/search/export/` | Retrieve export data. |
| `GET /taxonomy/worms/taxa/` | Resolve partial scientific or vernacular taxon names. |
| `GET /images/image_sets/` | List image sets. |
| `GET /images/image_sets/{id}/` | Retrieve an image set. |
| `GET /images/images/` | List images. |
| `GET /images/images/{id}/` | Retrieve an image. |
| `GET /annotations/annotation_sets/` | List annotation sets. |
| `GET /annotations/annotation_sets/{id}/` | Retrieve an annotation set. |
| `GET /annotations/annotations/` | List annotations. |
| `GET /annotations/annotations/{id}/` | Retrieve an annotation. |
| `GET /labels/labels/` | List labels. |
| `GET /labels/labels/{id}/` | Retrieve a label. |

## Base URL

Register a stable HTTPS base URL that precedes the paths above. For example, a source registered as:

```text
https://annotations.example.org/api
```

must serve search at:

```text
https://annotations.example.org/api/annotations/search/
```

Keep trailing-slash behavior consistent or return redirects that preserve the request method and query string.

## Pagination and response envelopes

List endpoints return:

```json
{
  "count": 125,
  "next": "https://annotations.example.org/api/images/images/?page=2",
  "previous": null,
  "results": []
}
```

`count`, `next`, `previous`, and `results` are required. IDs are UUID strings where specified by the OpenAPI document. Date-time values use RFC 3339/ISO 8601.

## Search requirements

The flat search result fields in the OpenAPI contract are required because the broker validates upstream responses before combining them. The source must support repeated array parameters such as `aphia_ids[]=126436`.

When `order_by` is supplied, results must be ascending, nulls last, with ascending search-row UUID as a deterministic tie-breaker. This is essential for incremental multi-source merge sessions. The supported values are:

* `annotation_creation_datetime`
* `label_aphia_id`
* `label_name`

See the imported Brokerage Service API search-session documentation for the full ordering, pagination, consistency, and error semantics.

## Taxonomy

The broker expects WoRMS-shaped taxonomy records containing at least `AphiaID` and `scientificname`. A custom source may obtain these values from any storage or upstream service; it does not have to deploy WoRMS Cache.

## Errors and availability

Return a successful JSON response from `/health/` only when the API is ready to serve brokerage requests. Use meaningful HTTP status codes. A failed or invalid upstream response is not silently merged because doing so could corrupt global ordering and counts.

## Conformance workflow

1. Download [`annotations-source-openapi.json`](_static/annotations-source-openapi.json).
2. Import it into an OpenAPI validator, mock server, or API testing tool.
3. Validate your implementation's requests and responses against the document.
4. Exercise pagination, empty results, null fields, and every supported `order_by` value.
5. Test the source from the Brokerage Service API before requesting registration.

The reference [Annotations API](https://github.com/paidiver/annotations-api) remains the executable example when behavior is unclear.
