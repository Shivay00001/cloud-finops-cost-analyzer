# Cloud FinOps Cost Analyzer

Turn a cloud billing CSV into a **client-presentable cost report**: total spend, top services/regions, anomaly detection, and a 30-day forecast — as terminal text, Markdown, or a styled self-contained **HTML report** you can email straight to a client.

Pure Python + pandas. No cloud credentials, no network calls, no AI keys — it reads a CSV you already have (AWS Cost Explorer export, GCP billing export, or a hand-made sheet) and reports on it.

## Quick start (fresh clone)

```bash
git clone https://github.com/Shivay00001/cloud-finops-cost-analyzer.git
cd cloud-finops-cost-analyzer

python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Analyze the bundled sample data
python -m src.main --file data/sample_costs.csv

# Generate the client-presentable HTML report
python -m src.main --file data/sample_costs.csv --format html \
    --client "Acme Corp" --output reports/acme.html
```

Optional: copy `.env.example` to `.env` to set defaults (client name, threshold, format).

## CSV input schema

| Column | Required | Rules |
|---|---|---|
| `date` | yes | parseable date (`2023-10-01`, `01/10/2023`, …) |
| `service` | yes | non-empty string (e.g. `AmazonEC2`) |
| `cost` | yes | numeric, ≥ 0 (USD) |
| `region` | no | any string; if present you get a per-region breakdown |

Bad input fails with a clear one-line error (`ERROR [ValidationError]: ...`) and a non-zero exit code — never a traceback. Exit codes: `1` = input problem, `2` = CSV validation problem, `3` = unexpected.

## CLI reference

```
python -m src.main --help
```

| Flag | Description |
|---|---|
| `--file PATH` / `-f` | Billing CSV (required) |
| `--format {text,markdown,html}` | Report format (default: text, or `FINOPS_FORMAT`) |
| `--output PATH` / `-o` | Write report to file; html/markdown default to `reports/finops-report-<ts>.<ext>` |
| `--client NAME` | Client name printed on the report |
| `--threshold N` | Anomaly sensitivity: flag days where daily spend > mean + N·σ (default 2.0) |
| `--top-n N` | Rows in top-N tables (default 5) |
| `--version` | Print version |

Every flag also has an env var (flag wins over env):

| Env var | Default | Meaning |
|---|---|---|
| `FINOPS_CLIENT_NAME` | `Client` | Report client label |
| `FINOPS_THRESHOLD_STD` | `2.0` | Anomaly threshold (std-devs) |
| `FINOPS_TOP_N` | `5` | Top-N table rows |
| `FINOPS_FORMAT` | `text` | `text` / `markdown` / `html` |
| `FINOPS_OUTPUT_DIR` | `reports` | Default report directory |

**Security note:** this tool takes no secrets and needs none — `.env` holds only display defaults. No hardcoded credentials exist anywhere in the repo.

## What the report contains

- **Total spend** and period covered (dates, days, row count)
- **Top services by spend** (with share %) and **top regions**
- **Anomaly detection**: days where spend exceeds mean + N standard deviations
- **30-day forecast**: straight-line projection (daily average × 30) — no ML claims

## Testing

```bash
pytest tests/ -q                                  # unit tests (11)
./scripts/smoke_test.sh                           # end-to-end: sample data → text/html/md reports, error paths, --help
```

`scripts/smoke_test.sh` is the release gate — it must pass before any client delivery.

## Deploy as a scheduled batch (Render free tier)

This is a batch job, not a server — run it on a schedule (Render Cron Job):

1. Push this repo to GitHub. In Render: **New → Cron Job**, point at the repo.
2. Build command: `pip install -r requirements.txt`
3. Command (drop the client's monthly export into the repo or a mounted disk, e.g. `data/client.csv`):
   ```
   python -m src.main --file data/client.csv --format html --client "Client Name" --output reports/monthly.html
   ```
4. Schedule: `0 9 1 * *` (9:00 on the 1st of each month, UTC) or weekly `0 9 * * 1`.
5. Env vars (optional): `FINOPS_CLIENT_NAME`, `FINOPS_THRESHOLD_STD`, `FINOPS_FORMAT=html`, `FINOPS_OUTPUT_DIR`.
6. Serve the generated report: upload `reports/monthly.html` anywhere static (Cloudflare Pages, or just email the file to the client — it's fully self-contained, no external assets).

No HTTP endpoint is exposed, so no API-key auth is needed — nothing listens on any port.

## Project layout

```
src/main.py        CLI entrypoint (argparse, env config, structured errors)
src/analyzer.py    CostAnalyzer: CSV load + schema validation + metrics
src/report.py      text / markdown / self-contained HTML renderers
src/errors.py      FinopsError hierarchy + clean error rendering
tests/             pytest suite
scripts/smoke_test.sh   end-to-end release gate
data/sample_costs.csv   sample billing data
Dockerfile         container image (batch use)
```

## License

MIT — see `LICENSE`.
