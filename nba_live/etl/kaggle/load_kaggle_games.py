"""
ETL loader for NBA game data from Kaggle datasets.

This module loads game dimension data from CSV files into the 
DuckDB star schema, maintaining full data lineage.
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
    # Fallback to CWD if not found
    return Path.cwd()


def load_config(root_path: Path) -> Dict[str, Any]:
    """Load YAML configuration."""
    config_path = root_path / 'nba_live' / 'etl' / 'etl_config.yaml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


class GameDataValidator:
    """Validates game data before loading."""
    
    @staticmethod
    def validate_required_columns(df: pd.DataFrame) -> List[str]:
        """Check for required columns in RAW format."""
        # These are the actual column names in the CSV
        required_raw = {
            'game_id', 'game_date', 'season_id',
            'team_id_home', 'team_id_away'
        }
        missing = required_raw - set(df.columns)
        return list(missing)
    
    @staticmethod
    def validate_game_id(game_id: str) -> bool:
        """Validate game ID format."""
        if pd.isna(game_id):
            return False
        # NBA game IDs are typically 10 characters
        return len(str(game_id)) >= 8
    
    @staticmethod
    def validate_date(date_str: str) -> bool:
        """Validate date format."""
        try:
            pd.to_datetime(date_str)
            return True
        except:
            return False


class GameETLMetrics:
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
        logger.info(f"  Total rows: {self.total_rows}")
        logger.info(f"  Loaded: {self.loaded_rows}")
        logger.info(f"  Skipped: {self.skipped_rows}")
        logger.info(f"  Success rate: {self.success_rate:.2%}")
        
        if self.errors:
            logger.warning(f"  Errors encountered: {len(self.errors)}")
            # Log first 5 errors as examples
            for error in self.errors[:5]:
                logger.warning(
                    f"    Row {error['row_number']}: "
                    f"{error['error_type']} - {error['error_message']}"
                )


def transform_game_data(df: pd.DataFrame) -> pd.DataFrame:
    """Transform raw Kaggle data to match star schema."""
    games = df.copy()
    
    # Add game_type (not in raw data)
    if 'game_type' not in games.columns:
        games['game_type'] = 'Regular'  # Default
    
    # Rename to match dim_game schema
    games = games.rename(columns={
        'team_id_home': 'home_team_id',
        'team_id_away': 'away_team_id'
    })
    
    # Convert date
    games['game_date'] = pd.to_datetime(games['game_date'], errors='coerce')
    
    final_columns = [
        'game_id', 'game_date', 'season_id',
        'game_type', 'home_team_id', 'away_team_id'
    ]
    
    return games[final_columns]


def load_games(conn: duckdb.DuckDBPyConnection, 
               csv_path: str,
               batch_size: int = 1000) -> GameETLMetrics:
    """
    Load game data from Kaggle CSV into DuckDB.
    
    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
        Active DuckDB connection
    csv_path : str
        Path to the CSV file
    batch_size : int
        Number of rows to process per transaction
        
    Returns
    -------
    GameETLMetrics
        Metrics about the ETL process
    """
    metrics = GameETLMetrics()
    validator = GameDataValidator()
    
    try:
        logger.info(f"Reading CSV from {csv_path}")
        
        # Use context manager for transaction
        with conn.cursor() as cur:
            cur.execute("BEGIN TRANSACTION;")
            
            try:
                for i, chunk in enumerate(pd.read_csv(
                    csv_path, chunksize=batch_size, low_memory=False
                )):
                    metrics.total_rows += len(chunk)
                    
                    # Remove duplicates before processing
                    chunk.drop_duplicates(subset=['game_id'], inplace=True)
                    
                    # Validate raw columns before transform
                    missing_cols = validator.validate_required_columns(chunk)
                    if missing_cols:
                        raise ValueError(f"Missing required columns: {missing_cols}")

                    # Transform data
                    games_df = transform_game_data(chunk)
                    
                    # Add lineage columns
                    games_df['source_id'] = SOURCE_ID_KAGGLE
                    games_df['load_timestamp'] = datetime.now()
                    
                    # Insert into DuckDB
                    cur.execute("""
                        INSERT INTO nba_prod.dim_game (
                            game_id,
                            game_date,
                            season_id,
                            game_type,
                            home_team_id,
                            away_team_id,
                            source_id,
                            load_timestamp
                        )
                        SELECT
                            game_id,
                            game_date,
                            season_id,
                            game_type,
                            home_team_id,
                            away_team_id,
                            source_id,
                            load_timestamp
                        FROM games_df
                        ON CONFLICT (game_id) DO UPDATE SET
                            game_date = excluded.game_date,
                            season_id = excluded.season_id,
                            game_type = excluded.game_type,
                            home_team_id = excluded.home_team_id,
                            away_team_id = excluded.away_team_id,
                            source_id = excluded.source_id,
                            load_timestamp = excluded.load_timestamp;
                    """)
                    
                    metrics.loaded_rows += len(games_df)
                
                cur.execute("COMMIT;")
                logger.info("Transaction committed.")
                
            except Exception as e:
                cur.execute("ROLLBACK;")
                logger.error(f"Transaction rolled back due to error: {e}")
                raise

    except FileNotFoundError:
        logger.error(f"File not found: {csv_path}")
        metrics.add_error(0, "File Not Found", f"CSV file not found at {csv_path}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        metrics.add_error(0, "General Error", str(e))
        
    return metrics


def run_verification_queries(conn: duckdb.DuckDBPyConnection):
    """Run post-load verification queries."""
    logger.info("Running verification queries...")
    total_games = conn.execute("SELECT COUNT(*) FROM nba_prod.dim_game;").fetchone()[0]
    logger.info(f"Total games in dim_game: {total_games}")
    
    latest_game = conn.execute("SELECT MAX(game_date) FROM nba_prod.dim_game;").fetchone()[0]
    logger.info(f"Latest game date: {latest_game}")


def main():
    """Main execution block."""
    project_root = get_project_root()
    config = load_config(project_root)
    
    db_path = project_root / config['database']['path']
    
    kaggle_base_path = config['data_sources']['kaggle_basketball']['base_path']
    games_file = config['data_sources']['kaggle_basketball']['games']
    csv_path = project_root / kaggle_base_path / games_file

    logger.info(f"Project root: {project_root}")
    logger.info(f"DB path: {db_path}")
    logger.info(f"CSV path: {csv_path}")

    try:
        conn = duckdb.connect(str(db_path))
        logger.info("Successfully connected to DuckDB.")
        
        metrics = load_games(conn, str(csv_path))
        metrics.log_summary()
        
        if metrics.loaded_rows > 0:
            run_verification_queries(conn)
            
    except Exception as e:
        logger.error(f"ETL process failed: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            logger.info("DuckDB connection closed.")


if __name__ == "__main__":
    main()