"""
ETL loader for NBA team game stats from Kaggle datasets.

This module extracts team-level game statistics from the `game.csv` file,
transforms the data from a wide to a long format, and loads it into the
`fact_team_game_stats` table in the DuckDB star schema.
"""

import logging
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import duckdb
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Source identifier for data lineage
SOURCE_ID_KAGGLE = 1


def get_project_root() -> Path:
    """Find project root by looking for pyproject.toml"""
    current = Path.cwd()
    while current != current.parent:
        if (current / 'pyproject.toml').exists():
            return current
        current = current.parent
    return Path.cwd()


def load_config(root_path: Path) -> Dict[str, Any]:
    """Load YAML configuration."""
    config_path = root_path / 'nba_live' / 'etl' / 'etl_config.yaml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


class TeamStatsDataValidator:
    """Validates team stats data before loading."""

    @staticmethod
    def validate_required_columns(df: pd.DataFrame) -> List[str]:
        """Check for required columns in the raw CSV."""
        required_raw = {
            'game_id', 'season_id', 'team_id_home', 'team_id_away',
            'pts_home', 'pts_away'
        }
        missing = required_raw - set(df.columns)
        return list(missing)


class ETLETLMetrics:
    """Tracks ETL process metrics."""

    def __init__(self):
        self.total_rows = 0
        self.loaded_rows = 0
        self.skipped_rows = 0
        self.errors: List[Dict[str, Any]] = []

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_rows == 0:
            return 0.0
        return self.loaded_rows / self.total_rows

    def add_error(self, row_num: int, error_type: str,
                  error_msg: str, row_data: Optional[Dict[str, Any]] = None):
        """Record an error."""
        self.errors.append({
            'row_number': row_num,
            'error_type': error_type,
            'error_message': error_msg,
            'row_data': row_data,
            'timestamp': datetime.now()
        })

    def log_summary(self):
        """Log ETL metrics summary."""
        logger.info("ETL Process Summary:")
        logger.info(f"  Total rows processed (from source): {self.total_rows}")
        logger.info(f"  Rows loaded into target: {self.loaded_rows}")
        logger.info(f"  Rows skipped: {self.skipped_rows}")
        logger.info(f"  Success rate: {self.success_rate:.2%}")

        if self.errors:
            logger.warning(f"  Errors encountered: {len(self.errors)}")
            for error in self.errors[:5]:
                logger.warning(
                    f"    Row {error['row_number']}: "
                    f"{error['error_type']} - {error['error_message']}"
                )


