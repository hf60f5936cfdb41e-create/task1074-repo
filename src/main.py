#!/usr/bin/env python3
"""
CLI entrypoint for TASK_1074.

Subcommand: process
  - Reads --input <file> (JSON list of objects)
  - Validates each object has fields:
      id (int), name (non-empty string), value (number)
  - Prints summary JSON to stdout:
      {"count": N, "total_value": X, "avg_value": Y}
"""

from __future__ import annotations
import argparse
import json
import sys
from typing import Any, Dict, List


def validate_item(item: Dict[str, Any]) -> None:
    """Validate a single item. Raises ValueError on invalid item."""
    if not isinstance(item, dict):
        raise ValueError("item must be an object")
    if "id" not in item:
        raise ValueError("missing field 'id'")
    if not isinstance(item["id"], int):
        raise ValueError("field 'id' must be int")
    if "name" not in item:
        raise ValueError("missing field 'name'")
    if not isinstance(item["name"], str) or not item["name"].strip():
        raise ValueError("field 'name' must be a non-empty string")
    if "value" not in item:
        raise ValueError("missing field 'value'")
    if not isinstance(item["value"], (int, float)):
        raise ValueError("field 'value' must be a number")


def process_file(path: str) -> Dict[str, float]:
    """Read JSON list from `path`, validate items, and return summary."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    if not isinstance(data, list):
        raise ValueError("input JSON must be a list")

    total = 0.0
    count = 0
    for item in data:
        validate_item(item)
        total += float(item["value"])
        count += 1

    avg = (total / count) if count else 0.0
    return {"count": count, "total_value": total, "avg_value": avg}


def build_parser() -> argparse.ArgumentParser:
    """Build argparse parser."""
    parser = argparse.ArgumentParser(prog="main")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("process", help="Process JSON input and output summary JSON")
    p.add_argument("--input", "-i", required=True, help="Path to input JSON file")
    return parser


def main(argv: List[str] | None = None) -> int:
    """CLI entrypoint. Returns exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "process":
            summary = process_file(args.input)
            print(json.dumps(summary, ensure_ascii=False))
            return 0
        else:
            parser.print_help()
            return 2
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
