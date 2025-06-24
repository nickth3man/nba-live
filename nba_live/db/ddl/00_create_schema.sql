-- DuckDB Star Schema DDL (v0.1)
DROP SCHEMA IF EXISTS nba_prod CASCADE;
CREATE SCHEMA nba_prod;

-- Dimensions
CREATE TABLE nba_prod.dim_season (
  season_id INTEGER PRIMARY KEY,
  year_start INTEGER NOT NULL,
  year_end INTEGER NOT NULL,
  era_label TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE nba_prod.dim_team (
  team_id INTEGER PRIMARY KEY,
  abbreviation TEXT NOT NULL,
  team_name TEXT,
  nickname TEXT,
  city TEXT,
  state TEXT,
  year_founded INTEGER,
  last_year INTEGER,
  source_id INTEGER,
  load_timestamp TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE nba_prod.dim_player (
  player_id INTEGER PRIMARY KEY,
  full_name TEXT NOT NULL,
  first_name TEXT,
  last_name TEXT,
  birth_date DATE,
  height_cm REAL,
  weight_kg REAL,
  debut_season_id INTEGER REFERENCES nba_prod.dim_season(season_id),
  source_id INTEGER,
  load_timestamp TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE nba_prod.dim_game (
  game_id INTEGER PRIMARY KEY,
  season_id INTEGER REFERENCES nba_prod.dim_season(season_id),
  game_date DATE NOT NULL,
  game_type TEXT,
  home_team_id INTEGER REFERENCES nba_prod.dim_team(team_id),
  away_team_id INTEGER REFERENCES nba_prod.dim_team(team_id),
  arena_id INTEGER,
  attendance INTEGER,
  source_id INTEGER,
  load_timestamp TIMESTAMP
);

-- Facts
CREATE TABLE nba_prod.fact_player_game_stats (
  player_id INTEGER REFERENCES nba_prod.dim_player(player_id),
  game_id INTEGER REFERENCES nba_prod.dim_game(game_id),
  team_id INTEGER REFERENCES nba_prod.dim_team(team_id),
  season_id INTEGER REFERENCES nba_prod.dim_season(season_id),
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

CREATE TABLE nba_prod.fact_team_game_stats (
    game_id VARCHAR NOT NULL,
    team_id INTEGER NOT NULL,
    is_home BOOLEAN NOT NULL,
    -- Scoring
    pts INTEGER,
    -- Shooting  
    fgm INTEGER,
    fga INTEGER,
    fg_pct FLOAT,
    fg3m INTEGER,
    fg3a INTEGER,
    fg3_pct FLOAT,
    ftm INTEGER,
    fta INTEGER,
    ft_pct FLOAT,
    -- Rebounds
    oreb INTEGER,
    dreb INTEGER,
    reb INTEGER,
    -- Other stats
    ast INTEGER,
    stl INTEGER,
    blk INTEGER,
    tov INTEGER,
    pf INTEGER,
    plus_minus INTEGER,
    -- Metadata
    data_source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (game_id, team_id),
    FOREIGN KEY (game_id) REFERENCES nba_prod.dim_game(game_id),
    FOREIGN KEY (team_id) REFERENCES nba_prod.dim_team(team_id)
);

-- Bridge for lineage/audit
CREATE TABLE nba_prod.bridge_duckdb_sources (
  fact_table TEXT NOT NULL,
  record_pk TEXT NOT NULL,
  source_id INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(fact_table, record_pk)
);
-- Phase 2 DDL Extensions

CREATE TABLE nba_prod.dim_referee (
    referee_id INTEGER PRIMARY KEY,
    full_name VARCHAR NOT NULL,
    first_name VARCHAR,
    last_name VARCHAR,
    jersey_number VARCHAR
);

CREATE TABLE nba_prod.dim_coach (
    coach_id INTEGER PRIMARY KEY,
    full_name VARCHAR NOT NULL,
    first_name VARCHAR,
    last_name VARCHAR,
    birth_date DATE
);

CREATE TABLE nba_prod.fact_shot_chart (
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

CREATE TABLE nba_prod.bridge_player_team (
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
CREATE TABLE nba_prod.dim_date AS
WITH date_series AS (
    SELECT UNNEST(generate_series(
        timestamp '1946-01-01',
        timestamp '2030-12-31',
        INTERVAL 1 DAY
    )) as date_ts
)
SELECT 
    CAST(date_ts AS DATE) as date_key,
    EXTRACT(YEAR FROM date_ts) as year,
    EXTRACT(MONTH FROM date_ts) as month,
    EXTRACT(DAY FROM date_ts) as day,
    DAYNAME(date_ts) as day_name,
    CASE 
        WHEN EXTRACT(MONTH FROM date_ts) IN (10,11,12,1,2,3,4,5,6)
        THEN CONCAT(
            EXTRACT(YEAR FROM date_ts) - 
            CASE WHEN EXTRACT(MONTH FROM date_ts) >= 10 
                 THEN 0 ELSE 1 END,
            '-',
            SUBSTR(CAST(EXTRACT(YEAR FROM date_ts) - 
            CASE WHEN EXTRACT(MONTH FROM date_ts) >= 10 
                 THEN 0 ELSE 1 END + 1 AS VARCHAR), 3, 2)
        )
    END as season_code
FROM date_series;