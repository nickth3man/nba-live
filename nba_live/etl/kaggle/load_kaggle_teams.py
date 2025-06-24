"""
ETL loader for NBA team data from Kaggle datasets.

This module loads team dimension data from CSV files into the 
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


def load_etl_config(config_path: Path) -> Dict[str, Any]:
    """Load ETL configuration from a YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found at {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file: {e}")
        raise


class TeamDataValidator:
    """Validates team data before loading."""
    
    @staticmethod
    def validate_required_columns(df: pd.DataFrame) -> List[str]:
        """Check for required columns in RAW format."""
        required_raw = {
            'id', 'full_name', 'abbreviation', 'nickname', 'city', 'state', 'year_founded'
        }
        missing = required_raw - set(df.columns)
        return list(missing)
    
    @staticmethod
    def validate_team_id(team_id: Any) -> bool:
        """Validate team ID format."""
        if pd.isna(team_id):
            return False
        return str(team_id).isdigit()


class TeamETLMetrics:
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


def transform_team_data(df: pd.DataFrame) -> pd.DataFrame:
    """Transform raw Kaggle team data to match star schema."""
    teams = df.copy()
    
    # Rename columns to match dim_team schema
    teams = teams.rename(columns={
        'id': 'team_id',
        'full_name': 'team_name'
    })
    
    # Split 'full_name' to derive city and nickname as a fallback
    # In this dataset, 'city' and 'nickname' are already provided.
    # If they were not, this is how you might derive them:
    # teams['city'] = teams['team_name'].apply(lambda x: ' '.join(x.split(' ')[:-1]))
    # teams['nickname'] = teams['team_name'].apply(lambda x: x.split(' ')[-1])

    # Convert year_founded to integer, handling NaNs
    teams['year_founded'] = pd.to_numeric(teams['year_founded'], errors='coerce').astype('Int64')

    final_columns = [
        'team_id', 'team_name', 'abbreviation', 'nickname',
        'city', 'state', 'year_founded'
    ]
    
    return teams[final_columns]


def load_teams(conn: duckdb.DuckDBPyConnection, 
               csv_path: str,
               batch_size: int = 1000) -> TeamETLMetrics:
    """
    Load team data from Kaggle CSV into DuckDB.
    """
    metrics = TeamETLMetrics()
    validator = TeamDataValidator()
    
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

                    teams_df = transform_team_data(chunk)
                    
                    teams_df['source_id'] = SOURCE_ID_KAGGLE
                    teams_df['load_timestamp'] = datetime.now()
                    
                    cur.execute("""
                        INSERT INTO nba_prod.dim_team (
                            team_id, team_name, abbreviation, nickname, city, state, 
                            year_founded, source_id, load_timestamp
                        )
                        SELECT
                            team_id, team_name, abbreviation, nickname, city, state,
                            year_founded, source_id, load_timestamp
                        FROM teams_df
                        ON CONFLICT (team_id) DO UPDATE SET
                            team_name = excluded.team_name,
                            abbreviation = excluded.abbreviation,
                            nickname = excluded.nickname,
                            city = excluded.city,
                            state = excluded.state,
                            year_founded = excluded.year_founded,
                            source_id = excluded.source_id,
                            load_timestamp = excluded.load_timestamp;
                    """)
                    
                    metrics.loaded_rows += len(teams_df)
                
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


def run_team_verification_queries(conn: duckdb.DuckDBPyConnection):
    """Run post-load verification queries."""
    logger.info("Running verification queries...")
    queries = {
        "Count total records": "SELECT COUNT(*) FROM nba_prod.dim_team;",
        "Count records from Kaggle": "SELECT COUNT(*) FROM nba_prod.dim_team WHERE source_id = 1;",
        "Show sample of 5 teams": "SELECT * FROM nba_prod.dim_team LIMIT 5;"
    }
    
    with conn.cursor() as cur:
        for name, query in queries.items():
            logger.info(f"Executing: {name}")
            result = cur.execute(query).fetchall()
            logger.info(f"Result:\n{pd.DataFrame(result, columns=[desc[0] for desc in cur.description])}")


def main():
    """Main execution block."""
    project_root = get_project_root()
    
    # Load configuration
    config_path = project_root / 'nba_live' / 'etl' / 'etl_config.yaml'
    config = load_etl_config(config_path)
    
    # Get paths from config
    db_path = project_root / config['database']['path']
    kaggle_base_path = project_root / config['data_sources']['kaggle_basketball']['base_path']
    team_csv_path = kaggle_base_path / config['data_sources']['kaggle_basketball']['teams']

    logger.info(f"Database path: {db_path}")
    logger.info(f"Team CSV path: {team_csv_path}")

    try:
        conn = duckdb.connect(database=str(db_path), read_only=False)
        
        # Create schema if it doesn't exist
        conn.execute("CREATE SCHEMA IF NOT EXISTS nba_prod;")
        
        # Create table if it doesn't exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS nba_prod.dim_team (
                team_id INTEGER PRIMARY KEY,
                team_name VARCHAR NOT NULL,
                abbreviation VARCHAR(5),
                nickname VARCHAR,
                city VARCHAR,
                state VARCHAR,
                year_founded INTEGER,
                source_id INTEGER,
                load_timestamp TIMESTAMP
            );
        """)
        
        metrics = load_teams(conn, str(team_csv_path))
        
        if metrics.success_rate >= 0.95:
            logger.info("ETL load successful, running verification.")
            run_team_verification_queries(conn)
        else:
            logger.error(f"ETL process failed with success rate {metrics.success_rate:.2%}. Aborting.")
            exit(1)
            
    except Exception as e:
        logger.critical(f"A critical error occurred in the main execution block: {e}")
        exit(1)
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    main()