# TODO – Engineering Task List

## ✅ Completed
- [x] **Phase 0 - Bootstrap**: Repository scaffolding, CI/CD, Poetry setup
- [x] **PlayerMatcher Implementation**: Fuzzy player deduplication utility with comprehensive testing
- [x] **Star Schema DDL Drafted**: `db/ddl/00_create_schema.sql` defining core dimension & fact tables
- [x] **DuckDB Dependency Added**: `pyproject.toml` switched to DuckDB 0.10
- [x] **Kaggle Player Loader Stub**: `etl/kaggle/load_kaggle_players.py` with lineage logging

## ✅ **Phase 1 – Research & Source Assessment (COMPLETED & EXPANDED)**

### Research Tasks (✅ COMPLETED - 35+ REPOSITORIES ANALYZED)
- [x] **1.0 Research Task: Existing NBA Database Projects** 
  - [x] **Core Analysis**: wyattowalsh/nbadb, toddwschneider/nba-shots-db, shufinskiy/nba_data, matsonj/nba-monte-carlo
  - [x] **Phase 1 Expansion**: ganymex/7-entity model, eoinmooremath/AWS pipeline, rkhmehta/streaming, dimitri/minimal design
  - [x] **Universal Schemas**: mpope9/nba-sql multi-DB support, NocturneBear/BigQuery exports  
  - [x] **Management Systems**: Rak6869/NBA_management_system, annapettigrew/dual-source integration
  - [x] **Advanced Patterns**: Multi-database federation, stint-level analytics, cloud-native ETL
  - [x] **Perplexity Research**: Best practices, anti-patterns, 5-layer reference architecture
  - [x] **Technology Evolution**: 4 generations of NBA database architecture identified
  - [x] **Comparative Framework**: Project evaluation matrix across 15+ criteria
  - [x] **MEGA EXPANSION**: 15+ additional repositories across specialized domains:
    - [x] **Betting Analytics**: NBA-Betting/NBA_Betting (comprehensive prediction system), kyleskom/NBA-Machine-Learning-Sports-Betting
    - [x] **API Ecosystem**: swar/nba_api (Python standard), jaebradley/basketball_reference_web_scraper, kshvmdn/nba.js
    - [x] **Educational Projects**: erilu/web-scraping-NBA-statistics (comprehensive tutorial), MadanThevar/NBA-Analysis-Project
    - [x] **Specialized Analytics**: pbpstats/pbpstats (play-by-play), DimaKudosh/pydfs-lineup-optimizer (fantasy)
    - [x] **Modern Pipelines**: ShaeInTheCloud/nba-stats-pipeline (AWS serverless), zsyed15/NBA_Data (Mage.AI)
    - [x] **Multi-Sport Platforms**: sportsdataverse/sportsdataverse-py, roclark/sportsipy
    - [x] **Blockchain Integration**: dapperlabs/nba-smart-contracts (NBA Top Shot)
  - [x] Document schema patterns, anti-patterns, and lessons learned
  - [x] Create research deliverables in `docs/research/`
  - **Key Links to Review:**
    - https://www.kaggle.com/datasets/sumitrodatta/nba-aba-baa-stats/data
    - https://github.com/wyattowalsh/sports-analytics/blob/main/basketball/README.md
    - https://github.com/wyattowalsh/data-science-notes
    - https://github.com/wyattowalsh/nbadb
    - https://github.com/wyattowalsh/NBA-attendance-prediction
    - https://www.kaggle.com/datasets/wyattowalsh/basketball
    - https://www.kaggle.com/datasets/justinas/nba-players-data
    - https://www.kaggle.com/datasets/eoinamoore/historical-nba-data-and-player-box-scores
    - https://sportsdatabase.com/NBA/query.html
    - https://www.reddit.com/r/datasets/comments/11n6ro1/comprehensive_nba_basketball_sqlite_database_on/
    - https://www.reddit.com/r/fantasybball/comments/1hqh2vj/nba_historical_dataset_box_scores_player_stats/
    - https://www.kaggle.com/datasets/eoinamoore/historical-nba-data-and-player-box-scores/

