# Test Suite

This component contains the complete test suite for the `nba_live` project. It uses `pytest` to ensure code quality, data integrity, and the correctness of all application logic.

---

## Key Responsibilities

*   Houses all `pytest` modules for testing application components.
*   Validates the correctness of ETL processes, data transformations, and analytical outputs.
*   Enforces a high standard of code quality with a target of ≥90% test coverage.

## Structure

*This directory is currently awaiting the implementation of test modules.*

---

## Component Status

| Feature                 | Description                               | State |
|-------------------------|-------------------------------------------|-------|
| Test Framework Setup    | `pytest` is the chosen framework.         | ✅ Complete |
| Test Implementation     | No tests have been written yet.           | ⏳ Not started |

## Quick Start

```bash
# Run the full test suite
pytest nba_live/tests/
```

## Roadmap

1.  Develop test cases for the Kaggle ETL scripts.
2.  Implement data validation tests for the database schema.
3.  Create tests for the player deduplication logic.

*For project-wide planning, see the [full roadmap](../../context/PLAN.md).*