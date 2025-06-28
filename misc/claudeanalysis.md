### Database Overview

The nba-live database contains **16 tables** with approximately **13.7 million** records total, with the majority (13.6M) being play-by-play data. The database follows a well-structured design with clear entity relationships across three main domains: **Players**, **Teams**, and **Games**.

### Primary Entities and Key Relationships

#### 1. **Player Domain** (Blue in ERD)

- **Core Entity**: `player` table (4,831 records)
  - Primary Key: `id` (BIGINT)
  - Contains basic player identification
- **Extended Information**: `common_player_info` (4,171 records)

  - Primary Key: `person_id` (matches `player.id`)
  - Foreign Key: `team_id` → `team.id`
  - Contains comprehensive player details including physical stats, draft info, and current team

- **Draft Information**:
  - `draft_history`: Historical draft data with FK to both `player.id` and `team.id`
  - `draft_combine_stats`: Pre-draft measurements and performance metrics

#### 2. **Team Domain** (Purple in ERD)

- **Core Entity**: `team` table (30 records)
  - Primary Key: `id` (BIGINT)
  - Contains basic team identification
- **Extended Information**:
  - `team_details`: Arena info, management, and social media
  - `team_history`: Historical team data including relocations
  - `team_info_common`: (Currently empty - appears to be a metadata table)

#### 3. **Game Domain** (Red in ERD)

- **Core Entity**: `game` table (65,698 records)
  - Primary Key: `game_id` (VARCHAR)
  - Foreign Keys: `team_id_home` and `team_id_away` → `team.id`
  - Contains complete box score statistics for both teams
- **Game Details**:
  - `game_info`: Attendance and timing data
  - `game_summary`: Game status and broadcast info
  - `line_score`: Quarter-by-quarter scoring (supports up to 10 overtimes!)
  - `other_stats`: Advanced team statistics
- **Game Participants**:
  - `play_by_play`: Detailed game events (13.6M records)
    - Multiple FKs to `player.id` (player1, player2, player3)
  - `inactive_players`: Players who didn't play
  - `officials`: Game referees

### Key Interconnections

1. **Player-Team Relationships**:

   - Players connect to teams through `common_player_info.team_id`
   - Draft history links players to the teams that drafted them
   - Many-to-many relationship over time (players change teams)

2. **Team-Game Relationships**:

   - Each game has exactly two teams (home and away)
   - Teams appear in multiple games throughout seasons
   - 63 distinct home teams and 72 away teams suggest historical data including relocated/defunct teams

3. **Player-Game Relationships**:

   - Direct connection through `play_by_play` events
   - `inactive_players` tracks roster members who didn't play
   - Each play can involve up to 3 players

4. **Temporal Relationships**:
   - `season_id` and `season` fields connect data across years
   - Historical tracking through draft years and team history
   - Game dates allow chronological analysis

### Data Integrity Observations

1. **Player Coverage**: 4,171 of 4,831 players have detailed info (86% coverage)
2. **Team Anomaly**: More distinct team IDs in games (63-72) than in team table (30), suggesting historical teams
3. **Missing Data**: `team_info_common` table structure exists but contains no data
4. **Rich Play-by-Play**: Average of ~207 events per game (13.6M events / 65.7K games)

This database design enables complex queries across:

- Player career trajectories
- Team performance analysis
- Game-by-game breakdowns
- Historical comparisons
- Draft analysis and player development
- Play-by-play sequence analysis

The structure supports both current NBA analytics and historical research, with comprehensive tracking of players, teams, and games across multiple seasons.