### Source Assessment Tasks  
- [x] **1.1 Comprehensive Source Mapping**
  - [x] Document NBA Stats API capabilities and rate limits
  - [x] Catalog Basketball-Reference.com scraping approaches
  - [x] Evaluate Kaggle datasets for historical data gaps
  - [x] Research ESPN API supplementary data access

- [x] **1.2 Coverage Matrix Creation**
  - [x] Build era-by-statistic availability matrix
  - [x] Document data quality scores by source and timeframe
  - [x] Identify explicit gaps and research impact

- [x] **1.3 Legal & Compliance Research**
  - [x] Document per-source rate limits and ToS requirements
  - [x] Research academic use justifications and fair use policies
  - [x] Create compliance framework for ethical data collection

## 📋 **Upcoming Phases**

- [ ] **Phase 2 – Database Design & Architecture**
  - [ ] Finalize remaining dimension & fact tables (shots, play-by-play, contracts, injuries)
  - [ ] Add audit history tables or extend `bridge_duckdb_sources`
  - [ ] Implement season-based Parquet partitioning strategy
  - [ ] Generate ER diagram for documentation
  - [ ] Decide on vector storage approach (DuckDB extension vs external)

- [ ] **Phase 3 – Modern Era ETL Pipeline**
  - [ ] Research ETL architecture patterns and frameworks
  - [ ] Implement NBA API extractors with rate limiting
  - [ ] Build transformation pipeline with data quality scoring

## 🛠 **Technical Debt & Enhancements**

- [ ] **Deduplication Strategy**
  - [x] Design fuzzy player matcher (birthdate, team overlap, nickname variations)
  - [x] Implement PlayerMatcher class in `etl/deduplication/player_matcher.py`
  - [ ] Add comprehensive unit tests for PlayerMatcher
  - [ ] Implement team name normalization utility

- [ ] **Incremental Historical Refresh**
  - [ ] Design quarterly re-scrape job for historical seasons
  - [ ] Implement diff and merge corrections into existing records

- [ ] **Performance Optimization**
  - [ ] Define index strategy for high-volume queries
  - [ ] Evaluate partitioning (e.g., by season) for `player_game_stats`
  - [ ] Consider materialized views for era aggregates

- [ ] **Retroactive Corrections Framework**
  - [ ] Design `RetroactiveCorrectionsHandler` in `etl/corrections/retroactive_handler.py`
  - [ ] Add `player_game_stats_history` versioning table to schema migration
  - [ ] Implement automated discrepancy scanner (look-back 30 days)

- [ ] **Play-by-Play Handling (Deferred)**
  - [ ] Decide compression format (msgpack + gzip?)
  - [ ] Prototype `PlayByPlayStorage.compress_game_data()`

- [ ] **API Layer (Future)**
  - [ ] Scaffold FastAPI server in `nba_live/api/server.py`
  - [ ] Implement REST endpoints for players, games, seasons
  - [ ] Add `/query/sql` endpoint with read-only guard + limit
  - [ ] Evaluate GraphQL vs REST hybrid approach
  - [ ] Plan WebSocket live updates (post-archive)

## 📝 **Documentation Pipeline**
- [x] `docs/research/existing-projects.md` - Analysis of 5+ NBA database projects
- [x] `docs/research/schema-patterns.md` - Common design patterns and anti-patterns  
- [x] `docs/research/lessons-learned.md` - Key insights to apply/avoid
- [x] `docs/data-sources.md` - Complete source catalog with access methods
- [x] `docs/coverage-matrix.md` - Detailed availability by era/stat/team
- [x] `docs/gap-documentation.md` - Research impact of missing data *(integrated into coverage-matrix.md)*
- [x] `docs/legal-compliance.md` - Rate limits, ToS, scraping ethics *(integrated into data-sources.md)* 