"""FinOps Cost Analyzer CLI.

Reads a cloud billing CSV and produces a cost report as plain text,
Markdown, or a client-presentable self-contained HTML page.

Configuration (CLI flag beats env var beats built-in default):
    FINOPS_CLIENT_NAME    label shown on the report        (default: "Client")
    FINOPS_THRESHOLD_STD  anomaly threshold in std-devs    (default: 2.0)
    FINOPS_TOP_N          rows shown in top-N tables       (default: 5)
    FINOPS_FORMAT         text | markdown | html           (default: text)
    FINOPS_OUTPUT_DIR     default directory for reports   (default: ./reports)

A .env file in the working directory is loaded automatically.
"""

import argparse
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

from src.analyzer import CostAnalyzer
from src.errors import EXIT_UNEXPECTED, FinopsError, InputError, ValidationError, render_error
from src.report import render

load_dotenv()


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _positive_float(value: str) -> float:
    try:
        f = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"must be a number, got '{value}'")
    if f <= 0:
        raise argparse.ArgumentTypeError(f"must be positive, got '{value}'")
    return f


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="finops",
        description=(
            "Cloud FinOps Cost Analyzer — turn a cloud billing CSV into a "
            "presentable cost report (totals, top services/regions, anomaly "
            "detection, 30-day forecast)."
        ),
        epilog=(
            "CSV schema: headers date,service,cost (+ optional region); "
            "cost numeric >= 0. Example: "
            "python -m src.main --file data/sample_costs.csv --format html -o reports/report.html"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--file", "-f", required=True,
                   help="Path to the billing CSV file (required).")
    p.add_argument("--format", choices=["text", "markdown", "html"],
                   default=_env("FINOPS_FORMAT", "text"),
                   help="Report format. Default from FINOPS_FORMAT (default: text).")
    p.add_argument("--output", "-o", default=None,
                   help="Write the report to this file instead of stdout. "
                        "Default: <FINOPS_OUTPUT_DIR>/finops-report-<ts>.<ext>.")
    p.add_argument("--client", default=_env("FINOPS_CLIENT_NAME", "Client"),
                   help="Client name shown on the report. Default from "
                        "FINOPS_CLIENT_NAME (default: 'Client').")
    p.add_argument("--threshold", type=_positive_float,
                   default=_positive_float(_env("FINOPS_THRESHOLD_STD", "2.0")),
                   help="Anomaly threshold in standard deviations of daily spend. "
                        "Default from FINOPS_THRESHOLD_STD (default: 2.0).")
    p.add_argument("--top-n", type=int, default=int(_env("FINOPS_TOP_N", "5")),
                   help="Number of rows in top-N tables. Default from "
                        "FINOPS_TOP_N (default: 5).")
    p.add_argument("--version", action="version", version="finops 1.1.0")
    return p


def _default_output_path(fmt: str) -> str:
    out_dir = _env("FINOPS_OUTPUT_DIR", "reports")
    ext = {"text": "txt", "markdown": "md", "html": "html"}[fmt]
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return os.path.join(out_dir, f"finops-report-{ts}.{ext}")


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    if args.top_n <= 0:
        print(render_error(ValidationError("--top-n must be a positive integer.")),
              file=sys.stderr)
        return ValidationError.exit_code

    try:
        analyzer = CostAnalyzer(args.file)
        summary = analyzer.summary(threshold_std=args.threshold, top_n=args.top_n)
        report = render(summary, client=args.client, fmt=args.format)

        if args.output:
            out_path = args.output
        elif args.format == "text":
            out_path = None  # text goes to stdout by default
        else:
            out_path = _default_output_path(args.format)

        if out_path:
            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(report)
            print(f"Report written to: {out_path}")
        else:
            print(report, end="")
        return 0

    except FinopsError as exc:
        print(render_error(exc), file=sys.stderr)
        return exc.exit_code
    except BrokenPipeError:
        return 0
    except Exception:
        # Deliberately no traceback: end users get a clean line, not a dump.
        print(render_error(FinopsError("analysis failed")), file=sys.stderr)
        return EXIT_UNEXPECTED


if __name__ == "__main__":
    sys.exit(main())
