# ETL

This directory contains all Extract, Transform, and Load (ETL) scripts and configurations for the project.

## Sub-directories

*   [`deduplication/`](deduplication/) - Contains scripts for identifying and merging duplicate records, such as the `player_matcher.py` script.
*   [`kaggle/`](kaggle/) - Contains ETL scripts specifically for loading data from Kaggle datasets.

## Files

*   [`README.md`](README.md) - A high-level overview of the ETL processes and architecture.
*   [`etl_config.yaml`](etl_config.yaml) - Central configuration for ETL scripts, defining database paths and data source locations.