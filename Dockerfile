# Python 3.11 slim: pandas/numpy need only stdlib + wheels, no build tools.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FINOPS_FORMAT=html \
    FINOPS_OUTPUT_DIR=/reports

WORKDIR /app

# Install deps first so layer is cached across code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY data/ ./data/

# Non-root for least privilege.
RUN useradd --create-home --shell /bin/false appuser \
    && mkdir -p /reports \
    && chown appuser:appuser /reports
USER appuser

# Default: analyze bundled sample data, write HTML report to /reports.
# Override at runtime: docker run -v /path/to/data:/data:ro -v /path/to/reports:/reports \
#   finops --file /data/billing.csv --format html --client "Acme Corp" --output /reports/acme.html
ENTRYPOINT ["python", "-m", "src.main"]
CMD ["--file", "data/sample_costs.csv"]
