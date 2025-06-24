# Kaggle ETL Scripts

This directory contains all ETL scripts for loading data sourced from Kaggle.

## Files

*   [`load_kaggle_games.py`](load_kaggle_games.py) - Loads game dimension data into the `dim_game` table.
*   [`load_kaggle_players.py`](load_kaggle_players.py) - Loads player dimension data into the `dim_player` table.
*   [`load_kaggle_team_stats.py`](load_kaggle_team_stats.py) - Loads team-level game statistics into the `fact_team_game_stats` table.
*   [`load_kaggle_teams.py`](load_kaggle_teams.py) - Loads team dimension data into the `dim_team` table.