# Schema Design Patterns for NBA Databases

**Confidence: 90%**

> **Analysis Scope:** Common schema patterns, anti-patterns, and design principles extracted from 5+ NBA database implementations to guide nba-live schema design.

---

## 🎯 **Core Schema Patterns**

### **1. Entity Relationship Patterns**

#### **Star Schema (Most Common)**
```
       players ←─┐
           ↓     │
    player_game_stats ──→ games ──→ teams
           ↓     │                    ↑
       seasons ←─┘                    │
                                 team_seasons
```

**Benefits:**
- ✅ Optimized for analytical queries
- ✅ Clear separation of facts and dimensions
- ✅ Easy to understand business logic

**Drawbacks:**
- ❌ Some denormalization required
- ❌ More complex for transactional updates

#### **Normalized Schema (Academic Projects)**
```
players → player_team_seasons → team_seasons → teams
    ↓           ↓                    ↓           ↓
player_stats → game_stats ← games ←─┘      conferences
    ↓           ↓             ↓
positions   stat_types    venues
```

**Benefits:**
- ✅ No data redundancy
- ✅ Perfect data integrity
- ✅ Easy to maintain relationships

**Drawbacks:**
- ❌ Complex analytical queries (many joins)
- ❌ Performance issues at scale
- ❌ Difficult for end-user queries

---

## 🏛️ **Foundational Entity Patterns**

### **Player Entity Design**

#### **✅ Recommended Pattern**
```sql
CREATE TABLE players (
    player_id SERIAL PRIMARY KEY,
    nba_api_id INTEGER UNIQUE,        -- External system ID
    basketball_reference_id VARCHAR(50), -- bbref-player-id
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    display_name VARCHAR(100),        -- "LeBron James"
    birth_date DATE,
    birth_city VARCHAR(50),
    birth_state VARCHAR(30),
    birth_country VARCHAR(50),
    height_inches INTEGER,
    weight_lbs INTEGER,
    college VARCHAR(100),
    draft_year INTEGER,
    draft_round INTEGER,
    draft_pick INTEGER,
    debut_date DATE,
    final_game_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    jersey_number INTEGER,            -- Current number
    position VARCHAR(10),             -- Current position
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Separate table for position history
CREATE TABLE player_positions (
    player_id INTEGER REFERENCES players(player_id),
    position VARCHAR(10) NOT NULL,
    start_season VARCHAR(7),
    end_season VARCHAR(7),
    is_primary BOOLEAN DEFAULT FALSE
);
```

#### **❌ Anti-Pattern: Single String Names**
```sql
-- Avoid this pattern
CREATE TABLE players (
    player_name VARCHAR(100),  -- "James, LeBron" - parsing nightmare
    -- ...
);
```

### **Team Entity Design**

