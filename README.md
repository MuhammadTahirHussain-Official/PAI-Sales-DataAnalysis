# Store Sales Ecuador: data pipeline and interactive website

This repository holds a Streamlit website that presents a complete retail data project, from five raw files to a model-ready table. **You do not need to open any other file to understand the project: this page explains all of it.**

**Live website:** https://pai-sales-eda.streamlit.app/

| Item | Detail |
| --- | --- |
| **Data** | Kaggle "Store Sales – Time Series Forecasting": 54 stores in Ecuador, 33 product families, January 2013 to August 2017 |
| **Size** | 3,000,888 sales rows, one per date, store and product family |
| **Work done** | Merging, EDA before cleaning, cleaning, validation, EDA after cleaning, feature engineering |
| **Result** | A clean table of 38 columns with no missing values, and a model-ready table of 85 features |
| **Not done, on purpose** | No train/test split, scaling or model training. That is the next stage |
| **Built with** | Python 3.12, Streamlit, pandas, Plotly, Pydantic, Parquet, GSAP |

## Contents

1. [Where to look first](#1-where-to-look-first)
2. [The whole system on one page](#2-the-whole-system-on-one-page)
3. [Repository structure](#3-repository-structure)
4. [The data pipeline, stage by stage](#4-the-data-pipeline-stage-by-stage)
5. [What the data showed](#5-what-the-data-showed)
6. [How the website is built](#6-how-the-website-is-built)
7. [Every page: its file and its data](#7-every-page-its-file-and-its-data)
8. [The prepared data files](#8-the-prepared-data-files)
9. [Business rules on the manager pages](#9-business-rules-on-the-manager-pages)
10. [Hosting and keeping the site awake](#10-hosting-and-keeping-the-site-awake)
11. [Running and rebuilding it](#11-running-and-rebuilding-it)
12. [Design decisions and limits](#12-design-decisions-and-limits)

## 1. Where to look first

| If you want to see | Go to |
| --- | --- |
| The project in one view | [Project summary](https://pai-sales-eda.streamlit.app/summary) |
| How the files were joined | [Merging](https://pai-sales-eda.streamlit.app/merging) |
| Every cleaning rule and validation result | [Cleaning](https://pai-sales-eda.streamlit.app/cleaning) |
| The analysis and its charts | [EDA after cleaning](https://pai-sales-eda.streamlit.app/eda-after) |
| Your own chart from the data | [Chart studio](https://pai-sales-eda.streamlit.app/studio) |
| The features for a future model | [Features](https://pai-sales-eda.streamlit.app/features) |
| Conclusions and limits | [Conclusion](https://pai-sales-eda.streamlit.app/conclusion) |
| The results as a store manager would use them | [Choose a store](https://pai-sales-eda.streamlit.app/choose-store) |
| The final clean data | [`downloads/cleaned_data.zip`](downloads/cleaned_data.zip) |
| The analysis code (notebooks) | [Team repository, `notebooks/`](https://github.com/USMANNATT/Stores_Sales_EDA/tree/streamlit-eda-app/notebooks) |

If the site shows a "get this app back up" page, click the button and wait about a minute. Section 10 explains why.

## 2. The whole system on one page

The project has two halves. The **analysis** runs once on the full data, in notebooks. The **website** never touches the full data: it reads small files prepared from the analysis results.

```text
ANALYSIS (run once, in the team repository)

  5 Kaggle CSV files
        |
        v
  Notebook 01: merging  ------>  Notebook 02: EDA before cleaning
        |
        v
  Notebook 03: cleaning and validation  ------>  Notebook 04: EDA after cleaning
        |                     |
        |                     +---------------->  downloads/ (clean CSV as zip files)
        v
  Notebook 05: feature engineering

        |  Kaggle files + outputs of notebooks 01, 03 and 05
        v

PREPARATION (run once, in this repository)

  app/prepare_data.py
        |
        v

WEBSITE (this repository)

  app/data/  (13 MB of Parquet and JSON)
        |
        v
  app/lib/  (shared helpers)  <-- app/views/  (14 pages)  <-- app/streamlit_app.py
                                       |
                                       v
                       Live site on Streamlit Community Cloud
                                       ^
                                       |
                       GitHub Action: a visit every hour
```

Why this split: the full clean table is 555 MB as a CSV, too large to load on a free host for every visitor. The prepared files hold only what the pages need, so the site stays fast. Download links and raw samples are there for anyone who wants the rows themselves.

## 3. Repository structure

```text
.
├── README.md                   This page
├── LICENSE
├── requirements.txt            Exact package versions
├── .streamlit/config.toml      Site colours and fonts
├── .github/workflows/
│   └── keep-awake.yml          Hourly job that visits the live site
├── scripts/
│   └── keep_awake.py           The visit itself, in a headless browser
├── downloads/                  Final clean data
│   ├── cleaned_data.zip        All rows as one CSV (37 MB zip, 555 MB unzipped)
│   └── cleaned_data_2013.zip   One zip per year up to 2017, for Excel users
└── app/
    ├── streamlit_app.py        Entry point: lists the pages and starts the site
    ├── prepare_data.py         Builds app/data from the full data (run once)
    ├── lib/                    Code shared by the pages
    │   ├── data.py             Cached loading of the prepared files
    │   ├── theme.py            Design, menu, step rail, chart and text helpers
    │   ├── glossary.py         56 click-to-read explanations of terms
    │   ├── explain.py          "Why was this day high or low?" for clicked points
    │   └── manager.py          Helpers for the store manager pages
    ├── views/                  One file per page (see section 7)
    ├── static/                 Animated pages and the GSAP library
    │   ├── welcome.html        Landing page animation
    │   ├── journey.html        Project summary animation
    │   ├── gsap.min.js
    │   └── ScrollTrigger.min.js
    └── data/                   Prepared data (see section 8)
        ├── *.parquet           Aggregates, samples and raw reference tables
        ├── summary.json        Facts and validation results shown on the pages
        └── stores/             One file per store, store_1 to store_54
```

The Python code is about 3,800 lines. The raw Kaggle files and intermediate notebook outputs are not stored here: they are large, and the raw data is subject to the Kaggle competition rules.

## 4. The data pipeline, stage by stage

The shape of the data at each stage:

| Stage | Notebook | Rows | Columns | Output |
| --- | --- | --- | --- | --- |
| Raw sales | | 3,000,888 | 6 | `train.csv` |
| Merged | 01 | 3,000,888 | 17 | `train_sales_transactions_oil_holidays_merged.csv` |
| Cleaned | 03 | 3,000,888 | 38 | `preparation_checkpoint.pkl`, `downloads/cleaned_data.zip` |
| Model-ready | 05 | 2,924,262 | 89 (85 features, id, date, 2 targets) | `model_ready_data.pkl`, `feature_columns.txt` |

The notebooks are in the [team repository](https://github.com/USMANNATT/Stores_Sales_EDA/tree/streamlit-eda-app/notebooks).

### 4.1 Raw files

| File | Rows | What it holds | Problem found |
| --- | --- | --- | --- |
| `train.csv` | 3,000,888 | Sales and items on promotion, per date, store and family | None missing |
| `stores.csv` | 54 | City, state, type and cluster of each store | None missing |
| `transactions.csv` | 83,488 | Receipts per store and day | 7,448 store-days have no record |
| `oil.csv` | 1,218 | Daily oil price | 43 values empty, no weekends |
| `holidays_events.csv` | 350 | National, regional and local days | Can match more than one row per day |

### 4.2 Merging (notebook 01)

The sales table stays on the left of every join, so no sales row can be lost. The row count was checked after each join and never changed.

| Step | Joined on | Type | Columns after | Why this key |
| --- | --- | --- | --- | --- |
| `train` | | Starting table | 6 | One row per date, store and family |
| + `stores` | `store_nbr` | Left, many-to-one | 10 | A store's details never change |
| + `transactions` | `date` + `store_nbr` | Left, many-to-one | 11 | Receipts differ per store and per day |
| + `oil` | `date` | Left | 12 | One price per day for all stores |
| + `holidays` | `date` + `store_nbr` | Left, many-to-one | 17 | A holiday may apply only to some stores |

A holiday reaches a store by its scope: national days reach all stores, regional days match the store's state, and local days match its city. Two events on one store-day are combined into one row first, so sales rows are never doubled.

Empty after merging, for cleaning to fix:

| Column | Empty rows | Reason |
| --- | --- | --- |
| Five holiday columns | 2,733,291 each | Most days are not holidays |
| `oil_price` | 928,422 | No trading on weekends and some other days |
| `transactions` | 245,784 | Missing store-day records |

### 4.3 Cleaning (notebook 03)

Every gap is filled by a written rule. Original sales and promotion values are never changed, and no row is deleted.

| Column | Rule | Rows affected |
| --- | --- | --- |
| Duplicates, negatives | Checked: no duplicate keys or ids, no negative sales or promotions | 0 problems |
| `transactions` | Empty on a store-day whose total sales are 0: set to 0 | 241,890 (7,330 store-days) |
| `transactions` | Empty with sales above 0: total sales × median(transactions / sales) of that store and weekday | 3,894 (118 store-days) |
| `oil_price` | Copy the last trading day's price forward, at most 7 days | 926,640 (520 dates) |
| `oil_price` | First date has no earlier price: use the next trading day, flagged | 1,782 (2013-01-01) |
| Holidays | 0/1 flags from the records; transferred-away days and work days are not holidays | 151,734 holiday rows |
| Holiday text | Empty text becomes "No Event" | 2,733,291 per column |
| `sales` | Zeros kept; `sales_log1p` added; values above Q3 + 3×IQR within each store and family are flagged, never removed | 3,373 flagged |
| New columns | Date parts, weekend, payday, category data types | 21 new columns; memory 2.1 GB to 1.1 GB |

Oil is copied forward rather than interpolated because interpolation would use a future price, which a forecast could not know.

### 4.4 Validation (notebooks 03, 04, 05)

Validation works at two levels. All results are real runs stored in `app/data/summary.json`.

**Integrity checks with pandas compare the cleaned table with the merged one. All 11 pass:** same row count, same row order, same dates, stores and families, sales unchanged, promotions unchanged, known transactions unchanged, `transactions_missing` matches the original gaps, known oil prices unchanged, `oil_price_missing` matches the original gaps, no duplicate keys, no missing values.

**Pydantic models check each record's types and ranges. 292,620 records, 0 errors:**

| Model | What it checks | Records checked |
| --- | --- | --- |
| `StoreDayTransactions` | Every store-day: valid store, whole transactions ≥ 0 | 90,936 |
| `OilDay` | Every date: price above 0, not infinite | 1,684 |
| `CleanSalesRow` | Random sample of 3,000,888 cleaned rows, 24 fields | 100,000 |
| `ModelRow` | Random sample of 2,924,262 model-ready rows, 12 fields | 100,000 |

On the [Cleaning page](https://pai-sales-eda.streamlit.app/cleaning) you can re-run validation yourself, try to break it with bad values, and see which check protects each of the 38 columns.

### 4.5 Feature engineering (notebook 05)

The goal is to forecast the next 16 days. **The rule behind every feature: use only what would be known at forecast time.** On the last forecast day the newest known sales are 16 days old, so anything built from sales or receipts looks at least 16 days back.

The first 43 days of data do not have enough history for these features, so 76,626 rows are removed. The table starts on 2013-02-13.

| Group | Features | Count |
| --- | --- | --- |
| Sales history | Lags of 16, 21, 28 and 364 days; rolling means over 7, 14 and 28 days; rolling standard deviation over 7 days; a flag for a missing 364-day lag | 9 |
| Transactions | Receipts 16 days earlier | 1 |
| Promotions | Items on promotion, its log, has a promotion | 3 |
| Oil | Oil price, whether it was filled, its 7-day change | 3 |
| Holidays and events | National, regional, local, event and work-day flags; day before and after a holiday; earthquake period | 9 |
| Calendar | Year, quarter, month, week and day numbers; cyclic month and weekday; days to Christmas; month start and end; weekend; payday; store open | 17 |
| Codes | Store number, and family, city, state and cluster codes | 5 |
| One-hot store type | Types A to E | 5 |
| One-hot family | One column per product family | 33 |
| **Total** | | **85** |

The 33 one-hot family columns explain why 38 cleaned columns become 85 features. Family is stored both ways because linear models need one-hot columns and tree models work well with a single code.

Columns describing the same day, such as `transactions` and `sales_extreme_flag`, are removed because they would leak the answer. Splitting and scaling are left out deliberately: both must use the training period only.

## 5. What the data showed

| Finding | Result | Note |
| --- | --- | --- |
| Rows with zero sales | 31.3% | Real, so kept |
| Weekend lift | +39% | Sunday strongest, Thursday weakest |
| National holidays | +26% | Christmas days lift most; stores close on 1 January |
| Busiest December day | 23 December | In every December of the data |
| Payday effect | +1% | Much smaller than expected at store level |
| Earthquake month | +17% | 16 April to 16 May 2016 against the month before |
| Sales and transactions | 0.84 correlation | Strongest link, on observed days only |
| Best store against weakest | 11 times | Average daily sales in 2015 and 2016 |

## 6. How the website is built

### Starting up

`app/streamlit_app.py` runs first on every interaction. It:

1. Removes old helper modules from memory if a file in `app/lib` changed. Streamlit Cloud pulls new code without restarting, and stale modules used to crash the site.
2. Applies the design with `theme.apply()`.
3. Registers all 14 pages with `st.navigation`, hides Streamlit's own menu and draws a custom one with `theme.top_menu()`.
4. Runs the chosen page from `app/views/`.

```text
Visitor
   |
   v
app/streamlit_app.py
   |
   +--> lib/theme.py        design and menu
   |       +--> lib/glossary.py   term explanations
   |
   +--> views/<page>.py     the chosen page
           +--> lib/data.py and lib/manager.py --> Streamlit cache --> app/data/
           +--> lib/explain.py    explanations of clicked points
           +--> static/*.html     animations
```

### The five helpers

| File | Responsibility | Main parts |
| --- | --- | --- |
| `lib/data.py` | Loads each prepared file once, then keeps it in cache for all visitors | `load()`, `summary()`, `stores()`, `holidays_active()`, column labels |
| `lib/theme.py` | Everything visual, so pages contain only content | CSS, Plotly template, `top_menu()`, `flow_top()`, `flow_next()`, `chart()`, `stats()`, `figcap()`, `glossify()` |
| `lib/glossary.py` | 56 terms, each with what it is, what it does, how it works and an example | `GLOSSARY` |
| `lib/explain.py` | Compares a clicked point with the 7 days around it and lists likely reasons | `explain()`, `context_table()`, `generic_point()` |
| `lib/manager.py` | The store and month controls, and one store's data | `picker()`, `store_rows()`, `store_days()`, `holidays_on()` |

### Interactive features

| Feature | How it works |
| --- | --- |
| Dotted terms | `theme.glossify()` wraps the first use of each known word on the server; a script in the page opens the explanation when clicked |
| Click a point on a chart | Plotly selection returns the point to Python, and `explain.py` builds the explanation |
| Chart studio | Any table, any axes, chart type, aggregation and filters; rows can be ticked by hand |
| Click a product bar | The bar triggers a hidden Streamlit button, which sets the product for the charts below |
| Scroll and cursor animation | GSAP, bundled in `app/static`, so no outside script is needed |
| Live validation | The Cleaning page defines and runs real Pydantic models in the visitor's session |

### Speed

- Each file loads once and is then cached.
- Scatter and distribution charts draw samples of 8,000 to 60,000 points rather than every row.
- Manager pages read only the chosen store's small file.

## 7. Every page: its file and its data

**Start:** [`views/welcome.py`](app/views/welcome.py) with `static/welcome.html`. A full-screen animation of 1,782 particles, one per store and product series, with two ways in. Reads `daily`, `store_day` and `sales_histogram`.

**Technical overview, for analysts.** Meant to be read in order, with a step rail at the top and a next-step link at the bottom of each page.

| Step | Page | File | What it shows | Data used |
| --- | --- | --- | --- | --- |
| Start | Project summary | [`home.py`](app/views/home.py) | All six stages as an animation, plus conclusions | `summary.json`, `daily`, `sales_histogram` |
| 1 | Raw data | [`raw_data.py`](app/views/raw_data.py) | The five files and what each column means | `summary.json`, `raw_*`, `store_day` |
| 2 | Merging | [`merging.py`](app/views/merging.py) | Animated joins, keys, checks, what was empty afterwards | `summary.json` |
| 3 | EDA before cleaning | [`eda_before.py`](app/views/eda_before.py) | Sales spread, products, stores, gaps, oil, holidays | `raw_*`, `family_summary`, `sales_histogram`, `store_day` |
| 4 | Cleaning | [`cleaning.py`](app/views/cleaning.py) | Every rule, integrity checks, Pydantic models, live re-run | `summary.json`, `daily`, `store_day` |
| 5 | EDA after cleaning | [`explore.py`](app/views/explore.py) | About 20 charts: time, holidays, products, stores, promotions, oil, the earthquake | `daily`, `store_day`, `family_day`, `store_family`, `clean_sample` |
| 6 | Chart studio | [`studio.py`](app/views/studio.py) | Build any chart, then download its data | Any prepared table |
| 7 | Features | [`features.py`](app/views/features.py) | The no-leakage rule, feature groups, correlations, encoding | `features`, `summary.json` |
| 8 | Conclusion | [`conclusion.py`](app/views/conclusion.py) | Findings, work done, limits, next step | `summary.json` |

**Business overview, for store managers.** Plain language, one store at a time.

| Page | File | What it shows | Data used |
| --- | --- | --- | --- |
| Choose a store | [`mgr_stores.py`](app/views/mgr_stores.py) | All 54 stores, with filters and sorting | `store_day`, `raw_stores` |
| Store overview | [`mgr_dashboard.py`](app/views/mgr_dashboard.py) | Key numbers, all products, day-by-day line, monthly goal, best weekdays, products to watch, Excel order list | `stores/store_N`, `store_day` |
| Product calendar | [`mgr_products.py`](app/views/mgr_products.py) | Colour calendar for one product; click a day to see why it was high or low | `stores/store_N`, `store_day`, `raw_holidays` |
| Insights and actions | [`mgr_insights.py`](app/views/mgr_insights.py) | Next actions, promotion results, special days, unusual days, comparison with other stores | `stores/store_N`, `store_day`, `raw_stores` |

## 8. The prepared data files

`app/prepare_data.py` builds everything in `app/data/`. All numbers on the site come from these files.

| File | Rows × columns | One row is | Used for |
| --- | --- | --- | --- |
| `summary.json` | | | Facts, merge steps, integrity and Pydantic results, column coverage |
| `daily.parquet` | 1,684 × 19 | One date, all stores | Time series, oil, summary |
| `store_day.parquet` | 90,936 × 28 | One store on one date | Store comparisons, gaps, manager pages |
| `family_day.parquet` | 55,572 × 6 | One family on one date | Product trends |
| `family_summary.parquet` | 33 × 7 | One family | Product rankings |
| `store_family.parquet` | 1,782 × 7 | One store and family | Store and product heatmaps |
| `stores/store_N.parquet` | About 55,572 × 4 each | One family on one date, for one store | Manager pages |
| `clean_sample.parquet` | 150,000 × 14 | Random cleaned row | Distributions |
| `raw_train_sample.parquet` | 150,000 × 6 | Random raw row | EDA before cleaning |
| `sales_histogram.parquet` | 61 × 3 | One bar, exact counts from all rows | Sales distribution |
| `features.parquet` | 85 × 3 | One feature, its group and correlation with sales | Features page |
| `raw_stores`, `raw_oil`, `raw_holidays` | 54, 1,218 and 350 rows | Original rows | Raw data page, holiday reasons |

The numbers on the site are exact wherever they come from aggregates. Only the two samples are partial, and they are used where a chart needs individual rows.

## 9. Business rules on the manager pages

These are the rules behind the advice, so nothing on those pages is unexplained.

| Item | Rule |
| --- | --- |
| Monthly goal | 8% above the same month last year |
| Bar colours | Blue: biggest rise. Green: other rises or no change. Orange: other falls. Red: biggest fall. Grey: no sales last month |
| Change | Units per day against last month |
| Products to watch | Products with at least 30 units this month, ranked by change |
| Expected next month | Units per day × (1 + change, limited to ±25%) × 30 |
| Suggested order | Expected next month + 10% safety stock. **The data has no stock counts, so stock on hand is not subtracted** |
| Day rating | Against the month's average day. Very high: 1.3 times or more. High: 1.1. Normal: 0.9. Low: 0.7. Very low: below 0.7 |
| Reasons for a day | Weekday effect, payday (15th and month end), holidays that apply to that store, promotions, whole store closed, earthquake period |
| Promotion comparison | Last 12 months; a product needs at least 10 days each with and without promotion |
| Unusual days | Outside Q1 − 1.5×IQR and Q3 + 1.5×IQR of that month's daily sales |

These rules are simple descriptive suggestions, not forecasts from a trained model.

## 10. Hosting and keeping the site awake

The site runs on Streamlit Community Cloud, which redeploys automatically when `main` changes.

Free apps go to sleep after a period without visitors, so [`.github/workflows/keep-awake.yml`](.github/workflows/keep-awake.yml) schedules a visit every hour. [`scripts/keep_awake.py`](scripts/keep_awake.py) opens the site in a real headless browser, because a plain web request does not count as a visit. It clicks the wake-up button if needed and confirms the page has loaded.

GitHub does not guarantee scheduled times: runs can start late or be skipped. Running hourly leaves plenty of margin. The job also makes a small commit after 45 quiet days, because GitHub turns off schedules in repositories with no activity for 60 days. It needs the repository variable `APP_URL`, which is already set.

## 11. Running and rebuilding it

**Run the website locally.** Everything it needs is in this repository:

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

**Rebuild `app/data`.** This is only needed if the analysis changes. It requires the Kaggle CSV files and the notebook outputs listed in section 4, which are not stored here:

```bash
STORE_FILES=/path/to/files python app/prepare_data.py
```

**Deploy your own copy.** On share.streamlit.io choose Create app, then this repository, branch `main`, main file `app/streamlit_app.py` and Python 3.12.

**Use the clean data.** [`downloads/cleaned_data.zip`](downloads/cleaned_data.zip) has all 3,000,888 rows and 38 columns. Excel stops at about 1 million rows, so `cleaned_data_2013.zip` to `cleaned_data_2017.zip` hold one year each.

## 12. Design decisions and limits

| Decision | Reason |
| --- | --- |
| Prepared Parquet files, no database | The data never changes after preparation, so a server would add cost and nothing else |
| Separate technical and business areas | Analysts need method and proof; managers need plain answers |
| Keep zeros and flag extremes | 31.3% zeros and the very high days are real behaviour, not errors |
| Copy oil forward, no interpolation | Interpolation would use future prices |
| Two validation levels | Pydantic checks each record; pandas checks that cleaning did not damage the original values |
| No train/test split yet | Splitting and scaling belong to the modelling stage and must use the training period only |

**Known limits**

- Transactions on 118 store-days are estimated from sales, so those days cannot prove the link between sales and transactions.
- A store-day with no sales and no record is set to 0 transactions. That is an assumption, not proof the store was closed.
- The data has no stock counts, prices or profit, so order suggestions cannot subtract stock and "sales" means units sold.
- Percentage changes on very small products can look huge. For example, +190% can mean only 3 units.
- This repository has no automated test suite. Checks are the validation results described in section 4.4.

**Fonts and motion:** Bricolage Grotesque, Hanken Grotesk and JetBrains Mono. Animation uses GSAP 3.13 under its standard license, and respects reduced-motion settings. The source data belongs to the Kaggle competition and is subject to its rules.
