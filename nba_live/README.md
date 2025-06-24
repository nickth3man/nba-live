# `nba_live` Application

This directory contains the complete source code for the `nba_live` application. It is organized into several key components, each responsible for a distinct aspect of the application's functionality.

---

## Key Responsibilities

*   Provides all core application logic, from data ingestion to AI-powered querying.
*   Manages the database schema and all data processing workflows.
*   Contains the complete test suite to ensure code quality and data integrity.

## Structure

*   `ai/` – Contains all AI-related components, such as the embedding generator and query agent.
*   `db/` – Manages all database assets, including DDL scripts for schema creation.
*   `etl/` – Contains all scripts for the Extract, Transform, and Load (ETL) processes.
*   `tests/` – Houses the complete `pytest` test suite for the application.

---

## Roadmap

1.  Implement the AI query agent for natural language database queries.
2.  Develop a comprehensive test suite with ≥90% coverage.
3.  Refactor the ETL process into a more modular and robust workflow.

*For project-wide planning, see the [full roadmap](../context/PLAN.md).*