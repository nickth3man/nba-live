# NBA-Live – Final Comprehensive Roadmap
## Explicit Gaps Data Archive Approach

**Confidence: 95%**

> **Primary Goal:** Build a complete local NBA database (1946-present) with explicit gap documentation, raw file preservation, and nightly updates. AI agent development deferred as future enhancement.

---

## **Project Overview**

### **Core Principles**
- **Data Completeness Over Perfection:** Collect everything available, document what's missing
- **Explicit Gaps:** NULL values where data doesn't exist, no statistical imputation
- **Raw Preservation:** Keep original source files with timestamps for future reprocessing
- **Research-Grade Quality:** Full provenance tracking and data confidence scoring

### **Storage Architecture (50GB Budget)**
```
nba-live/
├── data/
│   ├── raw/                    # ~30GB - Timestamped source files
│   │   ├── daily/YYYY-MM-DD/
│   │   ├── historical/
│   │   └── kaggle-datasets/
│   ├── processed/              # ~15GB - Cleaned, standardized
│   └── exports/               # Research-ready extracts
├── database/                   # ~5GB - DuckDB (nba_live.duckdb)
├── docs/                      # Comprehensive documentation
├── etl/                       # Data pipeline code
└── monitoring/                # Quality assurance tools
```

---

## **Phase 0: Project Bootstrap (½ day)**

### **Repository Setup**
```bash
# Initialize with full DevOps foundation
nba-live/
├── .github/workflows/ci.yml   # Lint → test → docs pipeline
├── pyproject.toml             # Poetry dependencies
├── .pre-commit-config.yaml    # Black, Ruff, MyPy
├── Makefile                   # Common operations
├── README.md                  # Project overview
├── LICENSE                    # MIT license
└── CODE_OF_CONDUCT.md
```

### **Tooling Stack**
- **Python 3.11+** with Poetry dependency management
- **Database:** DuckDB 0.10+ with columnar analytics (✅ ADOPTED)
- **Testing:** pytest with ≥90% coverage requirement  
- **Code Quality:** Black, Ruff, MyPy --strict
- **CI/CD:** GitHub Actions with automatic documentation deployment

### **Deliverable**
✅ Empty repository passing all CI checks

---

## **Phase 1: Data Reality Assessment (5 days)**

