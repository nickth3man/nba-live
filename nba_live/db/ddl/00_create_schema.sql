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
  fact_table TEXT,
  record_pk TEXT,
  source_id INTEGER,
  ingestion_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(fact_table, record_pk, source_id)
); 