"""pytest suite for the FinOps cost analyzer."""
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analyzer import CostAnalyzer
from src.errors import InputError, ValidationError
from src.report import render

SAMPLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "data", "sample_costs.csv")


def _csv(tmp_path, rows, header="date,service,cost,region"):
    p = tmp_path / "billing.csv"
    p.write_text(header + "\n" + "\n".join(rows) + "\n")
    return str(p)


def test_sample_runs_end_to_end():
    a = CostAnalyzer(SAMPLE)
    s = a.summary()
    assert s["total_spend"] == pytest.approx(456.00)
    assert s["top_services"][0]["service"] == "AmazonEC2"
    assert s["forecast_30d"] == pytest.approx(2280.00, rel=1e-3)
    assert isinstance(s["anomalies"], list)


def test_missing_file_is_input_error():
    with pytest.raises(InputError):
        CostAnalyzer("/no/such/file.csv")


def test_missing_column_gives_clear_error(tmp_path):
    p = _csv(tmp_path, ["2023-10-01,EC2"], header="date,service")
    with pytest.raises(ValidationError) as e:
        CostAnalyzer(p)
    assert "cost" in str(e.value)


def test_non_numeric_cost_rejected(tmp_path):
    p = _csv(tmp_path, ["2023-10-01,EC2,abc,us-east-1"])
    with pytest.raises(ValidationError) as e:
        CostAnalyzer(p)
    assert "numeric" in str(e.value)


def test_negative_cost_rejected(tmp_path):
    p = _csv(tmp_path, ["2023-10-01,EC2,-5,us-east-1"])
    with pytest.raises(ValidationError):
        CostAnalyzer(p)


def test_bad_date_rejected(tmp_path):
    p = _csv(tmp_path, ["not-a-date,EC2,10,us-east-1"])
    with pytest.raises(ValidationError) as e:
        CostAnalyzer(p)
    assert "date" in str(e.value)


def test_empty_data_rejected(tmp_path):
    p = _csv(tmp_path, [])
    with pytest.raises(ValidationError):
        CostAnalyzer(p)


def test_anomaly_detection_fires(tmp_path):
    rows = [f"2023-10-{d:02d},EC2,10,us-east-1" for d in range(1, 20)]
    rows.append("2023-10-20,EC2,500,us-east-1")  # spike
    a = CostAnalyzer(_csv(tmp_path, rows))
    anomalies = a.detect_anomalies(threshold_std=2.0)
    assert len(anomalies) == 1
    assert str(anomalies.iloc[0]["date"].date()) == "2023-10-20"


def test_reports_render_all_formats():
    a = CostAnalyzer(SAMPLE)
    s = a.summary()
    for fmt in ("text", "markdown", "html"):
        out = render(s, client="TestCorp", fmt=fmt)
        assert "456.00" in out or "$456" in out
        assert "TestCorp" in out
    html = render(s, client="TestCorp", fmt="html")
    assert "<html" in html and "FinOps Cost Report" in html


def test_bad_threshold_rejected():
    a = CostAnalyzer(SAMPLE)
    with pytest.raises(ValidationError):
        a.detect_anomalies(threshold_std=-1)


def test_region_optional(tmp_path):
    p = _csv(tmp_path, ["2023-10-01,EC2,10"], header="date,service,cost")
    a = CostAnalyzer(p)
    assert a.get_total_spend() == pytest.approx(10.0)
    assert a.summary()["top_regions"] == []
