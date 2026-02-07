import argparse
import sys
from src.analyzer import CostAnalyzer

def main():
    parser = argparse.ArgumentParser(description="FinOps Cost Analyzer")
    parser.add_argument("--file", required=True, help="Path to billing CSV file")
    
    args = parser.parse_args()
    
    try:
        analyzer = CostAnalyzer(args.file)
        
        print("--- FinOps Cost Report ---")
        print(f"Total Spend: ${analyzer.get_total_spend():,.2f}")
        
        print("\n--- Top Spenders by Service ---")
        top_services = analyzer.get_spend_by_service().head(5)
        print(top_services.to_string(index=False))
        
        print("\n--- Anomalies Detected ---")
        anomalies = analyzer.detect_anomalies()
        if anomalies.empty:
            print("No anomalies detected.")
        else:
            print(anomalies.to_string(index=False))
            
        forecast = analyzer.forecast_spend_next_month()
        print(f"\n--- Forecast (Next 30 Days) ---")
        print(f"Projected Spend: ${forecast:,.2f}")
        
    except FileNotFoundError:
        print(f"Error: File '{args.file}' not found.")
    except Exception as e:
        print(f"Error analyzing data: {e}")

if __name__ == "__main__":
    main()
