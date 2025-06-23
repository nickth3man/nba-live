"""
ETL loader for NBA game data from Kaggle datasets.

This module loads game dimension data from CSV files into the 
DuckDB star schema, maintaining full data lineage.
"""

import logging
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


class GameDataValidator:
    """Validates game data before loading."""
    
    @staticmethod
    def validate_required_columns(df: pd.DataFrame) -> List[str]:
        """Check for required columns."""
        required = {
            'GAME_ID', 'GAME_DATE_EST', 'SEASON',
            'HOME_TEAM_ID', 'VISITOR_TEAM_ID'
        }
        missing = required - set(df.columns)
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
    """
    Transform raw Kaggle data to match star schema.
    
    Handles various Kaggle dataset formats and normalizes
    to our standard schema.
    """
    # Create a copy to avoid modifying original
    games = df.copy()
    
    # Standardize column names (handle multiple formats)
    column_mapping = {
        # wyattowalsh/basketball format
        'GAME_DATE_EST': 'game_date',
        'GAME_ID': 'game_id',
        'HOME_TEAM_ID': 'home_team_id',
        'VISITOR_TEAM_ID': 'away_team_id',
        'SEASON': 'season_id',
        # Alternative formats
        'gamedate': 'game_date',
        'gameid': 'game_id',
        'hometeamid': 'home_team_id',
        'awayteamid': 'away_team_id',
        'visitorteamid': 'away_team_id',
        'season_year': 'season_id'
    }
    
    # Apply mapping
    games.rename(columns=column_mapping, inplace=True)
    
    # Ensure game_date is datetime
    if 'game_date' in games.columns:
        games['game_date'] = pd.to_datetime(
            games['game_date'], 
            errors='coerce'
        )
    
    # Extract game_type if available, otherwise default
    if 'playoffs' in games.columns:
        games['game_type'] = games['playoffs'].map({
            0: 'Regular',
            1: 'Playoff'
        })
    elif 'game_type' not in games.columns:
        # Default to Regular if not specified
        games['game_type'] = 'Regular'
    
    # Select only columns we need
    required_columns = [
        'game_id', 'game_date', 'season_id', 
        'game_type', 'home_team_id', 'away_team_id'
    ]
    
    # Add missing columns with None
    for col in required_columns:
        if col not in games.columns:
            games[col] = None
    
    return games[required_columns]


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
        # Read CSV
        logger.info(f"Reading CSV from {csv_path}")
        df = pd.read_csv(csv_path, low_memory=False)
        metrics.total_rows = len(df)
        logger.info(f"Found {metrics.total_rows} rows")
        
        # Validate required columns exist
        missing_cols = validator.validate_required_columns(df)
        if missing_cols:
            error_msg = f"Missing required columns: {missing_cols}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Transform data
        logger.info("Transforming data to match schema")
        games = transform_game_data(df)
        
        # Process in batches for better performance
        for batch_start in range(0, len(games), batch_size):
            batch_end = min(batch_start + batch_size, len(games))
            batch = games.iloc[batch_start:batch_end].copy()
            
            # Validate each row in batch
            valid_rows = []
            for i, (_, row) in enumerate(batch.iterrows()):
                row_num = batch_start + i + 1
                
                # Validate game_id
                if not validator.validate_game_id(row['game_id']):
                    metrics.add_error(
                        row_num, 'invalid_game_id',
                        f"Invalid game_id: {row['game_id']}"
                    )
                    metrics.skipped_rows += 1
                    continue
                
                # Validate date
                if pd.isna(row['game_date']):
                    metrics.add_error(
                        row_num, 'invalid_date',
                        "Missing game_date"
                    )
                    metrics.skipped_rows += 1
                    continue
                
                valid_rows.append(row)
            
            # Load valid rows
            if valid_rows:
                valid_df = pd.DataFrame(valid_rows)
                
                try:
                    conn.execute("BEGIN TRANSACTION")
                    
                    # Register dataframe
                    conn.register("games_batch", valid_df)
                    
                    # Insert games (UPDATE if exists)
                    conn.execute("""
                        INSERT INTO dim_game 
                        SELECT * FROM games_batch
                        ON CONFLICT (game_id) 
                        DO UPDATE SET
                            game_date = EXCLUDED.game_date,
                            season_id = EXCLUDED.season_id,
                            game_type = EXCLUDED.game_type,
                            home_team_id = EXCLUDED.home_team_id,
                            away_team_id = EXCLUDED.away_team_id
                    """)
                    
                    # Record lineage
                    conn.execute("""
                        INSERT INTO bridge_duckdb_sources 
                        (fact_table, record_pk, source_id)
                        SELECT 
                            'dim_game',
                            CAST(game_id AS VARCHAR),
                            ?
                        FROM games_batch
                        ON CONFLICT (fact_table, record_pk) 
                        DO UPDATE SET
                            updated_at = CURRENT_TIMESTAMP
                    """, [SOURCE_ID_KAGGLE])
                    
                    conn.execute("COMMIT")
                    
                    metrics.loaded_rows += len(valid_rows)
                    logger.debug(
                        f"Loaded batch {batch_start}-{batch_end}"
                    )
                    
                except Exception as e:
                    conn.execute("ROLLBACK")
                    logger.error(
                        f"Failed to load batch {batch_start}-{batch_end}: {e}"
                    )
                    # Record batch error
                    metrics.add_error(
                        batch_start, 'batch_load_error',
                        str(e)
                    )
                
                finally:
                    # Cleanup
                    conn.unregister("games_batch")
        
        # Check success rate
        if metrics.success_rate < 0.95:
            logger.warning(
                f"Low success rate: {metrics.success_rate:.2%}"
            )
        
    except Exception as e:
        logger.error(f"Fatal error in ETL process: {e}")
        raise
    
    finally:
        # Always log summary
        metrics.log_summary()
    
    return metrics


def main():
    """Example usage."""
    # Connect to DuckDB
    db_path = 'nba_live.duckdb'
    logger.info(f"Connecting to database: {db_path}")
    conn = duckdb.connect(db_path)
    
    # Define data path
    # Default dataset path inside the project
    csv_file = (
        Path(__file__).parent.parent.parent / 'data' / 'kaggle' /
        'wyattowalsh_basketball' / 'csv' / 'game.csv'
    )
    
    if not csv_file.exists():
        logger.error(f"Data file not found: {csv_file}")
        logger.error("Please download the 'wyattowalsh/basketball' dataset from Kaggle and place 'nba_games.csv' in the 'data/kaggle' directory.")
        return

    # Load games
    logger.info("Starting ETL process for games...")
    metrics = load_games(conn, str(csv_file))
    
    # Check results
    try:
        result = conn.execute(
            "SELECT COUNT(*) as game_count FROM dim_game"
        ).fetchone()
        if result:
            logger.info(f"Total games in database: {result[0]}")
    except Exception as e:
        logger.error(f"Failed to query database for results: {e}")
    
    conn.close()
    logger.info("Database connection closed.")


if __name__ == "__main__":
    main()