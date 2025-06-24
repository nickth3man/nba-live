"""
ETL loader for NBA player data from Kaggle datasets.

This module loads player dimension data from CSV files into the 
DuckDB star schema, maintaining full data lineage.
"""

import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import duckdb
import pandas as pd
import yaml

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


class PlayerDataValidator:
    """Validates player data before loading."""
    
    @staticmethod
    def validate_required_columns(df: pd.DataFrame) -> List[str]:
        """Check for required columns in RAW format."""
        required_raw = {
            'id', 'full_name', 'first_name', 'last_name'
        }
        missing = required_raw - set(df.columns)
        return list(missing)
    
    @staticmethod
    def validate_player_id(player_id: Any) -> bool:
        """Validate player ID format."""
        if pd.isna(player_id):
            return False
        return str(player_id).isdigit()


class PlayerETLMetrics:
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
            for error in self.errors[:5]:
                logger.warning(
                    f"    Row {error['row_number']}: "
                    f"{error['error_type']} - {error['error_message']}"
                )


def transform_player_data(df: pd.DataFrame) -> pd.DataFrame:
    """Transform raw Kaggle player data to match star schema."""
    players = df.copy()
    
    # Rename columns to match dim_player schema
    players = players.rename(columns={
        'id': 'player_id'
    })
    
    # Add placeholder columns for fields not in the source CSV
    players['birth_date'] = pd.NaT
    players['height_cm'] = pd.NA
    players['weight_kg'] = pd.NA
    players['debut_season_id'] = pd.NA

    final_columns = [
        'player_id', 'full_name', 'first_name', 'last_name',
        'birth_date', 'height_cm', 'weight_kg', 'debut_season_id'
    ]
    
    return players[final_columns]


def load_players(conn: duckdb.DuckDBPyConnection, 
               csv_path: str,
               batch_size: int = 1000) -> PlayerETLMetrics:
    """
    Load player data from Kaggle CSV into DuckDB.
    """
    metrics = PlayerETLMetrics()
    validator = PlayerDataValidator()
    
    try:
        logger.info(f"Reading CSV from {csv_path}")
        
        with conn.cursor() as cur:
            cur.execute("BEGIN TRANSACTION;")
            
            try:
                for i, chunk in enumerate(pd.read_csv(
                    csv_path, chunksize=batch_size, low_memory=False
                )):
                    metrics.total_rows += len(chunk)
                    
                    chunk.drop_duplicates(subset=['id'], inplace=True)
                    
                    missing_cols = validator.validate_required_columns(chunk)
                    if missing_cols:
                        raise ValueError(f"Missing required columns: {missing_cols}")

                    players_df = transform_player_data(chunk)
                    
                    players_df['source_id'] = SOURCE_ID_KAGGLE
                    players_df['load_timestamp'] = datetime.now()
                    
                    cur.execute("""
                        INSERT INTO nba_prod.dim_player (
                            player_id, full_name, first_name, last_name, birth_date, 
                            height_cm, weight_kg, debut_season_id, source_id, load_timestamp
                        )
                        SELECT
                            player_id, full_name, first_name, last_name, birth_date,
                            height_cm, weight_kg, debut_season_id, source_id, load_timestamp
                        FROM players_df
                        ON CONFLICT (player_id) DO UPDATE SET
                            full_name = excluded.full_name,
                            first_name = excluded.first_name,
                            last_name = excluded.last_name,
                            birth_date = excluded.birth_date,
                            height_cm = excluded.height_cm,
                            weight_kg = excluded.weight_kg,
                            debut_season_id = excluded.debut_season_id,
                            source_id = excluded.source_id,
                            load_timestamp = excluded.load_timestamp;
                    """)
                    
                    metrics.loaded_rows += len(players_df)
                
                cur.execute("COMMIT;")
                logger.info("Transaction committed successfully.")
                
            except Exception as e:
                cur.execute("ROLLBACK;")
                logger.error(f"Transaction failed, rolling back. Error: {e}")
                raise
                
    except FileNotFoundError:
        logger.error(f"File not found: {csv_path}")
        metrics.add_error(0, "File Error", f"CSV file not found at {csv_path}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        metrics.add_error(0, "General Error", str(e))
        
    metrics.log_summary()
    return metrics


def run_player_verification_queries(conn: duckdb.DuckDBPyConnection):
    """Run post-load verification queries."""
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM nba_prod.dim_player;")
        count = cur.fetchone()[0]
        logger.info(f"Verification: Found {count} players in dim_player.")
        
        cur.execute("SELECT * FROM nba_prod.dim_player ORDER BY RANDOM() LIMIT 5;")
        logger.info(f"Verification: Sample players:\n{cur.fetchdf()}")


def main():
    """Main execution block."""
    project_root = get_project_root()
    
    # Load configuration from YAML file
    config_path = project_root / 'nba_live' / 'etl' / 'etl_config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    db_path = project_root / config['database']['path']
    
    kaggle_config = config['data_sources']['kaggle_basketball']
    csv_path = project_root / kaggle_config['base_path'] / kaggle_config['players']

    logger.info(f"Project root: {project_root}")
    logger.info(f"Database path: {db_path}")
    logger.info(f"CSV path: {csv_path}")

    try:
        conn = duckdb.connect(str(db_path))
        logger.info("Successfully connected to DuckDB.")
        
        load_players(conn, str(csv_path))
        run_player_verification_queries(conn)
        
    except Exception as e:
        logger.error(f"An error occurred during the ETL process: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            logger.info("Database connection closed.")


if __name__ == "__main__":
    main()