# lot-metrics

Local time-series toolkit for lot / inspection measurements.

Inspired by the *problem class* of industrial time-series stores (ingest -> aggregate -> flag outliers), not a database clone.

## Usage

CSV columns: `timestamp`, `lot_id`, `metric`, `value`.

```bash
python src/lot_metrics.py -f samples/readings.csv
```

Install locally (optional):

```bash
pip install -e .
lot-metrics -f samples/readings.csv
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

Export aggregates as JSON:

```bash
python src/lot_metrics.py -f samples/readings.csv --json out/summary.json
```

`--sigma` sets the modified z-score outlier threshold (default `3.5`).

Browser companion for exploring the same CSV/MAD workflow: [lot-viewer](https://github.com/Erwinya/lot-viewer).

## License

MIT
