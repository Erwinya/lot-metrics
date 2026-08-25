# lot-metrics

Local time-series toolkit for lot / inspection measurements.

Inspired by the *problem class* of industrial time-series stores (ingest -> aggregate -> flag outliers), not a database clone.

## Usage

CSV columns: `timestamp`, `lot_id`, `metric`, `value`.

```bash
python src/lot_metrics.py -f samples/readings.csv
```

Export aggregates as JSON:

```bash
python src/lot_metrics.py -f samples/readings.csv --json out/summary.json
```

`--sigma` sets the modified z-score outlier threshold (default `3.5`).

## License

MIT
