"""Brazilian Central Bank (BCB) SGS data pipeline.

Fetches macroeconomic indicators from the BCB SGS public API,
normalizes them into a long-format DataFrame, and persists to
Parquet (full history) plus CSV (latest snapshot).
"""

import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from config import DEFAULT_START_DATE, SERIES

DATA_DIR = Path(__file__).parent / "data"
HISTORY_PARQUET = DATA_DIR / "series.parquet"
LATEST_CSV = DATA_DIR / "latest.csv"

API_URL = (
    "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"
    "?formato=json&dataInicial={start}&dataFinal={end}"
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("bcb-pipeline")


def fetch_series(code: int, start: str, end: str, timeout: int = 60) -> pd.DataFrame:
    """Fetch a single series by code from the BCB SGS API.

    Date strings must be in DD/MM/YYYY format (the BCB convention).
    """
    url = API_URL.format(code=code, start=start, end=end)
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    raw = response.json()
    if not raw:
        return pd.DataFrame(columns=["date", "value"])
    df = pd.DataFrame(raw)
    df["date"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    df["value"] = pd.to_numeric(df["valor"], errors="coerce")
    return df[["date", "value"]]


def fetch_all(series_config: dict, start: str, end: str) -> pd.DataFrame:
    """Fetch every configured series and combine into long format."""
    frames = []
    for slug, meta in series_config.items():
        logger.info(f"Fetching {slug} (code={meta['code']})...")
        try:
            df = fetch_series(meta["code"], start=start, end=end)
        except requests.RequestException as e:
            logger.error(f"  Failed to fetch {slug}: {e}")
            continue
        df["series_id"] = slug
        df["series_name"] = meta["name"]
        df["unit"] = meta["unit"]
        df["frequency"] = meta["frequency"]
        logger.info(f"  Got {len(df):,} rows")
        frames.append(df)

    if not frames:
        return pd.DataFrame(
            columns=["date", "value", "series_id", "series_name", "unit", "frequency"]
        )
    return pd.concat(frames, ignore_index=True)


def make_latest_snapshot(history: pd.DataFrame) -> pd.DataFrame:
    """For each series, return only the most recent value."""
    return (
        history.sort_values(["series_id", "date"])
        .groupby("series_id", as_index=False)
        .tail(1)
        .reset_index(drop=True)
        .sort_values("series_id")
    )


def run(start: str, end: str | None = None) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    end = end or datetime.now().strftime("%d/%m/%Y")
    logger.info(
        f"Pipeline run started at {datetime.now(timezone.utc).isoformat()} "
        f"(window {start} -> {end})"
    )

    history = fetch_all(SERIES, start=start, end=end)
    if history.empty:
        logger.error("No data fetched. Exiting without writing files.")
        return

    history = history.sort_values(["series_id", "date"]).reset_index(drop=True)
    history.to_parquet(HISTORY_PARQUET, index=False)

    latest = make_latest_snapshot(history)
    latest.to_csv(LATEST_CSV, index=False)

    logger.info(
        f"Wrote {len(history):,} rows to {HISTORY_PARQUET.name} "
        f"and {len(latest)} rows to {LATEST_CSV.name}"
    )
    logger.info("Latest values:")
    for _, row in latest.iterrows():
        logger.info(
            f"  {row['series_name']:30s} {row['value']:>10.4f} {row['unit']:8s} "
            f"({row['date'].strftime('%Y-%m-%d')})"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch BCB SGS series and persist as Parquet + CSV")
    parser.add_argument(
        "--start",
        default=DEFAULT_START_DATE,
        help=f"Start date in DD/MM/YYYY format (default: {DEFAULT_START_DATE})",
    )
    parser.add_argument(
        "--end",
        default=None,
        help="End date in DD/MM/YYYY format (default: today)",
    )
    args = parser.parse_args()
    run(start=args.start, end=args.end)