#### **✅ Recommended Pattern with Franchise Tracking**
```sql
CREATE TABLE franchises (
    franchise_id SERIAL PRIMARY KEY,
    franchise_name VARCHAR(100),      -- "Lakers"
    founded_year INTEGER,
    current_team_id INTEGER           -- Points to current iteration
);

CREATE TABLE teams (
    team_id SERIAL PRIMARY KEY,
    franchise_id INTEGER REFERENCES franchises(franchise_id),
    team_name VARCHAR(100) NOT NULL,  -- "Los Angeles Lakers"
    city VARCHAR(50) NOT NULL,        -- "Los Angeles"
    nickname VARCHAR(50) NOT NULL,    -- "Lakers"
    abbreviation VARCHAR(5) NOT NULL, -- "LAL"
    conference VARCHAR(10),           -- "Western"
    division VARCHAR(20),             -- "Pacific"
    primary_color VARCHAR(7),         -- "#552583"
    secondary_color VARCHAR(7),       -- "#FDB927"
    founded_date DATE,
    relocated_date DATE,              -- NULL if never relocated
    active_from DATE NOT NULL,
    active_to DATE,                   -- NULL if currently active
    arena_name VARCHAR(100),
    arena_capacity INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Key Benefits:**
- Handles relocations (Seattle SuperSonics → OKC Thunder)
- Tracks name changes (New Orleans Hornets → Pelicans)
- Preserves historical accuracy

### **Game Entity Design**

#### **✅ Recommended Pattern**
```sql
CREATE TABLE games (
    game_id SERIAL PRIMARY KEY,
    nba_game_id VARCHAR(20) UNIQUE,   -- "0022300001"
    season_id VARCHAR(7) NOT NULL,    -- "2023-24"
    game_date DATE NOT NULL,
    game_time TIME,
    
    home_team_id INTEGER REFERENCES teams(team_id),
    away_team_id INTEGER REFERENCES teams(team_id),
    
    home_score INTEGER,
    away_score INTEGER,
    
    -- Game flow
    regulation_periods INTEGER DEFAULT 4,
    overtime_periods INTEGER DEFAULT 0,
    total_periods INTEGER GENERATED ALWAYS AS (regulation_periods + overtime_periods),
    
    -- Context
    game_type VARCHAR(20) NOT NULL,   -- 'regular', 'playoffs', 'preseason'
    playoff_round VARCHAR(20),        -- 'first-round', 'conference-finals', etc.
    playoff_game_number INTEGER,      -- Game 1, 2, 3... of series
    
    -- Venue & attendance
    venue_name VARCHAR(100),
    attendance INTEGER,
    sellout BOOLEAN,
    
    -- Officials
    referee_1 VARCHAR(100),
    referee_2 VARCHAR(100),
    referee_3 VARCHAR(100),
    
    -- Data quality
    data_source VARCHAR(50) NOT NULL,
    data_quality_score DECIMAL(3,2),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_scores CHECK (home_score >= 0 AND away_score >= 0),
    CONSTRAINT different_teams CHECK (home_team_id != away_team_id),
    CONSTRAINT valid_periods CHECK (overtime_periods >= 0)
);
```

---

## 📊 **Statistics Schema Patterns**

### **Player Game Statistics**

#### **✅ Era-Aware Statistics Design**

---

## 🏗️ **Reference Architecture Blueprint**
*From Perplexity Research - "Gold Standard" Pattern*

### **5-Layer Architecture**

#### **1. Landing Zone (Raw Storage)**
```sql
-- Raw JSON/CSV in object storage or DuckDB
CREATE TABLE raw_api_responses (
    response_id UUID PRIMARY KEY,
    endpoint VARCHAR(200),
    request_params JSONB,
    response_body JSONB,
    response_timestamp TIMESTAMP,
    file_path VARCHAR(500)  -- For file-based storage
);
```

#### **2. Staging Schema (1:1 API Mirror)**
```sql
-- Mirror every API field verbatim for debugging
CREATE SCHEMA staging;

