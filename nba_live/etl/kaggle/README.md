# Kaggle ETL Scripts

This component contains all ETL scripts responsible for extracting data from the Kaggle CSV files and loading it into the project's data warehouse tables.

---

## Key Responsibilities

*   Loads game-level dimension data from a Kaggle CSV file into the `dim_game` table.
*   Loads player dimension data from a Kaggle CSV file into the `dim_player` table.
*   Loads team dimension data from a Kaggle CSV file into the `dim_team` table.
*   Loads team-level game statistics from a Kaggle CSV file into the `fact_team_game_stats` table.

## Structure

*   `load_kaggle_games.py` – Loads game dimension data.
*   `load_kaggle_players.py` – Loads player dimension data.
*   `load_kaggle_team_stats.py` – Loads team game statistics (fact data).
*   `load_kaggle_teams.py` – Loads team dimension data.

---

## Quick Start

To run any of the loaders, execute the script directly from the root of the project.

```bash
# Load all game dimension data
python nba_live/etl/kaggle/load_kaggle_games.py
```

## Roadmap

1.  Integrate these scripts into a master ETL workflow.
2.  Add more robust error handling and logging to each script.

*For project-wide planning, see the [full roadmap](../../../context/PLAN.md).*