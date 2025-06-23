# ETL Package

This directory will contain data extraction, transformation, and load modules segmented by era:

* `extractors/` – source-specific downloaders (NBA API, Basketball-Reference, Kaggle).
* `transformers/` – canonical schema mappers and validators.
* `loaders/` – database loaders with upsert/merge logic.
* `common/` – shared utilities (rate limiting, logging, config). 