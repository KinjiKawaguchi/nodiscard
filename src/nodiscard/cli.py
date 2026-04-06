"""CLI entry point for nodiscard."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

from nodiscard._models import CheckResult, Violation
from nodiscard.checker import check


def main(argv: list[str] | None = None) -> int:
    """Entry point for ``nodiscard check``."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "handler"):
        parser.print_help()
        return 0

    return args.handler(args)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nodiscard",
        description="Detect discarded return values of @nodiscard methods",
    )
    sub = parser.add_subparsers()

    check_parser = sub.add_parser("check", help="Run the checker")
    check_parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Files or directories to check",
    )
    check_parser.add_argument(
        "--src",
        dest="src_roots",
        action="append",
        type=Path,
        default=None,
        help="Source root(s) for import resolution",
    )
    check_parser.add_argument(
        "--exclude",
        action="append",
        default=None,
        help="Glob patterns to exclude",
    )
    check_parser.add_argument(
        "--format",
        dest="output_format",
        choices=("text", "json"),
        default=None,
        help="Output format (default: text)",
    )
    check_parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to pyproject.toml",
    )
    check_parser.set_defaults(handler=_handle_check)
    return parser


def _handle_check(args: argparse.Namespace) -> int:
    config = _load_config(args.config)

    paths = args.paths or [Path(p) for p in config.get("src", ["."])]
    if not paths:
        paths = [Path(".")]

    src_roots = args.src_roots or None
    exclude = args.exclude or config.get("exclude", [])
    output_format = args.output_format or config.get("format", "text")

    # Validate paths exist
    for p in paths:
        if not p.exists():
            sys.stderr.write(f"Error: path does not exist: {p}\n")
            return 2

    result = check(paths, src_roots=src_roots, exclude=exclude)

    if output_format == "json":
        _output_json(result)
    else:
        _output_text(result)

    return 1 if result.violations else 0


def _load_config(config_path: Path | None) -> dict[str, object]:
    """Load [tool.nodiscard] from pyproject.toml."""
    if config_path is None:
        config_path = Path("pyproject.toml")
    if not config_path.is_file():
        return {}
    try:
        with config_path.open("rb") as f:
            data = tomllib.load(f)
        return data.get("tool", {}).get("nodiscard", {})
    except (tomllib.TOMLDecodeError, OSError):
        return {}


def _output_text(result: CheckResult) -> None:
    for v in result.violations:
        sys.stdout.write(
            f"{v.file_path}:{v.line}:{v.col}: {v.code} {v.message}\n",
        )
    count = len(result.violations)
    if count:
        sys.stdout.write(f"Found {count} error{'s' if count != 1 else ''}.\n")


def _output_json(result: CheckResult) -> None:
    output = {
        "violations": [_violation_to_dict(v) for v in result.violations],
        "summary": {
            "files_checked": result.files_checked,
            "files_skipped": result.files_skipped,
            "violations": len(result.violations),
        },
    }
    sys.stdout.write(json.dumps(output, indent=2, default=str) + "\n")


def _violation_to_dict(v: Violation) -> dict[str, object]:
    return {
        "file": str(v.file_path),
        "line": v.line,
        "col": v.col,
        "code": v.code,
        "method": v.method_name,
        "receiver_type": v.receiver_type,
        "message": v.message,
    }


if __name__ == "__main__":
    sys.exit(main())
