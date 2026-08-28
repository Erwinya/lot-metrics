from datetime import datetime
from pathlib import Path

import pytest

import lot_metrics


def test_median_odd_values() -> None:
    assert lot_metrics.median([3.0, 1.0, 2.0]) == 2.0


def test_aggregate_flags_outlier() -> None:
    readings = [
        lot_metrics.Reading(datetime(2026, 8, 5, 8, 0), "LOT-1", "thickness_um", 100.0),
        lot_metrics.Reading(datetime(2026, 8, 5, 8, 5), "LOT-1", "thickness_um", 100.2),
        lot_metrics.Reading(datetime(2026, 8, 5, 8, 10), "LOT-1", "thickness_um", 100.1),
        lot_metrics.Reading(datetime(2026, 8, 5, 8, 15), "LOT-1", "thickness_um", 150.0),
    ]
    aggs = lot_metrics.aggregate(readings, sigma=2.0)
    assert len(aggs) == 1
    assert aggs[0].count == 4
    assert len(aggs[0].outliers) == 1


def test_load_csv_requires_columns(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("timestamp,lot_id\n2026-01-01T00:00:00Z,L1\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="CSV must include columns"):
        lot_metrics.load_csv(path)


def test_main_missing_file() -> None:
    with pytest.raises(SystemExit, match="file not found"):
        lot_metrics.main(["-f", "missing.csv"])
