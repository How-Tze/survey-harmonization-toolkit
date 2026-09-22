from __future__ import annotations

import argparse
import json
from pathlib import Path

from survey_harmonization.config import ConfigError
from survey_harmonization.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="survey-harmonization",
        description="Audit and harmonize the bundled synthetic survey ecosystem.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="Run audit, harmonization, validation, and reporting")
    run.add_argument("--config-dir", type=Path, default=Path("config"))
    run.add_argument("--output-dir", type=Path, required=True)
    run.add_argument("--run-timestamp", required=True)
    run.add_argument(
        "--strict",
        action="store_true",
        help="Return exit code 2 when reviewed blocked mappings remain.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_pipeline(
            args.config_dir,
            args.output_dir,
            run_timestamp=args.run_timestamp,
        )
    except ConfigError as error:
        print(str(error))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if result["validation_errors"]:
        return 1
    if args.strict and result["blocked_mappings"]:
        return 2
    return 0
