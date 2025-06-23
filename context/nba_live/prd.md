# Product Requirements Document (PRD)

> _Status: Draft_

## 1. Vision

Build a comprehensive, locally hosted NBA statistics archive (1946-present) with a transparent data-confidence model, enabling researchers, bettors, and fans to query historical and real-time data with ease.

## 2. Personas & Needs

| Persona | Key Needs |
|---------|-----------|
| Researcher | Clean export, data confidence indicators, reproducible versions |
| Sports Bettor | Real-time updates, injury/lineup changes, odds history |
| Casual Fan | Simple stats lookup, leaderboard comparisons |

## 3. Features (MVP)

1. Multi-era ETL with provenance tracking
2. DuckDB backend with columnar analytics
3. Data completeness dashboard
4. Nightly automated refresh (ETL pipeline)

## 4. Success Metrics

* >95% completeness for 1997-present seasons (modern era)
* Data Confidence Score published per stat per season
* Pipeline fails <1% of nightly runs over 30-day window
* Star schema supports sub-200ms analytical queries

## 5. Out of Scope (MVP)

* Live in-game ingestion
* AI/LLM conversational agent (future enhancement)
* Real-time betting line integration

## 6. Open Questions

* Vector storage approach: DuckDB extension vs external store?
* Audit history strategy: per-table versioning vs lineage-only?
* Performance optimization: season-based partitioning approach? 