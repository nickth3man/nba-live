# NBA-Live

NBA-Live is an open-source, local analytics warehouse that archives every NBA
season from 1946-present and exposes clean, auditable data for research,
betting models, and fan exploration.

## Current Status

| Phase | Description | State |
|-------|-------------|-------|
| 0 | Repository bootstrap, CI, Poetry | ✅ Complete |
| 1 | Research & source assessment (35+ repos) | ✅ Complete |
| 2 | Database design – DuckDB star schema, audit layer | 🚧 In progress |
| 3 | Modern-era ETL pipeline | ⏳ Not started |

Latest progress (2025-06-23):
* Replaced Postgres plan with DuckDB for local columnar analytics.
* Drafted full star-schema DDL (`nba_live/db/ddl/00_create_schema.sql`).
* Added Kaggle player loader stub with lineage logging.
* Updated docs/architecture and dependencies.

## Quick Start

```bash
# Install dependencies
poetry install

# Create DuckDB file and load sample Kaggle players
poetry run python -m nba_live.etl.kaggle.load_kaggle_players \
  --csv data/sample/players.csv \
  --db nba_live.duckdb
```

## Roadmap (Condensed)
1. Complete remaining dimension & fact tables.
2. Build ETL loaders for games, boxscores, shots, play-by-play.
3. Implement data-quality scoring & audit dashboards.
4. Add LangChain-powered FastAPI for natural-language queries.

See `context/PLAN.md` for the full roadmap.

