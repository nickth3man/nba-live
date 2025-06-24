# Data Definition Language (DDL)

This component contains all Data Definition Language (DDL) scripts. These scripts are responsible for defining and managing the structure of the database, including schemas, tables, and constraints.

---

## Key Responsibilities

*   Initializes the database by creating the `nba_prod` schema.
*   Defines the complete star schema, including all dimension and fact tables.

## Structure

*   `00_create_schema.sql` – The foundational script that sets up the entire database schema. The numeric prefix indicates the execution order.

---

## Component Status

| Feature                 | Description                               | State |
|-------------------------|-------------------------------------------|-------|
| Star Schema Definition  | All core tables are defined.              | ✅ Complete |

## Roadmap

1.  Refactor DDL into a formal migration system (e.g., using `yoyo-migrations`).
2.  Add DDL for new data sources or analytical features as needed.

*For project-wide planning, see the [full roadmap](../../../context/PLAN.md).*