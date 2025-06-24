# Database Component

This component is responsible for managing all database assets, including schema definitions and data manipulation scripts.

---

## Key Responsibilities

*   Defines the core database schema via DDL scripts.
*   Provides a centralized location for all database-related files.

## Structure

*   `ddl/` – Contains all Data Definition Language (DDL) scripts. The scripts are numbered to indicate their execution order.

---

## Component Status

| Feature                 | Description                               | State |
|-------------------------|-------------------------------------------|-------|
| Initial Schema          | The base schema is defined in `00_create_schema.sql`. | ✅ Complete |
| Migration Framework     | A formal migration system is not yet implemented. | ⏳ Not started |

## Roadmap

1.  Implement a formal database migration framework (e.g., using `yoyo-migrations`).
2.  Add scripts for seeding initial data.

*For project-wide planning, see the [full roadmap](../../context/PLAN.md).*