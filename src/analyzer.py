"""CostAnalyzer: loads a cloud billing CSV, validates it, and computes
real cost statistics (totals, per-service/region breakdowns, daily
anomaly detection, 30-day forecast).

Accepted CSV schema (headers required, extras allowed):
    date    - parseable date (e.g. 2023-10-01, 01/10/2023)
    service - cloud service name (non-empty string)
    cost    - numeric, >= 0 (USD)

Optional column:
    region  - cloud region (if present, per-region breakdown is produced)
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from src.errors import InputError, ValidationError

REQUIRED_COLUMNS = ("date", "service", "cost")
OPTIONAL_COLUMNS = ("region",)
MAX_ROWS = 1_000_000


def _load_csv(path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        raise InputError(f"input file not found: '{path}'")
    except PermissionError:
        raise InputError(f"permission denied reading input file: '{path}'")
    except pd.errors.EmptyDataError:
        raise ValidationError(f"input file is empty: '{path}'")
    except Exception:
        raise InputError(f"could not read input file as CSV: '{path}'")
    return df


def _validate(df: pd.DataFrame, path: str) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValidationError(
            f"'{path}': missing required column(s): {', '.join(missing)}. "
            f"CSV must have headers: {', '.join(REQUIRED_COLUMNS)} "
            f"(optional: {', '.join(OPTIONAL_COLUMNS)})."
        )
    if df.empty:
        raise ValidationError(f"'{path}': CSV has headers but no data rows.")
    if len(df) > MAX_ROWS:
        raise ValidationError(
            f"'{path}': {len(df)} rows exceeds the {MAX_ROWS:,} row limit."
        )

    # --- date ---
    try:
        df["date"] = pd.to_datetime(df["date"], errors="raise")
    except Exception:
        raise ValidationError(
            f"'{path}': column 'date' contains unparseable dates "
            f"(use YYYY-MM-DD or a common date format)."
        )
    if df["date"].isna().any():
        raise ValidationError(f"'{path}': column 'date' has missing values.")

    # --- service ---
    df["service"] = df["service"].astype(str).str.strip()
    if (df["service"] == "").any() or (df["service"].str.lower() == "nan").any():
        raise ValidationError(f"'{path}': column 'service' has missing values.")

    # --- cost ---
    df["cost"] = pd.to_numeric(df["cost"], errors="coerce")
    if df["cost"].isna().any():
        raise ValidationError(
            f"'{path}': column 'cost' must be numeric (found non-numeric values)."
        )
    if (df["cost"] < 0).any():
        raise ValidationError(
            f"'{path}': column 'cost' must be >= 0 (found negative values)."
        )
    if not np.isfinite(df["cost"]).all():
        raise ValidationError(
            f"'{path}': column 'cost' contains infinite values."
        )

    # --- region (optional) ---
    if "region" in df.columns:
        df["region"] = df["region"].astype(str).str.strip().replace(
            {"nan": "", "None": ""}
        )
    else:
        df["region"] = ""

    return df


class CostAnalyzer:
    def __init__(self, data_path: str):
        df = _load_csv(data_path)
        self.df = _validate(df, data_path)
        self.data_path = data_path

    # ---------------- core metrics ----------------

    def get_total_spend(self) -> float:
        return float(self.df["cost"].sum())

    def get_spend_by_service(self) -> pd.DataFrame:
        return (
            self.df.groupby("service", as_index=False)["cost"]
            .sum()
            .sort_values("cost", ascending=False)
            .reset_index(drop=True)
        )

    def get_spend_by_region(self) -> pd.DataFrame:
        regions = self.df[self.df["region"] != ""]
        if regions.empty:
            return pd.DataFrame(columns=["region", "cost"])
        return (
            regions.groupby("region", as_index=False)["cost"]
            .sum()
            .sort_values("cost", ascending=False)
            .reset_index(drop=True)
        )

    def get_daily_spend(self) -> pd.DataFrame:
        return (
            self.df.groupby("date", as_index=False)["cost"]
            .sum()
            .sort_values("date")
            .reset_index(drop=True)
        )

    def detect_anomalies(self, threshold_std: float = 2.0) -> pd.DataFrame:
        """Days where daily spend > mean + threshold_std * std."""
        if threshold_std <= 0:
            raise ValidationError("--threshold must be a positive number.")
        daily = self.get_daily_spend()
        if len(daily) < 3:
            return daily.iloc[0:0]  # not enough data for std
        mean = daily["cost"].mean()
        std = daily["cost"].std()
        limit = mean + threshold_std * std
        out = daily[daily["cost"] > limit].copy()
        out["deviation"] = out["cost"] - mean
        return out.reset_index(drop=True)

    def forecast_spend_next_month(self) -> float:
        """Next-30-day projection = daily average * 30 (linear, no ML claims)."""
        return float(self.get_daily_spend()["cost"].mean() * 30)

    # ---------------- report payload ----------------

    def summary(self, threshold_std: float = 2.0, top_n: int = 5) -> dict:
        by_service = self.get_spend_by_service()
        by_region = self.get_spend_by_region()
        anomalies = self.detect_anomalies(threshold_std)
        daily = self.get_daily_spend()
        total = self.get_total_spend()
        return {
            "total_spend": total,
            "row_count": int(len(self.df)),
            "date_from": str(daily["date"].min().date()),
            "date_to": str(daily["date"].max().date()),
            "days_covered": int(len(daily)),
            "top_services": [
                {"service": r["service"], "cost": float(r["cost"]),
                 "share": float(r["cost"] / total) if total else 0.0}
                for r in by_service.head(top_n).to_dict("records")
            ],
            "top_regions": [
                {"region": r["region"], "cost": float(r["cost"])}
                for r in by_region.head(top_n).to_dict("records")
            ],
            "anomalies": [
                {"date": str(r["date"].date()), "cost": float(r["cost"]),
                 "deviation": float(r["deviation"])}
                for r in anomalies.to_dict("records")
            ],
            "anomaly_threshold_std": threshold_std,
            "forecast_30d": self.forecast_spend_next_month(),
            "daily_avg": float(daily["cost"].mean()),
        }
