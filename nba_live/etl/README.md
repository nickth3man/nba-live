# ETL Package

This component is responsible for all data ingestion and processing workflows. It contains scripts to extract data from various sources (like Kaggle), transform it into the required schema, and load it into the DuckDB data warehouse.

---

## Key Responsibilities

*   Manages all ETL processes for datasets sourced from Kaggle.
*   Provides scripts for data cleaning and deduplication.
*   Uses a central configuration file (`etl_config.yaml`) to manage data sources and database connections.

## Structure

*   `deduplication/` – Scripts for data cleaning and entity matching.
*   `kaggle/` – Scripts for loading data from Kaggle CSVs.
*   `etl_config.yaml` – Central configuration for all ETL scripts.

---

## Component Status

| Feature                 | Description                               | State |
|-------------------------|-------------------------------------------|-------|
| Kaggle Data Loaders     | Scripts to load core game, team, and player data. | ✅ Complete |
| Player Deduplication    | Initial script for matching player records. | 🚧 In progress |
| Modular Refactor        | Planned refactor into a more modular structure. | ⏳ Not started |


## Roadmap

1.  Refactor the package into a more modular structure with `extractors/`, `transformers/`, and `loaders/`.
2.  Develop a more robust error handling and logging mechanism for all ETL scripts.

*For project-wide planning, see the [full roadmap](../../context/PLAN.md).*