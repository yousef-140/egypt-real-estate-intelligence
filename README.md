# Egypt Real Estate Intelligence

A self-built big data pipeline and market intelligence platform for the Egyptian real estate market, using self-collected data (not a public dataset). Built as a hands-on data engineering + ML learning project, covering the full lifecycle from ingestion to a live analytics dashboard.

**Current scope:** Greater Cairo (Cairo + Giza), residential apartments, sale & rent.
**Roadmap:** expand geographic coverage to other Egyptian cities.

## Architecture

```
Scraper (Python)  →  HDFS Bronze  →  Spark (Silver cleaning)  →  Spark (Gold aggregation)
       ↓                                                              ↓
   Airflow DAG (daily orchestration)                     ML Pipeline (Random Forest)
                                                                       ↓
                                                            Streamlit Dashboard
```

- **Ingestion:** Python scraper (`requests` + `BeautifulSoup`), orchestrated daily via Airflow
- **Storage:** HDFS data lake with Bronze / Silver / Gold layers
- **Processing:** Apache Spark (PySpark) for cleaning, deduplication, and feature engineering
- **Orchestration:** Apache Airflow (Docker Compose stack: Airflow, Postgres, Spark, Hadoop)
- **ML:** Spark MLlib — Random Forest Regressor for price prediction + a "Fair Value Score" that flags under/overpriced listings
- **Dashboard:** Streamlit, reading from exported Gold-layer data

## What's built

- **Bronze layer:** raw daily scrapes, date-partitioned
- **Silver layer:** cleaned listings — numeric parsing, missing-value imputation (size-bin based), area/location extraction from listing URLs, language detection, deduplication by listing ID
- **Gold layer:**
  - Market overview per area (listing count, average price, average price/m²)
  - Rental yield per area (estimated annual return from sale price vs. average rent)
  - Fair Value Score per listing (actual price vs. ML-predicted price)
- **ML model:** Random Forest Regressor (PySpark MLlib), tuned via cross-validation, features include size, bedrooms, bathrooms, area (one-hot encoded), and compound name (for frequently-listed compounds). R² ≈ 0.59 on held-out test data.
- **Dashboard:** 3-page Streamlit app — Market Overview, Deal Finder (Fair Value Score explorer), Rental Yield by area

## Known limitations (documented honestly)

- Dataset size is still moderate (~4,000 unique listings as of this writing); model accuracy will improve as the daily pipeline accumulates more data
- No property condition/finish-level, floor, or view data available from the source — these are known missing signals that cap predictive accuracy
- Geographic coverage currently limited to Greater Cairo

## Tech stack

Python, PySpark, Apache Airflow, Hadoop (HDFS), Docker Compose, Streamlit, pandas

## Status

Actively maintained. Next steps: expanding geographic coverage, interactive prediction page, further model refinement.
