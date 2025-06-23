-- DuckDB Star Schema DDL (v0.1)
-- Dimensions
CREATE TABLE dim_season (
  season_id INTEGER PRIMARY KEY,
  year_start INTEGER NOT NULL,
  year_end INTEGER NOT NULL,
  era_label TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_team (
  team_id INTEGER PRIMARY KEY,
  abbreviation TEXT NOT NULL,
  team_name TEXT,
  city TEXT,
  first_year INTEGER,
  last_year INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_player (
  player_id INTEGER PRIMARY KEY,
  full_name TEXT NOT NULL,
  first_name TEXT,
  last_name TEXT,
  birth_date DATE,
  height_cm REAL,
  weight_kg REAL,
  debut_season_id INTEGER REFERENCES dim_season(season_id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_game (
  game_id INTEGER PRIMARY KEY,
  season_id INTEGER REFERENCES dim_season(season_id),
  game_date DATE NOT NULL,
  home_team_id INTEGER REFERENCES dim_team(team_id),
  away_team_id INTEGER REFERENCES dim_team(team_id),
  arena_id INTEGER,
  attendance INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Facts
CREATE TABLE fact_player_game_stats (
  player_id INTEGER REFERENCES dim_player(player_id),
  game_id INTEGER REFERENCES dim_game(game_id),
  team_id INTEGER REFERENCES dim_team(team_id),
  season_id INTEGER REFERENCES dim_season(season_id),
  minutes_played REAL,
  points INTEGER,
  rebounds INTEGER,
  assists INTEGER,
  steals INTEGER,
  blocks INTEGER,
  turnovers INTEGER,
  fouls INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(player_id, game_id)
);

CREATE TABLE fact_team_game_stats (
  team_id INTEGER REFERENCES dim_team(team_id),
  game_id INTEGER REFERENCES dim_game(game_id),
  season_id INTEGER REFERENCES dim_season(season_id),
  points INTEGER,
  rebounds INTEGER,
  assists INTEGER,
  steals INTEGER,
  blocks INTEGER,
  turnovers INTEGER,
  fouls INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(team_id, game_id)
);

-- Bridge for lineage/audit
CREATE TABLE bridge_duckdb_sources (
  fact_table TEXT NOT NULL,
  record_pk TEXT NOT NULL,
  source_id INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(fact_table, record_pk)
);
-- Phase 2 DDL Extensions

CREATE TABLE dim_referee (
    referee_id INTEGER PRIMARY KEY,
    full_name VARCHAR NOT NULL,
    first_name VARCHAR,
    last_name VARCHAR,
    jersey_number VARCHAR
);

CREATE TABLE dim_coach (
    coach_id INTEGER PRIMARY KEY,
    full_name VARCHAR NOT NULL,
    first_name VARCHAR,
    last_name VARCHAR,
    birth_date DATE
);

CREATE TABLE fact_shot_chart (
    game_id VARCHAR NOT NULL,
    player_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    period INTEGER,
    minutes_remaining INTEGER,
    seconds_remaining INTEGER,
    shot_type VARCHAR,
    shot_distance INTEGER,
    shot_made BOOLEAN,
    shot_value INTEGER,
    x_coordinate DOUBLE,
    y_coordinate DOUBLE,
    -- Composite primary key
    PRIMARY KEY (game_id, player_id, period, 
                 minutes_remaining, seconds_remaining)
);

CREATE TABLE bridge_player_team (
    player_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    season_id INTEGER NOT NULL,
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN,
    jersey_number VARCHAR,
    position VARCHAR,
    PRIMARY KEY (player_id, team_id, season_id, start_date)
);

-- Pre-populated date dimension
CREATE TABLE dim_date AS
WITH date_series AS (
    SELECT generate_series(
        DATE '1946-01-01',
        DATE '2030-12-31',
        INTERVAL 1 DAY
    )::DATE as date_key
)
SELECT 
    date_key,
    EXTRACT(YEAR FROM date_key) as year,
    EXTRACT(MONTH FROM date_key) as month,
    EXTRACT(DAY FROM date_key) as day,
    DAYNAME(date_key) as day_name,
    CASE 
        WHEN EXTRACT(MONTH FROM date_key) IN (10,11,12,1,2,3,4,5,6)
        THEN CONCAT(
            EXTRACT(YEAR FROM date_key) - 
            CASE WHEN EXTRACT(MONTH FROM date_key) >= 10 
                 THEN 0 ELSE 1 END,
            '-',
            SUBSTR(CAST(EXTRACT(YEAR FROM date_key) - 
            CASE WHEN EXTRACT(MONTH FROM date_key) >= 10 
                 THEN 0 ELSE 1 END + 1 AS VARCHAR), 3, 2)
        )
    END as season_code
FROM date_series;