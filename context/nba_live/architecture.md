# Architecture Overview

> _Status: Draft_

## 1. High-Level Diagram

TBD – insert C4 Level 1 system context diagram.

## 2. Components

| Component | Description |
|-----------|-------------|
| ETL Pipeline | Orchestrates data download, transform, and load from Kaggle & live APIs. |
| DuckDB (star schema) | Columnar analytics store with Parquet backing. |
| Audit Layer | Change-data capture tables recording every source write. |
| DuckDB \+ pgvector | Stores relational data and embeddings. |
| DuckDB \+ pgvector* | Stores analytics tables and optional vector embeddings.* |
| *Note* | Vector storage approach (DuckDB extension vs external) is under evaluation. |
| AI Service | LangChain-powered FastAPI for queries. |

## 3. Data Flow

1. Sources → ETL Download
2. Raw → Transform → Load into DuckDB
3. Text generation → Embedding → DuckDB pgvector index
4. Client → API → Retrieval + LLM → Response

## 4. Non-Functional Requirements

* Scalability: ingest nightly updates < 5 minutes.
* Reliability: pipeline retry strategy; database backups.
* Security: .env secrets, least-privileged DB user.

## 5. Open Questions

* Should we include real-time play-by-play via websockets?
* Which vector index (IVFFlat vs HNSW) performs best on our corpus? 