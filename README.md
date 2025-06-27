# NBA-Live MotherDuck Database

## Overview

This repository provides a fully-queryable MotherDuck (DuckDB-compatible) database containing **NBA play-by-play and summary statistics from the league's first season (1946-47) through the 2022-23 Finals (12 Jun 2023)**.  
The data were sourced from the NBA Stats API and ingested via automated Python pipelines, then uploaded to MotherDuck for cloud-scale analytics.

> **Key takeaway:** You have _77 years_ of regular-season & playoff data (games, players, teams, drafts, combine metrics, etc.) in one place with fast, serverless SQL.

---

## Connecting

1. Install the DuckDB CLI (≥ 0.10.3) or use any DuckDB client/driver.
2. Authenticate with MotherDuck:
   ```bash
   duckdb motherduck:nba-live
   -- or
   duckdb
   "INSTALL httpfs; LOAD httpfs; SET motherduck_token='YOUR_TOKEN';"
   ```
3. In this project's workflow we connect from the Cursor AI assistant:
   ```sql
   -- Already done in chat
   USE "nba-live";
   ```

---

## Schema Snapshot (Jun 2025)

| #   | Table               | Rows       |
| --- | ------------------- | ---------- |
| 1   | common_player_info  | 4 171      |
| 2   | draft_combine_stats | 1 202      |
| 3   | draft_history       | 7 990      |
| 4   | game                | 65 698     |
| 5   | game_info           | 58 053     |
| 6   | game_summary        | 58 110     |
| 7   | inactive_players    | 110 191    |
| 8   | line_score          | 58 053     |
| 9   | officials           | 70 971     |
| 10  | other_stats         | 28 271     |
| 11  | play_by_play        | 13 592 899 |
| 12  | player              | 4 831      |
| 13  | team                | 30         |
| 14  | team_details        | 25         |
| 15  | team_history        | 52         |
| 16  | team_info_common    | 0          |

**Storage footprint:** ~8 GB compressed parquet on MotherDuck (play-by-play dominates).

---

## Data Coverage

- **First recorded game:** 1 Nov 1946 (NYK @ TOR)
- **Most recent game:** 12 Jun 2023 (DEN 94 – 90 MIA, 2023 Finals G5)
- Regular-season & playoffs flagged by `season_type`.

---

## Quick-start Queries

```sql
-- 1. Top 10 single-game scoring performances (since 1980)
SELECT p.display_first_last AS player,
       gs.game_date,
       gs.pts_home AS pts_home,
       gs.pts_away AS pts_away,
       CASE WHEN gs.team_id_home = pbp.player_id THEN gs.team_name_home ELSE gs.team_name_away END AS team
FROM game_summary gs
JOIN play_by_play pbp USING (game_id)
JOIN player p ON pbp.player_id = p.player_id
WHERE gs.game_date >= DATE '1980-10-01'
  AND pbp.eventmsgtype = 1            -- made FG
GROUP BY ALL
ORDER BY pbp.score DESC
LIMIT 10;
```

```sql
-- 2. Franchise win-loss records
SELECT t.team_name,
       SUM(CASE WHEN wl_home = 'W' THEN 1 ELSE 0 END
           + CASE WHEN wl_away = 'W' THEN 1 ELSE 0 END)   AS wins,
       SUM(CASE WHEN wl_home = 'L' THEN 1 ELSE 0 END
           + CASE WHEN wl_away = 'L' THEN 1 ELSE 0 END)   AS losses,
       ROUND(100.0 * wins::DOUBLE / (wins+losses), 2)     AS win_pct
FROM game g
JOIN team t ON t.team_id = g.team_id_home OR t.team_id = g.team_id_away
GROUP BY 1
ORDER BY win_pct DESC;
```

```sql
-- 3. Average pace (possessions) by season since 2000
WITH poss AS (
  SELECT season_id,
         0.5 * ((fga_home + 0.4 * fta_home - 1.07 * (oreb_home / (oreb_home + dreb_away)) * (fga_home - fgm_home) + tov_home)
              + (fga_away + 0.4 * fta_away - 1.07 * (oreb_away / (oreb_away + dreb_home)) * (fga_away - fgm_away) + tov_away)) AS possessions
  FROM game
  WHERE season_id >= 2000
)
SELECT season_id, ROUND(AVG(possessions),2) AS avg_possessions_per_team
FROM poss
GROUP BY season_id
ORDER BY season_id;
```

> **Tip:** Because DuckDB supports queries that start with `FROM`, you can shorten exploratory SQL to e.g.  
> `FROM game WHERE season_id = 2023 SAMPLE 10 ROWS;`

---

## Analytical Ideas

- **Draft ROI:** Join `draft_history` with career `player` / `common_player_info` to evaluate pick value.
- **Referee tendencies:** Aggregate `officials` & `play_by_play` to find refs with the highest foul call rates.
- **Clutch performance:** Filter `play_by_play` for last 5 minutes & ±5 score margin to rank clutch shooters.
- **Injury impact:** Use `inactive_players` to measure lineup continuity vs. team performance.

---

## Why MotherDuck?

MotherDuck provides serverless DuckDB with cloud object-storage backing, meaning you get:

- **Shared access** without shipping `.duckdb` files.
- **Scales to billions of rows** (vectorized execution + object store).
- **Built-in AI functions** (e.g., `prompt()`) for natural-language insights.

---

## Contributing / Next Steps

- **Extend the ETL** to pull real-time 2023-24 & beyond.
- **Add advanced stats** (e.g., RAPM, lineup data) in new tables.
- **Build dashboards** (Streamlit, DuckDB + Vega) to visualize league trends.

Feel free to open issues or PRs with new analyses!  
_Enjoy exploring 75 + years of NBA history._
