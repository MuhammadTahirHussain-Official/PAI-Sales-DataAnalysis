# Store Sales EDA — interactive website

An interactive Streamlit report on the Kaggle **Store Sales – Time Series Forecasting** data (54 stores in Ecuador, 33 product families, 2013 – 2017, 3,000,888 rows). It walks through the raw files, the ETL and cleaning, the data validation, the exploratory analysis and the model-ready features.

## What is in it

**Welcome page.** A full-screen GSAP landing page with two ways in. 1,782 particles, one per store and product series, react to the cursor and reshape into real charts while you scroll.

**Project summary (first step for technical users).** The whole project in one view: a GSAP animation of the six steps (raw data, merging, EDA before cleaning, cleaning, EDA after cleaning, conclusion) drawn from real numbers, plus the conclusions and links to both dashboards.

**Technical overview**, for analysts. It opens with the project summary, then runs in order, with a step rail at the top and a link to the next step at the bottom of each page:

| Step | Page | What it shows |
| --- | --- | --- |
| 1 | Raw data | The five files: facts, and what every column means |
| 2 | Merging | Animated joins, which file is merged on which column and why, checks, what was empty afterwards |
| 3 | EDA before cleaning | Sales distribution, products, stores, gaps in transactions, oil and holidays |
| 4 | Cleaning | Every rule and the rows it touched, then 11 integrity checks, four Pydantic models, coverage matrix, live re-run and "try to break it" |
| 5 | EDA after cleaning | 20 charts on one page; click a point on the time series for a summary of that day and likely reasons |
| 6 | Chart studio | Any table, any x, y and colour, chart type, aggregation, log axes, trend line, filters |
| 7 | Features | The no-leakage rule, feature groups, correlation with the target, encoding |
| 8 | Conclusion | Findings, what was done, limits, next step, download of the clean data |

**Business overview**, for store managers and other non-technical users. It uses the structure of the team's manager prototype with real data. You first choose one of the 54 stores, then see only that store:

| Page | What it shows |
| --- | --- |
| Choose a store | All 54 stores, with city and type filters and sorting |
| Store overview | One-sentence summary, key numbers, all 33 products (click one to drill down), day-by-day line, monthly goal (8% above last year), best weekdays, products to watch, Excel order list |
| Product calendar | Colour calendar for one product; click a day to see why it was high or low and what to do |
| Insights and actions | Prioritised next actions, promotion lift, holidays, weekends and payday, unusual days, comparison with region and chain averages |

**Plain language.** Dotted words anywhere on the site open a short explanation when clicked: what it is, what it does, how it works and an example (`app/lib/glossary.py`). The chart studio has filters for dates, stores, places, products, kinds of day and number ranges, and rows can also be ticked by hand.

Suggested orders exclude stock on hand because the data has no stock counts. Motion uses GSAP 3.13 (bundled in `app/static`, standard GSAP license).

## Download the final clean data

[`downloads/cleaned_data.zip`](downloads/cleaned_data.zip) holds the complete cleaned table as one CSV: 3,000,888 rows, 38 columns, no missing values. Excel stops at about 1 million rows, so `downloads/cleaned_data_2013.zip` to `cleaned_data_2017.zip` hold one year each. The same links are on the website.

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

The app reads only `app/data/` (about 12 MB): daily, store-day, family-day and store-family aggregates, one small daily file per store for the manager pages, the stores/oil/holiday tables, two 150,000-row random samples, real Pydantic validation results and feature correlations. These were produced by `app/prepare_data.py` from the original Kaggle CSVs and the outputs of the cleaning and feature-engineering notebooks of the analysis project, which are not included here. The source data belongs to the Kaggle competition and is subject to its rules.

## Design

Bricolage Grotesque, Hanken Grotesk and JetBrains Mono on charcoal glass panels with one ember accent. Every panel keeps clear space around it. Motion respects reduced-motion settings.
