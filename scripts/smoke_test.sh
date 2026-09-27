#!/usr/bin/env bash
# Smoke test: run the analyzer on the bundled sample data in every format,
# verify reports are produced and sane. Keeps working after install-from-scratch.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

PY="${PYTHON_BIN:-python3}"
echo "== FinOps smoke test =="

# 1. Text report to stdout
$PY -m src.main --file data/sample_costs.csv --format text | grep -q "Total Spend"
echo "[ok] text report on stdout"

# 2. HTML report to file (client-presentable output)
$PY -m src.main --file data/sample_costs.csv --format html \
    --client "Smoke Test Corp" --output reports/smoke-report.html
test -s reports/smoke-report.html
grep -q "FinOps Cost Report" reports/smoke-report.html
grep -q "Smoke Test Corp" reports/smoke-report.html
echo "[ok] html report written"

# 3. Markdown report to file
$PY -m src.main --file data/sample_costs.csv --format markdown \
    --output reports/smoke-report.md
test -s reports/smoke-report.md
grep -q "## Summary" reports/smoke-report.md
echo "[ok] markdown report written"

# 4. Bad input -> structured error, non-zero exit, no traceback
if $PY -m src.main --file data/does-not-exist.csv 2>reports/err.log; then
    echo "[FAIL] missing file should exit non-zero"; exit 1
fi
grep -q "ERROR" reports/err.log
if grep -qi "traceback" reports/err.log; then
    echo "[FAIL] traceback leaked"; exit 1
fi
echo "[ok] structured error, no traceback"

# 5. Invalid CSV -> clear validation error
printf 'date,service\n2023-10-01,EC2\n' > reports/bad.csv
if $PY -m src.main --file reports/bad.csv 2>reports/err2.log; then
    echo "[FAIL] bad csv should exit non-zero"; exit 1
fi
grep -q "missing required column" reports/err2.log
echo "[ok] csv validation error is clear"

# 6. --help documents all options
$PY -m src.main --help | grep -q "\-\-format"
$PY -m src.main --help | grep -q "\-\-client"
echo "[ok] --help complete"

echo "== ALL SMOKE TESTS PASSED =="
