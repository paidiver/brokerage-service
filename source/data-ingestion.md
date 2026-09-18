# Ingest data

Populate taxonomy before importing annotation labels that refer to AphiaIDs. Then create an Annotations API user/token and ingest imagery and annotations.

## 1. Populate WoRMS Cache

The repository contains `initial_aphia_ids.txt`, with one AphiaID per line. Run the management command inside the service container:

```bash
cd worms-cache
docker compose -f docker/docker-compose.yml run --rm worms-cache \
  python manage.py ingest_worms --file initial_aphia_ids.txt --add-ranks
```

`--add-ranks` imports WoRMS rank definitions as well as taxa, parent classification, synonyms, and vernacular names. Edit or replace the input file to seed the taxa relevant to your collection.

Individual taxa can also be ingested through the protected API:

```bash
curl -X POST http://localhost:8001/api/taxa/ingest/ \
  -H "Authorization: Bearer mysecrettoken" \
  -H "Content-Type: application/json" \
  -d '{"aphia_id": 126436}'
```

For later maintenance, use `python manage.py refresh_worms`; see the imported WoRMS Cache README for its dry-run and cache-age options.

## 2. Create an Annotations API token

Write operations require Django token authentication:

```bash
cd ../annotations-api
docker compose -f docker/docker-compose.yml exec api \
  python manage.py create_user_with_token my-user 'replace-this-password'
```

Store the returned token securely and export it for the examples:

```bash
export API_BASE=http://localhost:8000
export API_TOKEN=replace-with-returned-token
```

## 3. Ingest imagery metadata

The image-set ingestion endpoint accepts an iFDO JSON payload:

```bash
curl -sS -X POST "$API_BASE/api/ingest/image-sets/" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  --data-binary @path/to/images.ifdo.json
```

Review the imported Annotations API examples for required iFDO fields and response details.

## 4. Ingest annotations

Upload an XLSX workbook after its referenced image set and images exist:

```bash
curl -sS -X POST "$API_BASE/api/ingest/annotation-sets/" \
  -H "Authorization: Bearer $API_TOKEN" \
  -F "file=@path/to/annotations.xlsx"
```

Labels containing AphiaIDs are resolved through the configured WoRMS Cache. A missing taxon can trigger cached-WoRMS ingestion when the two API tokens agree.

## Generate demonstration data

For interface testing without a real dataset:

```bash
docker compose -f docker/docker-compose.yml run --rm api \
  python manage.py seed_demo_data
```

This command is for development only and must not be run against production databases.

## Validate before registration

Use the interactive schema at <http://localhost:8000/api/docs/> and confirm:

* `/api/health/` returns successfully.
* The search endpoint returns imported records.
* Public GET operations do not require the write token.
* Taxonomic labels return the expected AphiaIDs and scientific names.
