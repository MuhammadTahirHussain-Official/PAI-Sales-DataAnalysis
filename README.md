# Store Sales EDA — interactive website

An interactive Streamlit report on the Kaggle **Store Sales – Time Series Forecasting** data (54 stores in Ecuador, 33 product families, 2013 – 2017, 3,000,888 rows). It walks through the raw files, the ETL and cleaning, the data validation, the exploratory analysis and the model-ready features.

## Pages

| Page | What it shows |
| --- | --- |
| Overview | Animated sales line and counters, what one row means, the five source files, key findings |
| The raw data | One view per CSV before cleaning: column dictionary, facts and interactive charts |
| ETL & cleaning | Animated join pipeline, join checks, missing values before/after, the cleaning ledger |
| Validation | 11 integrity checks, four Pydantic models with rules and results, coverage matrix, live re-run, "try to break it" |
| Explore sales | Ten chapters: time series with click-to-explain, weekly/yearly rhythm, holidays, families, stores, promotions, oil, earthquake, distributions, correlations |
| Chart studio | Any table, any x/y/colour, chart type, aggregation, log axes, trend line and filters |
| Features | The no-leakage rule, feature groups, correlation with the target, encoding |

Every chart shows exact values on hover and has a caption underneath. Clicking a point on the time series opens a summary of that day: how it compares with the days around it and the likely reasons (holidays and events, weekday, closed stores, promotions, transactions, oil, payday, earthquake).

## Run locally

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

## Deploy on Streamlit Community Cloud

share.streamlit.io → Create app → this repository, branch `main`, main file `app/streamlit_app.py`, Python 3.12. Pick a custom subdomain under App settings.

## Data

The app reads only `app/data/` (about 5 MB): daily, store-day, family-day and store-family aggregates, the stores/oil/holiday tables, two 150,000-row random samples, real Pydantic validation results and feature correlations. These were produced by `app/prepare_data.py` from the original Kaggle CSVs and the outputs of the cleaning and feature-engineering notebooks of the analysis project, which are not included here. The source data belongs to the Kaggle competition and is subject to its rules.

## Design

Instrument Serif, Geist and Geist Mono on a paper-toned palette. Motion is CSS only and respects reduced-motion settings.
