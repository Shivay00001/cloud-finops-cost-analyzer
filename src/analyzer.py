import pandas as pd
import numpy as np

class CostAnalyzer:
    def __init__(self, data_path: str):
        self.df = pd.read_csv(data_path)
        self.df['date'] = pd.to_datetime(self.df['date'])

    def get_total_spend(self) -> float:
        """Returns the total spend in the dataset."""
        return self.df['cost'].sum()

    def get_spend_by_service(self) -> pd.DataFrame:
        """Groups spend by cloud service."""
        return self.df.groupby('service')['cost'].sum().sort_values(ascending=False).reset_index()

    def detect_anomalies(self, threshold_std: float = 2.0) -> pd.DataFrame:
        """
        Detects daily spending anomalies based on standard deviation.
        Returns days where spend is > mean + threshold * std.
        """
        daily_spend = self.df.groupby('date')['cost'].sum().reset_index()
        mean_spend = daily_spend['cost'].mean()
        std_spend = daily_spend['cost'].std()
        
        limit = mean_spend + (threshold_std * std_spend)
        anomalies = daily_spend[daily_spend['cost'] > limit]
        
        return anomalies

    def forecast_spend_next_month(self) -> float:
        """Simple linear extrapolation for next 30 days based on daily average."""
        daily_avg = self.df.groupby('date')['cost'].sum().mean()
        return daily_avg * 30
