# Player Deduplication

This component is responsible for identifying and merging duplicate player records from different data sources.

---

## Key Responsibilities

*   Provides a utility to match player names using fuzzy matching algorithms.
*   Uses contextual comparisons to improve matching accuracy.

## Structure

*   [`player_matcher.py`](player_matcher.py) – The core script for identifying and merging duplicate player records.

---

## Component Status

| Feature                 | Description                               | State |
|-------------------------|-------------------------------------------|-------|
| Fuzzy Name Matching     | Core logic for matching player names.     | 🚧 In progress |
| Contextual Comparison   | Logic to compare player context (e.g., team, season). | ⏳ Not started |

## Roadmap

1.  Integrate the `player_matcher.py` script into the main ETL workflow.
2.  Add unit tests to validate the matching logic.

*For project-wide planning, see the [full roadmap](../../../context/PLAN.md).*