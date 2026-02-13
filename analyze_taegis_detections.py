#!/usr/bin/env python3
"""
Taegis XDR Detection Analysis Script

Analyzes a large CSV file containing Taegis XDR detections and generates
a Sankey diagram showing the flow: sensor_types → severity → status.
"""

import pandas as pd
import json
import ast
import sys
from collections import defaultdict
from pathlib import Path
import plotly.graph_objects as go


def parse_sensor_types(sensor_types_str):
    """
    Parse sensor_types field which is a JSON array string.
    Handles various formats including quoted strings.
    """
    if pd.isna(sensor_types_str) or sensor_types_str == '':
        return []
    
    # Remove surrounding quotes if present
    sensor_types_str = str(sensor_types_str).strip()
    if sensor_types_str.startswith('"') and sensor_types_str.endswith('"'):
        sensor_types_str = sensor_types_str[1:-1]
    
    try:
        # Try JSON parsing first
        parsed = json.loads(sensor_types_str)
        if isinstance(parsed, list):
            return [str(s).strip('"') for s in parsed]
        return [str(parsed).strip('"')]
    except (json.JSONDecodeError, ValueError):
        try:
            # Try ast.literal_eval as fallback
            parsed = ast.literal_eval(sensor_types_str)
            if isinstance(parsed, list):
                return [str(s).strip('"') for s in parsed]
            return [str(parsed).strip('"')]
        except (ValueError, SyntaxError):
            # If all else fails, try to extract from string directly
            if sensor_types_str.startswith('[') and sensor_types_str.endswith(']'):
                # Remove brackets and split
                content = sensor_types_str[1:-1]
                items = [s.strip().strip('"').strip("'") for s in content.split(',')]
                return [s for s in items if s]
            return [sensor_types_str]


def clean_string_field(value):
    """Remove surrounding quotes from string fields."""
    if pd.isna(value):
        return None
    value = str(value).strip()
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    return value if value else None


def process_csv_chunks(csv_path, chunk_size=100000, exclude_info=False):
    """
    Process CSV file in chunks and aggregate sensor_type → severity → status flows.
    
    Args:
        csv_path: Path to CSV file
        chunk_size: Number of rows to process at a time
        exclude_info: If True, exclude rows with severity="INFO"
    """
    flow_counts = defaultdict(int)
    total_rows = 0
    excluded_rows = 0
    sensor_types_set = set()
    severity_set = set()
    status_set = set()
    
    print(f"Processing CSV file: {csv_path}")
    print(f"Chunk size: {chunk_size:,} rows")
    if exclude_info:
        print("Excluding INFO severity level from analysis")
    
    try:
        chunk_iter = pd.read_csv(csv_path, chunksize=chunk_size, low_memory=False)
        
        for chunk_num, chunk in enumerate(chunk_iter, 1):
            print(f"Processing chunk {chunk_num} ({len(chunk):,} rows)...", end='\r')
            
            # Extract relevant columns
            if 'sensor_types' not in chunk.columns:
                print(f"\nError: 'sensor_types' column not found in CSV")
                print(f"Available columns: {list(chunk.columns)}")
                sys.exit(1)
            
            for idx, row in chunk.iterrows():
                total_rows += 1
                
                # Parse sensor_types
                sensor_types = parse_sensor_types(row.get('sensor_types'))
                severity = clean_string_field(row.get('severity'))
                status = clean_string_field(row.get('status'))
                
                # Skip rows with missing critical fields
                if not sensor_types or severity is None or status is None:
                    continue
                
                # Skip INFO severity if exclude_info is True
                if exclude_info and severity.upper() == 'INFO':
                    excluded_rows += 1
                    continue
                
                # Track unique values
                sensor_types_set.update(sensor_types)
                severity_set.add(severity)
                status_set.add(status)
                
                # Count flows for each sensor type
                for sensor_type in sensor_types:
                    flow_key = (sensor_type, severity, status)
                    flow_counts[flow_key] += 1
            
            if chunk_num % 10 == 0:
                print(f"\nProcessed {chunk_num} chunks ({total_rows:,} rows total)")
        
        print(f"\nFinished processing {total_rows:,} rows")
        if exclude_info:
            print(f"Excluded {excluded_rows:,} rows with INFO severity")
        
    except FileNotFoundError:
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing CSV: {e}")
        sys.exit(1)
    
    return flow_counts, sensor_types_set, severity_set, status_set, total_rows


