# Taegis XDR Detection Analysis

This tool analyzes large CSV files exported from Taegis XDR and generates a Sankey diagram visualizing the flow of alerts from sensor types through severity levels to their final status.

## Features

- Processes large CSV files (tested with 4.6 GB files) efficiently using chunked reading
- Extracts relationships between:
  - **Sensor Types** (e.g., Mimecast, ENDPOINT_TAEGIS)
  - **Severity Levels** (e.g., INFO, HIGH, CRITICAL)
  - **Status Values** (e.g., OPEN, SUPPRESSED, RESOLVED)
- Generates interactive Sankey diagram visualization
- Provides detailed summary statistics

## Requirements

- Python 3.7 or higher
- Required Python packages (see `requirements.txt`)

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python analyze_taegis_detections.py path/to/detections.csv
```

### Advanced Options

```bash
python analyze_taegis_detections.py path/to/detections.csv \
    --chunk-size 50000 \
    --output my_sankey_diagram.png \
    --exclude-info
```

### Command Line Arguments

- `csv_file` (required): Path to the Taegis XDR detections CSV file
- `--chunk-size` (optional): Number of rows to process at a time (default: 100000)
  - Reduce this value if you encounter memory issues
  - Increase for faster processing if you have sufficient RAM
- `--output` (optional): Output path for the Sankey diagram (default: `sankey_diagram.png`)
- `--exclude-info` (optional): Exclude INFO severity level from analysis
  - When enabled, focuses analysis on LOW, MEDIUM, HIGH, and CRITICAL severity levels
  - Useful for filtering out low-priority informational alerts

## Output

The script generates:

1. **Console Output**: Summary statistics including:
   - Total alerts processed
   - Unique sensor types, severity levels, and status values
   - Distribution of alerts by sensor type, severity, and status
   - Top 10 sensor type → severity → status flows

2. **Sankey Diagram**: A PNG image file (or HTML if PNG export fails) showing:
   - Left nodes: Sensor types
   - Middle nodes: Severity levels
   - Right nodes: Status values
   - Flow thickness represents the number of alerts following each path

## Example Output

```
Processing CSV file: detections.csv
Chunk size: 100,000 rows
Excluding INFO severity level from analysis
Processing chunk 1 (100000 rows)...
...
Finished processing 5,234,567 rows
Excluded 3,456,789 rows with INFO severity

================================================================================
ANALYSIS SUMMARY
================================================================================
Total alerts processed: 5,234,567
Unique sensor types: 3
Unique severity levels: 4
Unique status values: 3

Sensor Types:
  - ENDPOINT_TAEGIS: 2,345,678 alerts
  - Mimecast: 2,888,889 alerts

Severity Distribution:
  - INFO: 4,123,456 alerts
  - HIGH: 1,111,111 alerts

Status Distribution:
  - OPEN: 3,456,789 alerts
  - SUPPRESSED: 1,777,778 alerts
...
```

## Troubleshooting

### Memory Issues

If you encounter memory errors when processing very large files:

1. Reduce the chunk size:
   ```bash
   python analyze_taegis_detections.py detections.csv --chunk-size 50000
   ```

2. Ensure you have sufficient available RAM (recommended: 8GB+ for 4.6 GB CSV files)

### PNG Export Issues

If PNG export fails, the script will automatically fall back to HTML format. To enable PNG export:

1. Ensure `kaleido` is installed:
   ```bash
   pip install kaleido
   ```

2. On Windows, you may need to install additional dependencies. See [Plotly's documentation](https://plotly.com/python/static-image-export/) for details.

### Column Not Found Errors

If you see an error about missing columns, verify that your CSV file contains:
- `sensor_types` column
- `severity` column
- `status` column

The script will display available columns if the expected columns are not found.

## Data Format

The script expects a CSV file with the following columns:

- **sensor_types**: JSON array string (e.g., `["Mimecast"]` or `["ENDPOINT_TAEGIS"]`)
- **severity**: String value (e.g., `"INFO"`, `"HIGH"`, `"CRITICAL"`)
- **status**: String value (e.g., `"OPEN"`, `"SUPPRESSED"`, `"RESOLVED"`)

The script handles various formats including quoted strings and JSON arrays.

## Performance

- Processing time depends on file size and system resources
- For a 4.6 GB file with ~5 million rows:
  - Processing: ~5-15 minutes (depending on hardware)
  - Memory usage: ~2-4 GB RAM
  - Output file size: ~500 KB - 2 MB (PNG) or ~1-5 MB (HTML)

## License

This script is provided as-is for analyzing Taegis XDR detection data.