CREATE TABLE staging.stg_players (
    nba_api_id INTEGER,
    first_name VARCHAR,
    last_name VARCHAR,
    is_active BOOLEAN,
    -- Raw response fields preserved exactly
    raw_response JSONB,
    loaded_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE staging.stg_game_stats (
    game_id VARCHAR,
    player_id INTEGER,
    points INTEGER,
    -- Every API field included
    raw_response JSONB,
    loaded_at TIMESTAMP DEFAULT NOW()
);
```

#### **3. Core Warehouse Schema (Star Design)**
```sql
-- Dimensional Tables
CREATE TABLE dim_player (
    player_id SERIAL PRIMARY KEY,
    nba_api_id INTEGER UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    birth_date DATE,
    height_inches SMALLINT,
    weight_lbs SMALLINT,
    draft_pick SMALLINT,
    draft_year SMALLINT,
    position VARCHAR(10),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE dim_team (
    team_id SERIAL PRIMARY KEY,
    nba_team_id INTEGER UNIQUE,
    team_name VARCHAR(100) NOT NULL,
    abbreviation VARCHAR(5) NOT NULL,
    city VARCHAR(50) NOT NULL,
    conference VARCHAR(10),
    division VARCHAR(20),
    founded_year INTEGER
);

CREATE TABLE dim_season (
    season_id VARCHAR(7) PRIMARY KEY,  -- "2023-24"
    start_date DATE,
    end_date DATE,
    playoff_start_date DATE,
    total_games INTEGER,
    season_type VARCHAR(20)  -- "regular", "playoffs"
);

CREATE TABLE dim_arena (
    arena_id SERIAL PRIMARY KEY,
    arena_name VARCHAR(100) NOT NULL,
    city VARCHAR(50),
    capacity INTEGER,
    opened_year INTEGER
);

-- Fact Tables
CREATE TABLE fact_game (
    game_id SERIAL PRIMARY KEY,
    nba_game_id VARCHAR(20) UNIQUE,
    season_id VARCHAR(7) REFERENCES dim_season(season_id),
    game_date DATE NOT NULL,
    home_team_id INTEGER REFERENCES dim_team(team_id),
    away_team_id INTEGER REFERENCES dim_team(team_id),
    arena_id INTEGER REFERENCES dim_arena(arena_id),
    home_score SMALLINT,
    away_score SMALLINT,
    attendance INTEGER,
    game_type VARCHAR(20) NOT NULL
);

CREATE TABLE fact_boxscore_player (
    game_id INTEGER REFERENCES fact_game(game_id),
    player_id INTEGER REFERENCES dim_player(player_id),
    team_id INTEGER REFERENCES dim_team(team_id),
    minutes DECIMAL(4,2),
    pts SMALLINT,
    ast SMALLINT,
    reb SMALLINT,
    stl SMALLINT,
    blk SMALLINT,
    turnover SMALLINT,
    fgm SMALLINT,
    fga SMALLINT,
    fg3m SMALLINT,
    fg3a SMALLINT,
    ftm SMALLINT,
    fta SMALLINT,
    plus_minus SMALLINT,
    PRIMARY KEY (game_id, player_id)
);

CREATE TABLE fact_shot (
    shot_id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES fact_game(game_id),
    player_id INTEGER REFERENCES dim_player(player_id),
    team_id INTEGER REFERENCES dim_team(team_id),
    period INTEGER,
    minutes_remaining INTEGER,
    seconds_remaining INTEGER,
    shot_made BOOLEAN,
    shot_type VARCHAR(50),
    shot_zone VARCHAR(50),
    shot_distance INTEGER,
    loc_x INTEGER,  -- Court coordinates
    loc_y INTEGER,
    shot_value INTEGER  -- 2 or 3 points
);

-- Advanced Analytics Table
CREATE TABLE fact_stint (
    stint_id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES fact_game(game_id),
    period INTEGER,
    start_time DECIMAL(5,2),
    end_time DECIMAL(5,2),
    duration DECIMAL(5,2),
    lineup_player_1 INTEGER REFERENCES dim_player(player_id),
    lineup_player_2 INTEGER REFERENCES dim_player(player_id),
    lineup_player_3 INTEGER REFERENCES dim_player(player_id),
    lineup_player_4 INTEGER REFERENCES dim_player(player_id),
    lineup_player_5 INTEGER REFERENCES dim_player(player_id),
    plus_minus DECIMAL(5,2),
    possessions DECIMAL(5,2)
);
```

#### **4. Analytics Views & Materialized Tables**
```sql
-- Popular aggregations pre-computed
CREATE MATERIALIZED VIEW vw_player_season_totals AS
SELECT 
    p.player_id,
    p.first_name || ' ' || p.last_name AS player_name,
    g.season_id,
    COUNT(*) AS games_played,
    ROUND(AVG(bs.minutes), 1) AS avg_minutes,
    SUM(bs.pts) AS total_points,
    ROUND(AVG(bs.pts), 1) AS ppg,
    SUM(bs.ast) AS total_assists,
    ROUND(AVG(bs.ast), 1) AS apg,
    SUM(bs.reb) AS total_rebounds,
    ROUND(AVG(bs.reb), 1) AS rpg,
    -- Advanced metrics
    ROUND(SUM(bs.fgm)::DECIMAL / NULLIF(SUM(bs.fga), 0), 3) AS fg_pct,
    ROUND(SUM(bs.fg3m)::DECIMAL / NULLIF(SUM(bs.fg3a), 0), 3) AS fg3_pct,
    ROUND(SUM(bs.ftm)::DECIMAL / NULLIF(SUM(bs.fta), 0), 3) AS ft_pct
FROM dim_player p
JOIN fact_boxscore_player bs ON p.player_id = bs.player_id
JOIN fact_game g ON bs.game_id = g.game_id
GROUP BY p.player_id, p.first_name, p.last_name, g.season_id;

CREATE MATERIALIZED VIEW vw_lineup_four_factors AS
SELECT 
    s.game_id,
    s.period,
    s.start_time,
    s.end_time,
    -- Lineup composition
    ARRAY[s.lineup_player_1, s.lineup_player_2, s.lineup_player_3, 
          s.lineup_player_4, s.lineup_player_5] AS lineup_players,
    -- Performance metrics
    s.plus_minus,
    s.possessions,
    s.plus_minus / NULLIF(s.possessions, 0) AS net_rating
FROM fact_stint s;
```

#### **5. Optional Side-Cars (Specialized Storage)**
```sql
-- Graph DB for relationships (Neo4j schema example)
CREATE (p:Player {nba_id: 2544, name: "LeBron James"})
CREATE (c:College {name: "St. Vincent-St. Mary High School"})
CREATE (coach:Coach {name: "Dru Joyce II"})
CREATE (p)-[:ATTENDED]->(c)
CREATE (p)-[:COACHED_BY]->(coach)

-- Document store for unstructured data (MongoDB schema)
{
  "_id": ObjectId("..."),
  "player_id": 2544,
  "scouting_report": {
    "strengths": ["court_vision", "basketball_iq", "leadership"],
    "weaknesses": ["three_point_consistency"],
    "notes": "Exceptional floor general with elite passing ability"
  },
  "media_mentions": [
    {
      "date": "2023-12-15",
      "source": "ESPN",
      "headline": "LeBron's triple-double leads Lakers past Nuggets",
      "sentiment": "positive"
    }
  ]
}
```

### **Best Practice DDL Patterns**

#### **✅ Composite Primary Keys**
```sql
-- Prevent duplicate player-game records
PRIMARY KEY (game_id, player_id)

-- Ensure unique shot records
PRIMARY KEY (game_id, player_id, period, shot_clock_time)
```

#### **✅ Comprehensive Constraints**
```sql
-- Statistical sanity checks
CONSTRAINT valid_scores CHECK (home_score >= 0 AND away_score >= 0),
CONSTRAINT valid_periods CHECK (period >= 1 AND period <= 8),
CONSTRAINT different_teams CHECK (home_team_id != away_team_id),
CONSTRAINT reasonable_minutes CHECK (minutes >= 0 AND minutes <= 65),
CONSTRAINT valid_percentages CHECK (fg_pct >= 0 AND fg_pct <= 1)

-- Business rule validation
CONSTRAINT valid_game_date CHECK (game_date >= '1946-11-01'),
CONSTRAINT future_game_check CHECK (game_date <= CURRENT_DATE + INTERVAL '1 year')
```

#### **✅ Performance Optimization**
```sql
-- Critical indexes for analytics queries
CREATE INDEX idx_boxscore_player_season ON fact_boxscore_player(player_id, game_id);
CREATE INDEX idx_boxscore_team_season ON fact_boxscore_player(team_id, game_id);
CREATE INDEX idx_game_date_season ON fact_game(game_date, season_id);
CREATE INDEX idx_shot_player_location ON fact_shot(player_id, loc_x, loc_y);

-- Partitioning for large fact tables
CREATE TABLE fact_boxscore_player_2024 PARTITION OF fact_boxscore_player
FOR VALUES FROM ('2023-10-01') TO ('2024-10-01');
```

```sql
CREATE TABLE player_game_stats (
    stats_id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES games(game_id),
    player_id INTEGER REFERENCES players(player_id),
    team_id INTEGER REFERENCES teams(team_id),
    
    -- Basic stats (available 1946+)
    minutes_played INTEGER,           -- Available 1951+, NULL before
    points INTEGER NOT NULL,
    
    -- Shooting (available 1946+, but inconsistent until 1950)
    field_goals_made INTEGER,
    field_goals_attempted INTEGER,
    field_goal_percentage DECIMAL(4,3) GENERATED ALWAYS AS (
        CASE WHEN field_goals_attempted > 0 
             THEN field_goals_made::DECIMAL / field_goals_attempted 
             ELSE NULL END
    ),
    
    -- Three-pointers (available 1979+)
    three_pointers_made INTEGER,      -- NULL before 1979-80
    three_pointers_attempted INTEGER, -- NULL before 1979-80
    
    -- Free throws (available 1946+)
    free_throws_made INTEGER,
    free_throws_attempted INTEGER,
    
    -- Rebounds (available 1950+, inconsistent until 1973)
    offensive_rebounds INTEGER,       -- Available 1973+
    defensive_rebounds INTEGER,       -- Available 1973+
    total_rebounds INTEGER,
    
    -- Playmaking (available 1963+, inconsistent until 1977)
    assists INTEGER,                  -- NULL before 1963-64
    
    -- Defense (available 1973+)
    steals INTEGER,                   -- NULL before 1973-74
    blocks INTEGER,                   -- NULL before 1973-74
    
    -- Turnovers (available 1977+)
    turnovers INTEGER,                -- NULL before 1977-78
    
    -- Fouls (available 1946+)
    personal_fouls INTEGER,
    
    -- Advanced (available 1996+)
    plus_minus INTEGER,               -- NULL before 1996-97
    
    -- Game context
    starter BOOLEAN,
    dnp_reason VARCHAR(50),           -- "injury", "coach's decision", etc.
    
    -- Data lineage
    data_source VARCHAR(50) NOT NULL,
    data_quality_score DECIMAL(3,2),
    era_completeness_score DECIMAL(3,2), -- Adjusted for era expectations
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Validate reasonable statistical ranges
    CONSTRAINT valid_minutes CHECK (minutes_played >= 0 AND minutes_played <= 65),
    CONSTRAINT valid_points CHECK (points >= 0 AND points <= 100),
    CONSTRAINT valid_fg_pct CHECK (field_goal_percentage >= 0 AND field_goal_percentage <= 1),
    CONSTRAINT valid_rebounds CHECK (total_rebounds >= 0 AND total_rebounds <= 50)
);
```

### **Season Aggregates Pattern**

#### **✅ Materialized View Approach**
```sql
CREATE MATERIALIZED VIEW player_season_stats AS
SELECT 
    player_id,
    season_id,
    team_id,
    COUNT(*) AS games_played,
    SUM(minutes_played) AS total_minutes,
    AVG(minutes_played) AS avg_minutes,
    SUM(points) AS total_points,
    AVG(points) AS avg_points,
    -- ... other aggregations
    
    -- Era-aware metrics
    AVG(data_quality_score) AS avg_data_quality,
    MIN(data_quality_score) AS min_data_quality,
    
    -- Computed advanced stats
    CASE WHEN SUM(field_goals_attempted) > 0 
         THEN SUM(field_goals_made)::DECIMAL / SUM(field_goals_attempted)
         ELSE NULL 
    END AS season_fg_percentage,
    
    NOW() AS computed_at
    
FROM player_game_stats 
JOIN games USING (game_id)
WHERE games.game_type = 'regular'  -- Exclude preseason
GROUP BY player_id, season_id, team_id;

-- Refresh strategy
CREATE INDEX ON player_season_stats (player_id, season_id);
```

---

## 🚨 **Schema Anti-Patterns to Avoid**

### **1. The "God Table" Anti-Pattern**

#### **❌ Avoid This**
```sql
-- 100+ column monster table
CREATE TABLE player_stats (
    player_name VARCHAR(100),
    team_name VARCHAR(100),
    season VARCHAR(10),
    -- 97 more columns of every possible statistic
    games_played INTEGER,
    minutes_played INTEGER,
    points INTEGER,
    -- ... every stat ever conceived
    per_36_points DECIMAL,
    true_shooting_pct DECIMAL,
    -- ... more computed stats
    win_shares DECIMAL,
    bpm DECIMAL
    -- No foreign keys, no normalization
);
```

**Problems:**
- Impossible to maintain
- No referential integrity
- Massive row size
- Cannot handle era-specific availability

### **2. String-Based Relationships Anti-Pattern**

#### **❌ Avoid This**
```sql
CREATE TABLE game_stats (
    player_name VARCHAR(100),         -- Should be player_id FK
    team_abbreviation VARCHAR(5),     -- Should be team_id FK
    opponent_abbreviation VARCHAR(5), -- Should be opponent_team_id FK
    game_date VARCHAR(20),            -- Should be DATE type
    season VARCHAR(20)                -- Should be season_id FK
);
```

**Problems:**
- No referential integrity
- Spelling variations break queries
- Team name changes break historical data
- Cannot efficiently join tables

### **3. Mixed Granularity Anti-Pattern**

#### **❌ Avoid This**
```sql
CREATE TABLE mixed_stats (
    player_id INTEGER,
    stat_type VARCHAR(50),  -- 'game', 'season', 'career'
    stat_value DECIMAL,
    date_or_season VARCHAR(20)  -- Sometimes '2023-01-15', sometimes '2022-23'
);
```

**Problems:**
- Cannot properly index
- Queries become complex
- Different business rules mixed together
- Temporal logic is impossible

---

## ✅ **Best Practice Patterns**

### **1. Audit Trail Pattern**
```sql
-- Add to every table
created_at TIMESTAMP DEFAULT NOW(),
updated_at TIMESTAMP DEFAULT NOW(),
created_by VARCHAR(50) DEFAULT 'system',
data_source VARCHAR(50) NOT NULL,
source_url VARCHAR(500),
extraction_timestamp TIMESTAMP,
data_quality_score DECIMAL(3,2)
```

### **2. Soft Delete Pattern**
```sql
-- Instead of DELETE, mark as inactive
deleted_at TIMESTAMP NULL,
is_active BOOLEAN DEFAULT TRUE,

-- Use in queries
WHERE deleted_at IS NULL
-- OR
WHERE is_active = TRUE
```

### **3. Data Quality Scoring Pattern**
```sql
CREATE TABLE data_quality_metrics (
    metric_id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER NOT NULL,
    completeness_score DECIMAL(3,2),  -- 0.0 to 1.0
    accuracy_score DECIMAL(3,2),      -- Based on validation rules
    timeliness_score DECIMAL(3,2),    -- How fresh is the data
    consistency_score DECIMAL(3,2),   -- Cross-table validation
    overall_score DECIMAL(3,2) GENERATED ALWAYS AS (
        (completeness_score + accuracy_score + timeliness_score + consistency_score) / 4
    ),
    measured_at TIMESTAMP DEFAULT NOW()
);
```

### **4. Era Metadata Pattern**
```sql
CREATE TABLE stat_availability (
    stat_name VARCHAR(50) PRIMARY KEY,
    first_tracked_season VARCHAR(7),      -- '1973-74'
    consistent_from_season VARCHAR(7),    -- '1977-78'
    tracking_notes TEXT,
    quality_issues TEXT,
    expected_completeness_by_era JSONB    -- {'1946-1963': 0.4, '1963-1980': 0.8}
);

-- Usage in validation
CREATE OR REPLACE FUNCTION validate_era_stat(
    stat_name TEXT, 
    season TEXT, 
    stat_value INTEGER
) RETURNS BOOLEAN AS $$
DECLARE
    first_season TEXT;
BEGIN
    SELECT first_tracked_season INTO first_season 
    FROM stat_availability 
    WHERE stat_name = $1;
    
    -- NULL values allowed before stat was tracked
    IF $2 < first_season AND $3 IS NULL THEN
        RETURN TRUE;
    END IF;
    
    -- Non-null values not allowed before stat was tracked
    IF $2 < first_season AND $3 IS NOT NULL THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;
```

---

## 🎯 **Recommendations for nba-live**

### **Schema Architecture Decision**
1. **Use Star Schema**: Optimize for analytical queries
2. **PostgreSQL**: Superior to SQLite for our scale and complexity
3. **Era-Aware Design**: Built-in handling for statistical evolution
4. **Quality-First**: Data quality scoring throughout

### **Key Design Principles**
1. **Explicit Over Implicit**: NULL means "not available", not "zero"
2. **Audit Everything**: Full data lineage and provenance tracking
3. **Validate Early**: Business rules enforced at database level
4. **Design for Time**: Handle historical corrections and updates
5. **Separate Concerns**: Don't mix transactional and analytical schemas

### **Implementation Priorities**
1. **Core Entities**: Players, Teams, Games, Seasons (foundation)
2. **Game Statistics**: Player and team performance data
3. **Quality Framework**: Data validation and scoring system
4. **Season Aggregates**: Materialized views for analytics
5. **Advanced Features**: Shot charts, play-by-play (future phases)

---

**Research Completed**: ✅ Phase 1.0 - Schema Design Patterns Analysis  
**Next Steps**: Implement recommended schema patterns in nba-live database design 