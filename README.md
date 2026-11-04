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

## Always awake

Streamlit Community Cloud puts apps to sleep after hours without visitors. The workflow `.github/workflows/keep-awake.yml` opens the site in a headless browser every 3 hours (`scripts/keep_awake.py`), clicks the wake-up button if the app ever fell asleep, and confirms the page loads. It also makes a small heartbeat commit after 45 quiet days, because GitHub stops scheduled workflows in repositories without activity for 60 days.

One-time setup after deploying: repository Settings → Secrets and variables → Actions → Variables → add `APP_URL` with the app address (for example `https://stores-sales-eda.streamlit.app`). Then Actions → "Keep the Streamlit app awake" → Run workflow to check it once.

## Data

The app reads only `app/data/` (about 5 MB): daily, store-day, family-day and store-family aggregates, the stores/oil/holiday tables, two 150,000-row random samples, real Pydantic validation results and feature correlations. These were produced by `app/prepare_data.py` from the original Kaggle CSVs and the outputs of the cleaning and feature-engineering notebooks of the analysis project, which are not included here. The source data belongs to the Kaggle competition and is subject to its rules.

## Design

Instrument Serif, Geist and Geist Mono on a paper-toned palette. Motion is CSS only and respects reduced-motion settings.
