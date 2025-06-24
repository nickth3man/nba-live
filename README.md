# NBA Live

**A complete, local-first NBA database and data processing pipeline.**

This project's primary goal is to build a comprehensive, historically accurate, and locally accessible NBA database using modern data stack principles. It is designed to serve as a foundational dataset for analytics, machine learning, and application development.

The project has shifted from its initial PostgreSQL and `sqlc` proof-of-concept to a more flexible and embedded solution using **DuckDB**.

---

## Current Status

| Phase                                      | Description                                    | State         |
|--------------------------------------------|------------------------------------------------|---------------|
| **Phase 1: Research & Planning**           | Define project goals and architecture.         | ✅ Complete   |
| **Phase 2: Database Design**               | Schema defined, implementing tables.           | 🚧 In progress |
| **Phase 3: Modern-era ETL Pipeline**       | Build loaders for modern NBA data (2000-present). | 🚧 In progress |
| **Phase 4: Historical-era ETL Pipeline**   | Build loaders for historical data (pre-2000).  | ⏳ Not started |
| **Phase 5: AI Query Agent**                | Implement a natural language query interface.  | ⏳ Not started |

**Latest progress:**
*   The full star-schema DDL has been drafted in [`nba_live/db/ddl/00_create_schema.sql`](nba_live/db/ddl/00_create_schema.sql).
*   Initial ETL loaders for Kaggle data have been built.

---

## Quick Start

To get started, clone the repository and run one of the existing ETL scripts:

```bash
# Load game data from the Kaggle source
python nba_live/etl/kaggle/load_kaggle_games.py
```

## Roadmap

The immediate focus is on completing the ETL pipeline for the modern era.

1.  **Finalize ETL Loaders:** Complete and test all data loaders for the modern era.
2.  **Implement Database Migrations:** Introduce a formal migration framework (e.g., `yoyo-migrations`).
3.  **Develop Test Suite:** Build out the `pytest` suite to ensure data quality and code correctness.

For more detailed planning, see the [full project plan](context/PLAN.md).
