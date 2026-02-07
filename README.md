# Cloud FinOps Cost Analyzer

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB.svg)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.1-150458.svg)](https://pandas.pydata.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A **production-grade FinOps tool** for analyzing and optimizing multi-cloud infrastructure costs. This repository provides a Python-based engine to ingest billing data, identify cost spikes, and recommend resource rightsizing.

## 🚀 Features

- **Multi-Cloud Support**: Normalized data ingestion from AWS, Azure, and GCP billing exports (CSV).
- **Cost Allocation**: Tag-based cost attribution to teams, projects, or cost centers.
- **Anomaly Detection**: Statistical identification of spending spikes using rolling averages.
- **Forecasting**: Simple linear projection of future spend based on historical trends.
- **Reporting**: Automated generation of cost summary reports.

## 📁 Project Structure

```
cloud-finops-cost-analyzer/
├── src/
│   ├── analyzer.py       # Core analysis logic
│   └── main.py           # CLI Entrypoint
├── data/                 # Sample billing data
│   └── sample_costs.csv
├── tests/
├── requirements.txt
└── Dockerfile
```

## 🛠️ Quick Start

```bash
# Clone
git clone https://github.com/Shivay00001/cloud-finops-cost-analyzer.git

# Install
pip install -r requirements.txt

# Run Analysis
python src/main.py --file data/sample_costs.csv
```

## 📄 License

MIT License