def transform_team_stats_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms raw game data to a long format for team stats.

    Unpivots the data, creating one row per team (home and away) per game.
    """
    df_copy = df.copy()

    # Define columns for home and away teams
    home_cols = {col: col.replace('_home', '') for col in df_copy.columns if col.endswith('_home')}
    away_cols = {col: col.replace('_away', '') for col in df_copy.columns if col.endswith('_away')}

    # Create home team DataFrame
    home_df = df_copy[['game_id', 'season_id'] + list(home_cols.keys())].rename(columns=home_cols)
    home_df['is_home'] = True

    # Create away team DataFrame
    away_df = df_copy[['game_id', 'season_id'] + list(away_cols.keys())].rename(columns=away_cols)
    away_df['is_home'] = False

    # Concatenate home and away data
    transformed_df = pd.concat([home_df, away_df], ignore_index=True)

    # Standardize column names to match fact_team_game_stats
    # Most are handled by renaming, but ensure all are correct
    final_cols = [
        'game_id', 'team_id', 'season_id', 'is_home', 'pts', 'fgm', 'fga',
        'fg_pct', 'fg3m', 'fg3a', 'fg3_pct', 'ftm', 'fta', 'ft_pct',
        'oreb', 'dreb', 'reb', 'ast', 'stl', 'blk', 'tov', 'pf', 'plus_minus'
    ]
    
    # Select and reorder columns, filling missing ones with None
    for col in final_cols:
        if col not in transformed_df.columns:
            transformed_df[col] = None
            
    return transformed_df[final_cols]


def load_team_stats(conn: duckdb.DuckDBPyConnection,
                    csv_path: str,
                    batch_size: int = 1000) -> ETLETLMetrics:
    """
    Load team game stats from Kaggle CSV into DuckDB.
    """
    metrics = ETLETLMetrics()
    validator = TeamStatsDataValidator()
    
    try:
        logger.info(f"Reading team stats from CSV: {csv_path}")
        
        with conn.cursor() as cur:
            cur.execute("BEGIN TRANSACTION;")
            
            try:
                for i, chunk in enumerate(pd.read_csv(
                    csv_path, chunksize=batch_size, low_memory=False
                )):
                    metrics.total_rows += len(chunk)
                    
                    chunk.drop_duplicates(subset=['game_id'], inplace=True)
                    
                    missing_cols = validator.validate_required_columns(chunk)
                    if missing_cols:
                        raise ValueError(f"Missing required columns: {missing_cols}")

                    stats_df = transform_team_stats_data(chunk)
                    
                    # Add lineage columns
                    stats_df['source_id'] = SOURCE_ID_KAGGLE
                    stats_df['load_timestamp'] = datetime.now()
                    
                    # Use a temporary table for staging
                    cur.execute("CREATE TEMP TABLE temp_team_stats AS SELECT * FROM stats_df")
                    
                    # Insert into the final table, handling potential duplicates
                    cur.execute("""
                        INSERT INTO nba_prod.fact_team_game_stats (
                            game_id, team_id, season_id, is_home, pts, fgm, fga,
                            fg_pct, fg3m, fg3a, fg3_pct, ftm, fta, ft_pct,
                            oreb, dreb, reb, ast, stl, blk, tov, pf, plus_minus,
                            source_id, load_timestamp
                        )
                        SELECT * FROM temp_team_stats
                        ON CONFLICT (game_id, team_id) DO NOTHING;
                    """)
                    
                    loaded_count = cur.fetchone()[0]
                    metrics.loaded_rows += loaded_count
                    metrics.skipped_rows += len(stats_df) - loaded_count
                    
                    cur.execute("DROP TABLE temp_team_stats;")

                cur.execute("COMMIT;")
                logger.info("Transaction committed successfully.")
                
            except Exception as e:
                cur.execute("ROLLBACK;")
                logger.error(f"Transaction rolled back due to error: {e}")
                raise

    except FileNotFoundError:
        logger.error(f"CSV file not found at {csv_path}")
        metrics.add_error(0, "File Not Found", f"Path: {csv_path}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        metrics.add_error(0, "General Error", str(e))
        
    metrics.log_summary()
    return metrics


def run_team_stats_verification_queries(conn: duckdb.DuckDBPyConnection):
    """Runs verification queries against the fact_team_game_stats table."""
    logger.info("Running verification queries for fact_team_game_stats...")
    
    queries = {
        "Total records loaded": "SELECT COUNT(*) FROM nba_prod.fact_team_game_stats;",
        "Total home games": "SELECT COUNT(*) FROM nba_prod.fact_team_game_stats WHERE is_home = TRUE;",
        "Total away games": "SELECT COUNT(*) FROM nba_prod.fact_team_game_stats WHERE is_home = FALSE;",
        "Total points for a sample team (Lakers, ID 1610612747)": """
            SELECT SUM(pts) 
            FROM nba_prod.fact_team_game_stats 
            WHERE team_id = 1610612747;
        """,
        "Max points in a single game": "SELECT MAX(pts) FROM nba_prod.fact_team_game_stats;"
    }
    
    for name, query in queries.items():
        try:
            result = conn.execute(query).fetchone()[0]
            logger.info(f"  - {name}: {result}")
        except Exception as e:
            logger.error(f"  - Query failed for '{name}': {e}")


def main():
    """Main execution block."""
    root_path = get_project_root()
    config = load_config(root_path)
    
    db_path = root_path / config['database']['path']
    csv_base_path = root_path / config['data_sources']['kaggle_basketball']['base_path']
    game_csv = csv_base_path / config['data_sources']['kaggle_basketball']['games']
    
    logger.info(f"Database path: {db_path}")
    logger.info(f"Game CSV path: {game_csv}")
    
    try:
        conn = duckdb.connect(database=str(db_path), read_only=False)
        
        metrics = load_team_stats(conn, str(game_csv))
        
        if metrics.success_rate >= 0.95:
            logger.info("ETL process completed successfully with high confidence.")
            run_team_stats_verification_queries(conn)
        else:
            logger.warning("ETL process completed with low success rate. Please review errors.")
            
    except Exception as e:
        logger.critical(f"ETL process failed: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed.")


if __name__ == "__main__":
    main()