def create_sankey_diagram(flow_counts, sensor_types_set, severity_set, status_set, output_path='sankey_diagram.png'):
    """
    Create a Sankey diagram showing sensor_types → severity → status flows.
    """
    # Sort sets for consistent ordering
    sensor_types = sorted(sensor_types_set)
    severities = sorted(severity_set)
    statuses = sorted(status_set)
    
    # Create node labels (left: sensor types, middle: severities, right: statuses)
    all_nodes = sensor_types + severities + statuses
    node_indices = {node: idx for idx, node in enumerate(all_nodes)}
    
    # Calculate node positions
    num_sensor_types = len(sensor_types)
    num_severities = len(severities)
    num_statuses = len(statuses)
    
    # Create source, target, and value lists for edges
    sources = []
    targets = []
    values = []
    
    # First layer: sensor_types → severity
    sensor_severity_counts = defaultdict(int)
    for (sensor_type, severity, status), count in flow_counts.items():
        sensor_severity_counts[(sensor_type, severity)] += count
    
    for (sensor_type, severity), count in sensor_severity_counts.items():
        sources.append(node_indices[sensor_type])
        targets.append(node_indices[severity])
        values.append(count)
    
    # Second layer: severity → status
    severity_status_counts = defaultdict(int)
    for (sensor_type, severity, status), count in flow_counts.items():
        severity_status_counts[(severity, status)] += count
    
    for (severity, status), count in severity_status_counts.items():
        sources.append(node_indices[severity])
        targets.append(node_indices[status])
        values.append(count)
    
    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=all_nodes,
            color="lightblue"
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color="rgba(0, 0, 255, 0.3)"
        )
    )])
    
    fig.update_layout(
        title_text="Taegis XDR Detection Flow: Sensor Types → Severity → Status",
        font_size=12,
        width=1600,
        height=900
    )
    
    # Save as PNG
    print(f"\nSaving Sankey diagram to {output_path}...")
    try:
        fig.write_image(output_path, width=1600, height=900, scale=2)
        print(f"Successfully saved Sankey diagram to {output_path}")
    except Exception as e:
        print(f"Warning: Could not save as PNG ({e})")
        print("Saving as HTML instead...")
        html_path = output_path.replace('.png', '.html')
        fig.write_html(html_path)
        print(f"Saved as HTML: {html_path}")
        print("Note: Install kaleido (pip install kaleido) for PNG export")


def print_summary_statistics(flow_counts, sensor_types_set, severity_set, status_set, total_rows):
    """Print summary statistics."""
    print("\n" + "="*80)
    print("ANALYSIS SUMMARY")
    print("="*80)
    print(f"Total alerts processed: {total_rows:,}")
    print(f"Unique sensor types: {len(sensor_types_set)}")
    print(f"Unique severity levels: {len(severity_set)}")
    print(f"Unique status values: {len(status_set)}")
    
    print("\nSensor Types:")
    for st in sorted(sensor_types_set):
        count = sum(v for (s, sev, stat), v in flow_counts.items() if s == st)
        print(f"  - {st}: {count:,} alerts")
    
    print("\nSeverity Distribution:")
    severity_dist = defaultdict(int)
    for (sensor_type, severity, status), count in flow_counts.items():
        severity_dist[severity] += count
    for sev in sorted(severity_dist.keys()):
        print(f"  - {sev}: {severity_dist[sev]:,} alerts")
    
    print("\nStatus Distribution:")
    status_dist = defaultdict(int)
    for (sensor_type, severity, status), count in flow_counts.items():
        status_dist[status] += count
    for stat in sorted(status_dist.keys()):
        print(f"  - {stat}: {status_dist[stat]:,} alerts")
    
    print("\nTop 10 Sensor Type → Severity → Status Flows:")
    sorted_flows = sorted(flow_counts.items(), key=lambda x: x[1], reverse=True)
    for (sensor_type, severity, status), count in sorted_flows[:10]:
        print(f"  {sensor_type} → {severity} → {status}: {count:,} alerts")
    
    print("="*80)


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Analyze Taegis XDR detection CSV and generate Sankey diagram'
    )
    parser.add_argument(
        'csv_file',
        type=str,
        help='Path to the Taegis XDR detections CSV file'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=100000,
        help='Number of rows to process at a time (default: 100000)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='sankey_diagram.png',
        help='Output path for Sankey diagram (default: sankey_diagram.png)'
    )
    parser.add_argument(
        '--exclude-info',
        action='store_true',
        help='Exclude INFO severity level from analysis (focus on LOW, MEDIUM, HIGH, CRITICAL)'
    )
    
    args = parser.parse_args()
    
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)
    
    # Process CSV file
    flow_counts, sensor_types_set, severity_set, status_set, total_rows = process_csv_chunks(
        csv_path, args.chunk_size, exclude_info=args.exclude_info
    )
    
    if not flow_counts:
        print("Error: No valid data found in CSV file")
        sys.exit(1)
    
    # Print summary statistics
    print_summary_statistics(
        flow_counts, sensor_types_set, severity_set, status_set, total_rows
    )
    
    # Create Sankey diagram
    create_sankey_diagram(
        flow_counts, sensor_types_set, severity_set, status_set, args.output
    )
    
    print("\nAnalysis complete!")


if __name__ == '__main__':
    main()
