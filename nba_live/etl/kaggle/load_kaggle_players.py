from __future__ import annotations

"""Kaggle Player Loader

Usage:
    python -m nba_live.etl.kaggle.load_kaggle_players \
        --csv data/players.csv \
        --db nba_live.duckdb

This script loads player metadata from a Kaggle CSV into the `dim_player`
table.

Each load is recorded in `bridge_duckdb_sources` for lineage tracking.
"""

import argparse
import pathlib
import duckdb
import pandas as pd

SOURCE_ID_KAGGLE = 4  # see precedence list in documentation


def load_players(csv_path: pathlib.Path, db_path: pathlib.Path) -> None:
    """Load player data into DuckDB dim_player."""
    conn = duckdb.connect(db_path.as_posix())

    # Read CSV with pandas for simple cleaning
    df = pd.read_csv(csv_path)

    # Minimal column mapping – adjust once real Kaggle schema inspected
    players = df.rename(
        columns={
            "id": "player_id",
            "full_name": "full_name",
            "first_name": "first_name",
            "last_name": "last_name",
            "height_cm": "height_cm",
            "weight_kg": "weight_kg",
            "birth_date": "birth_date",
        }
    )[
        [
            "player_id",
            "full_name",
            "first_name",
            "last_name",
            "birth_date",
            "height_cm",
            "weight_kg",
        ]
    ]

    # Use DuckDB's efficient parquet insert path (vectorized) via pandas
    conn.execute("BEGIN TRANSACTION")
    conn.register("players_df", players)

    # Insert or upsert records
    conn.execute(
        """
        INSERT OR REPLACE INTO dim_player
        SELECT *
        FROM players_df
        """,
    )

    # Log lineage
    conn.execute(
        """
        INSERT INTO bridge_duckdb_sources (fact_table, record_pk, source_id)
        SELECT
            'dim_player',
            CAST(player_id AS VARCHAR),
            ?
        FROM players_df
        """,
        [SOURCE_ID_KAGGLE],
    )

    conn.execute("COMMIT")
    print(f"Loaded {len(players)} players into {db_path}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Load Kaggle players into DuckDB",
    )
    parser.add_argument(
        "--csv",
        type=pathlib.Path,
        required=True,
        help="Path to Kaggle players CSV",
    )
    parser.add_argument(
        "--db",
        type=pathlib.Path,
        default=pathlib.Path("nba_live.duckdb"),
        help="Output DuckDB file (default: nba_live.duckdb)",
    )
    args = parser.parse_args()

    load_players(args.csv, args.db) 