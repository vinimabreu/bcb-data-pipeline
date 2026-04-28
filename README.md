# BCB Data Pipeline

Automated daily pipeline that pulls Brazilian macroeconomic indicators from the [Banco Central do Brasil SGS API](https://www3.bcb.gov.br/sgspub/), normalizes them into a long-format dataset, and publishes the output as Parquet (full history) and CSV (latest snapshot) — refreshed every morning by GitHub Actions.

## Indicators tracked

| Series | Code | Frequency | Unit |
|---|---|---|---|
| Selic meta (target rate) | 432 | daily | % a.a. |
| Selic Over (daily rate) | 11 | daily | % a.d. |
| IPCA monthly | 433 | monthly | % a.m. |
| IPCA accumulated 12 months | 13522 | monthly | % a.a. |
| USD/BRL PTAX (buy) | 1 | daily | R$ |
| EUR/BRL PTAX (buy) | 21619 | daily | R$ |

Default window: from January 1, 2018 to today. The window is bounded because the BCB API rejects unbounded queries on long-running daily series.

## Architecture

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ BCB SGS public   │     │ pipeline.py      │     │ data/            │
│ API (HTTPS, no   │ --> │ requests +       │ --> │ series.parquet   │
│ auth required)   │     │ pandas +         │     │ latest.csv       │
└──────────────────┘     │ pyarrow          │     └──────────────────┘
                         └──────────────────┘              ▲
                                  ▲                        │
                                  │                        │ commit
                         ┌──────────────────┐              │
                         │ GitHub Actions   │ ─────────────┘
                         │ cron: 12:00 UTC  │
                         │ daily            │
                         └──────────────────┘
```

## Quick start

```bash
# Clone
git clone https://github.com/vinimabreu/bcb-data-pipeline.git
cd bcb-data-pipeline

# Set up virtualenv
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# Install
pip install -r requirements.txt

# Run
python pipeline.py
```

## CLI options

```bash
python pipeline.py                                   # default: 01/01/2018 -> today
python pipeline.py --start 01/01/2020                # custom start date
python pipeline.py --start 01/01/2024 --end 31/12/2024  # explicit window
```

Date format is `DD/MM/YYYY` (the format the BCB API expects).

## Output

**`data/series.parquet`** — long-format history of all configured series.

| Column | Type | Description |
|---|---|---|
| date | datetime | Observation date |
| value | float | Observation value |
| series_id | string | Slug from `config.py` (e.g. `selic_meta`) |
| series_name | string | Human-readable name |
| unit | string | Original unit (e.g. `% a.a.`, `R$`) |
| frequency | string | `daily` or `monthly` |

**`data/latest.csv`** — most recent value per series, suitable for dashboards or Slack snapshots.

## Adding a new indicator

1. Look up the series code on https://www3.bcb.gov.br/sgspub/.
2. Add an entry to `SERIES` in [config.py](config.py).
3. Re-run `python pipeline.py`.

The pipeline is idempotent: re-running over the same window simply rewrites the Parquet with the latest data. New series are picked up automatically on the next run.

## Scheduling

The included GitHub Actions workflow (`.github/workflows/daily-pipeline.yml`) runs the pipeline once a day at 12:00 UTC and commits any new data back to the `main` branch. To enable it on your fork, just push the workflow file — no extra secrets required, since the BCB API is public.

You can also trigger a run manually from the **Actions** tab via "Run workflow".

## Stack

- **Python 3.12**
- **requests** for the HTTP layer
- **pandas + pyarrow** for normalization and Parquet output
- **GitHub Actions** for scheduling

## Author

Vinicius Pereira
