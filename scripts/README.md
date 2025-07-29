# SND-Bench Data Processing Scripts

This directory contains scripts for processing benchmark data and integrating with Weights & Biases (W&B).

## Scripts Overview

### 1. fixed-wandb-fetcher.py
Fetches benchmark run data from the W&B API and exports it in JSON format.

**Features:**
- Connect to W&B using API key from environment
- Fetch run history and metrics with pagination support
- Filter by model, date range, or specific run ID
- Export data in JSON format
- Comprehensive error handling

**Usage:**
```bash
# Fetch all runs
python scripts/fixed-wandb-fetcher.py --output wandb_data.json

# Fetch runs for specific model
python scripts/fixed-wandb-fetcher.py --model "qwen2.5-1.5b" --output qwen_runs.json

# Fetch runs from last 7 days
python scripts/fixed-wandb-fetcher.py --days 7 --output recent_runs.json

# Fetch specific run by ID
python scripts/fixed-wandb-fetcher.py --run-id "q20j435e" --output single_run.json
```

### 2. generate-site-with-wandb.py
Generates static HTML pages from benchmark results with W&B integration.

**Features:**
- Load benchmark results from JSON files
- Integrate W&B data for enhanced visualizations
- Generate individual run pages with AI summaries
- Create dashboard with model performance charts
- Include links to W&B runs
- Update metadata for comparison features

**Usage:**
```bash
# Generate site with W&B data
python scripts/generate-site-with-wandb.py --wandb-data wandb_data.json

# Generate site without W&B data
python scripts/generate-site-with-wandb.py

# Generate page for specific run only
python scripts/generate-site-with-wandb.py --run 20250729_004631
```

### 3. aggregate-benchmarks.py
Aggregates all benchmark data for comparison and analysis.

**Features:**
- Scan all runs/ directories
- Load and aggregate data.json files
- Calculate statistics (mean, median, std dev)
- Support filtering by model, task, accuracy, date
- Export to unified metadata.json
- Export to CSV for external analysis
- Print summary statistics

**Usage:**
```bash
# Aggregate all data and update metadata.json
python scripts/aggregate-benchmarks.py

# Filter and aggregate specific model
python scripts/aggregate-benchmarks.py --filter-model "qwen" --output qwen_metadata.json

# Export to CSV with filtering
python scripts/aggregate-benchmarks.py --csv benchmark_data.csv --min-accuracy 0.5

# Print summary statistics
python scripts/aggregate-benchmarks.py --summary
```

## Complete Workflow Example

Here's how to use all scripts together in the benchmark workflow:

```bash
#!/bin/bash

# 1. Run benchmark (existing script)
./run-benchmark.sh --model models/llama-7b.gguf --tasks hellaswag

# 2. Fetch latest W&B data
echo "Fetching W&B data..."
python scripts/fixed-wandb-fetcher.py \
    --entity sndlabs \
    --project llm-bench \
    --days 30 \
    --output wandb_data.json

# 3. Aggregate all benchmark data
echo "Aggregating benchmark data..."
python scripts/aggregate-benchmarks.py \
    --summary \
    --csv benchmark_summary.csv

# 4. Generate static site with W&B integration
echo "Generating static site..."
python scripts/generate-site-with-wandb.py \
    --wandb-data wandb_data.json

echo "Site generation complete! Open index.html to view results."
```

## Environment Setup

Required environment variables:
```bash
export WANDB_API_KEY="your_api_key_here"
export WANDB_ENTITY="sndlabs"  # or your entity
export WANDB_PROJECT="llm-bench"  # or your project
```

## Integration with run-benchmark.sh

The main benchmark script can be modified to automatically call these scripts:

```bash
# Add to end of run-benchmark.sh
if command -v python3 &> /dev/null; then
    # Aggregate data after each run
    python3 "$SCRIPT_DIR/scripts/aggregate-benchmarks.py" --quiet
    
    # Optionally fetch W&B data and regenerate site
    if [[ -n "${WANDB_API_KEY:-}" ]]; then
        python3 "$SCRIPT_DIR/scripts/fixed-wandb-fetcher.py" --limit 50 --output wandb_recent.json
        python3 "$SCRIPT_DIR/scripts/generate-site-with-wandb.py" --wandb-data wandb_recent.json
    fi
fi
```

## Error Handling

All scripts include comprehensive error handling:
- Missing API keys are detected and reported
- Network failures are caught with appropriate messages
- Invalid data formats are handled gracefully
- File I/O errors are logged with context

## Performance Considerations

- The W&B fetcher includes delays to avoid rate limiting
- Large datasets are processed with pagination
- Site generation is optimized for incremental updates
- Aggregation uses efficient data structures for large run counts

## Future Enhancements

Potential improvements for these scripts:
- Real-time dashboard updates via WebSocket
- Integration with more tracking platforms
- Advanced filtering and search in UI
- Automated report generation
- Performance regression detection
- Model comparison matrices
- Export to various formats (PDF, Excel)