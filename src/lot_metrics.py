#!/usr/bin/env python3
"""Load lot/inspection time-series readings from CSV."""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Reading:
    timestamp: datetime
    lot_id: str
    metric: str
    value: float


def parse_ts(raw: str) -> datetime:
    text = raw.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"bad timestamp: {raw!r}") from exc


def load_csv(path: Path) -> list[Reading]:
    rows: list[Reading] = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        required = {"timestamp", "lot_id", "metric", "value"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise SystemExit(f"CSV must include columns: {', '.join(sorted(required))}")
        for i, row in enumerate(reader, start=2):
            try:
                rows.append(
                    Reading(
                        timestamp=parse_ts(row["timestamp"]),
                        lot_id=row["lot_id"].strip(),
                        metric=row["metric"].strip(),
                        value=float(row["value"]),
                    )
                )
            except (KeyError, ValueError) as exc:
                raise SystemExit(f"line {i}: {exc}") from exc
    if not rows:
        raise SystemExit("no readings found")
    return rows


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Load lot inspection readings from CSV")
    p.add_argument("--file", "-f", type=Path, required=True, help="CSV readings file")
    args = p.parse_args(argv)

    readings = load_csv(args.file)
    print(f"loaded {len(readings)} readings from {args.file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
