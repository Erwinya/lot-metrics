from datetime import datetime
from pathlib import Path
import json

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


def test_parse_ts_accepts_z_suffix() -> None:
    ts = lot_metrics.parse_ts("2026-08-05T08:00:00Z")
    assert ts.year == 2026
    assert ts.hour == 8


def test_main_rejects_non_positive_sigma(tmp_path: Path) -> None:
    path = tmp_path / "readings.csv"
    path.write_text(
        "timestamp,lot_id,metric,value\n2026-08-05T08:00:00Z,L1,m,1.0\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit, match="--sigma must be > 0"):
        lot_metrics.main(["-f", str(path), "--sigma", "0"])


def test_main_writes_json_export(tmp_path: Path) -> None:
    csv_path = tmp_path / "readings.csv"
    csv_path.write_text(
        "\n".join(
            [
                "timestamp,lot_id,metric,value",
                "2026-08-05T08:00:00Z,LOT-1,thickness_um,100.0",
                "2026-08-05T08:05:00Z,LOT-1,thickness_um,100.5",
            ]
        ),
        encoding="utf-8",
    )
    json_path = tmp_path / "summary.json"
    assert lot_metrics.main(["-f", str(csv_path), "--json", str(json_path)]) == 0
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["sigma"] == 3.5
    assert len(payload["series"]) == 1


def test_modified_z_single_value() -> None:
    assert lot_metrics.modified_z([42.0]) == [0.0]


def test_aggregate_constant_series_has_no_outliers() -> None:
    readings = [
        lot_metrics.Reading(datetime(2026, 8, 5, 8, i), "LOT-1", "thickness_um", 100.0)
        for i in range(5)
    ]
    aggs = lot_metrics.aggregate(readings, sigma=3.5)
    assert len(aggs) == 1
    assert aggs[0].stdev == 0.0
    assert aggs[0].outliers == []