### **1.0 Research Task: Existing NBA Database Projects (1 day)**
**Study successful NBA database implementations to understand:**
- Schema design patterns used by [Columbia NBA Database](https://alubanana.github.io/database/columbia/web%20application/NBA-Database-Design/) and [NBA-DB projects](https://github.com/ichrist-gr/NBA-DB)
- Common data quality challenges and solutions from [filipmilanovic/nba_database](https://github.com/filipmilanovic/nba_database)
- Performance optimization strategies for multi-era data
- API design patterns for basketball statistics
- Legal/compliance approaches used by academic projects

**Research Deliverables:**
- `docs/research/existing-projects.md` - Analysis of 5+ NBA database projects
- `docs/research/schema-patterns.md` - Common design patterns and anti-patterns
- `docs/research/lessons-learned.md` - Key insights to apply/avoid

### **1.1 Comprehensive Source Mapping**
**Modern Era Sources (1997-2025):**
- NBA Stats API (stats.nba.com) - primary
- wyattowalsh/basketball Kaggle dataset - backup/validation
- ESPN API - supplementary

**Historical Sources (1946-1997):**
- Basketball-Reference.com - primary historical
- eoinamoore/historical-nba-data - secondary
- Reddit community datasets - tertiary

### **1.2 Coverage Matrix Creation**
```markdown
# Data Availability Matrix

| Stat Category | 1946-1963 | 1963-1980 | 1980-1997 | 1997-2025 |
|---------------|-----------|-----------|-----------|-----------|
| Games/Scores  | ✅ 95%    | ✅ 98%    | ✅ 99%    | ✅ 100%   |
| Basic Box Score| ⚠️ 60%   | ✅ 85%    | ✅ 95%    | ✅ 100%   |
| Assists       | ❌ 0%     | ✅ 80%    | ✅ 95%    | ✅ 100%   |
| Steals/Blocks | ❌ 0%     | ⚠️ 40%    | ✅ 95%    | ✅ 100%   |
| Minutes Played| ❌ 0%     | ⚠️ 30%    | ✅ 90%    | ✅ 100%   |
| Shot Locations| ❌ 0%     | ❌ 0%     | ❌ 0%     | ✅ 99%    |
| Play-by-Play  | ❌ 0%     | ❌ 0%     | ❌ 0%     | ✅ 95%    |
```

### **1.3 Gap Documentation Standards**
```python
# Data quality scoring system
class DataQuality:
    COMPLETE = 1.0      # >99% coverage
    HIGH = 0.8          # 90-99% coverage  
    MODERATE = 0.6      # 70-89% coverage
    LOW = 0.4           # 40-69% coverage
    SPARSE = 0.2        # 10-39% coverage
    MISSING = 0.0       # <10% coverage
```

### **Deliverables**
- `docs/data-sources.md` - Complete source catalog with access methods
- `docs/coverage-matrix.md` - Detailed availability by era/stat/team
- `docs/gap-documentation.md` - Research impact of missing data
- `docs/legal-compliance.md` - Rate limits, ToS, scraping ethics

---

## **Phase 2: Database Design & Architecture (4 days)**

### **2.0 Research Task: Schema Design Best Practices (1 day)**
+✅ **COMPLETED** - Research integrated into existing-projects.md and schema-patterns.md
**Study database design patterns for sports analytics:**
- Time-series data modeling for historical statistics
- Handling schema evolution across basketball eras
- Indexing strategies for analytical queries
- Partitioning approaches for large datasets
- Data warehouse vs transactional design trade-offs

**Research Deliverables:**
-- `docs/research/schema-research.md` - Database design pattern analysis
-- `docs/research/performance-patterns.md` - Indexing and partitioning strategies
+- ✅ `docs/research/schema-patterns.md` - Database design pattern analysis  
+- ✅ `docs/research/existing-projects.md` - Performance optimization strategies

### **2.1 Multi-Era Schema Design**
+🚧 **IN PROGRESS** - Core tables drafted in `nba_live/db/ddl/00_create_schema.sql`
```sql
--- Core entities with era-appropriate constraints
+-- ✅ IMPLEMENTED: Core dimensions and facts with DuckDB-optimized design
CREATE TABLE seasons (
    season_id VARCHAR(7) PRIMARY KEY,  -- '1946-47'
    start_year INTEGER,
    end_year INTEGER,
-    league VARCHAR(10),  -- 'NBA', 'BAA', 'ABA'
-    games_played INTEGER,
-    data_quality_score DECIMAL(3,2)
+    era_label TEXT,
+    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-CREATE TABLE teams (
+CREATE TABLE dim_team (
    team_id SERIAL PRIMARY KEY,
-    franchise_id INTEGER,  -- Links relocated teams
-    abbrev VARCHAR(5),
+    abbreviation TEXT NOT NULL,
+    team_name TEXT,
    city VARCHAR(50),
-    name VARCHAR(50),
-    first_season VARCHAR(7),
-    last_season VARCHAR(7),
-    league VARCHAR(10)
+    first_year INTEGER,
+    last_year INTEGER,
+    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **2.2 Database Setup & Migration**
+🚧 **IN PROGRESS** - DuckDB dependency added, core DDL drafted
```bash
# DuckDB initialization (simplified)
make db-init     # Create DuckDB file
make db-migrate  # Run schema DDL from 00_create_schema.sql
make db-seed     # Load lookup tables
make db-test     # Validate constraints
```

### **Deliverables**
-- `db/schema.sql` - Complete DDL with constraints and indexes
-- `db/migrations/` - Versioned schema changes
-- `db/seed_data.sql` - Teams, seasons, stat availability reference data
-- `docs/schema.md` - Documentation with ER diagram
+- ✅ `nba_live/db/ddl/00_create_schema.sql` - Core DDL with DuckDB constraints
+- ✅ `nba_live/etl/kaggle/load_kaggle_players.py` - Sample loader with lineage
+- ⏳ `db/migrations/` - Versioned schema changes (planned)
+- ⏳ `db/seed_data.sql` - Teams, seasons, stat availability reference data
+- ⏳ `docs/schema.md` - Documentation with ER diagram

---

## **Phase 3: Modern Era ETL Pipeline (7 days)**

### **3.0 Research Task: ETL Architecture Patterns (1 day)**
**Study modern ETL/ELT frameworks and patterns:**
- Data pipeline orchestration tools (Airflow, Prefect, Dagster)
- Error handling and retry strategies for web APIs
- Data validation and quality assurance frameworks
- Incremental vs full refresh strategies
- Modern data formats (Parquet, Arrow) vs traditional (CSV, JSON)

**Research Deliverables:**
- `docs/research/etl-patterns.md` - Pipeline architecture analysis
- `docs/research/data-quality-frameworks.md` - Validation strategy comparison

### **3.1 NBA API Integration**
```python
# etl/extractors/nba_api.py
class NBAAPIExtractor:
    def __init__(self):
        self.rate_limiter = RateLimiter(calls=10, period=60)  # 10 calls/minute
        
    def extract_daily_games(self, date: str) -> Dict:
        """Extract all games and stats for a specific date"""
        with self.rate_limiter:
            games = self._get_games(date)
            boxscores = self._get_boxscores(games)
            play_by_play = self._get_play_by_play(games)
            
        # Save raw files with metadata
        raw_data = {
            'games': games,
            'boxscores': boxscores, 
            'play_by_play': play_by_play,
            'metadata': {
                'extraction_date': datetime.now(),
                'source': 'nba_stats_api',
                'version': self.api_version
            }
        }
        
        self._save_raw_file(raw_data, f"data/raw/daily/{date}/nba_api.json")
        return raw_data
```

### **3.2 Data Transformation Pipeline**
```python
# etl/transformers/modern_era.py
class ModernEraTransformer:
    def transform_player_stats(self, raw_boxscore: Dict) -> List[PlayerGameStats]:
        """Transform NBA API data to canonical format"""
        transformed = []
        
        for player_data in raw_boxscore['players']:
            stats = PlayerGameStats(
                # Direct mappings
                points=self._safe_int(player_data.get('PTS')),
                assists=self._safe_int(player_data.get('AST')),
                rebounds=self._safe_int(player_data.get('REB')),
                
                # Modern era specific
                three_pointers_made=self._safe_int(player_data.get('FG3M')),
                minutes_played=self._parse_minutes(player_data.get('MIN')),
                plus_minus=self._safe_int(player_data.get('PLUS_MINUS')),
                
                # Quality metadata
                data_source='nba_api_2025',
                data_quality_score=self._calculate_completeness(player_data)
            )
            
            # Validate against business rules
            self._validate_stats(stats)
            transformed.append(stats)
            
        return transformed
        
    def _calculate_completeness(self, data: Dict) -> float:
        """Calculate data quality score based on field completeness"""
        expected_fields = ['PTS', 'AST', 'REB', 'FGM', 'FGA', 'MIN']
        present_fields = sum(1 for field in expected_fields if data.get(field) is not None)
        return present_fields / len(expected_fields)
```

---
