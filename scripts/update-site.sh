#!/bin/bash
#
# Update Site Script - Fetches W&B data and regenerates static site
#
# This script demonstrates how to use all three data processing scripts
# together to update the benchmark dashboard with latest results.

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
WANDB_DAYS=30
WANDB_LIMIT=100
VERBOSE=false

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Update SND-Bench dashboard with latest benchmark data and W&B integration.

OPTIONS:
    -d, --days N         Fetch W&B runs from last N days (default: 30)
    -l, --limit N        Maximum W&B runs to fetch (default: 100)
    -s, --skip-wandb     Skip W&B data fetching
    -v, --verbose        Enable verbose output
    -h, --help          Show this help message

EXAMPLES:
    # Update with last 7 days of W&B data
    $0 --days 7

    # Update without W&B data (faster)
    $0 --skip-wandb

    # Verbose update with all data
    $0 --verbose --days 60 --limit 200

EOF
}

# Parse arguments
SKIP_WANDB=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--days)
            WANDB_DAYS="$2"
            shift 2
            ;;
        -l|--limit)
            WANDB_LIMIT="$2"
            shift 2
            ;;
        -s|--skip-wandb)
            SKIP_WANDB=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            usage
            exit 1
            ;;
    esac
done

# Check Python availability
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not found${NC}"
    exit 1
fi

# Change to project root
cd "$PROJECT_ROOT"

echo -e "${GREEN}=== SND-Bench Site Update ===${NC}"
echo "Project root: $PROJECT_ROOT"
echo ""

# Step 1: Aggregate benchmark data
echo -e "${BLUE}Step 1: Aggregating benchmark data...${NC}"
AGGREGATE_CMD="python3 scripts/aggregate-benchmarks.py"
if [[ "$VERBOSE" == "true" ]]; then
    AGGREGATE_CMD="$AGGREGATE_CMD --verbose --summary"
fi

if $AGGREGATE_CMD; then
    echo -e "${GREEN}✓ Benchmark data aggregated successfully${NC}"
else
    echo -e "${RED}✗ Failed to aggregate benchmark data${NC}"
    exit 1
fi

# Step 2: Fetch W&B data (if not skipped)
WANDB_DATA_FILE=""
if [[ "$SKIP_WANDB" == "false" ]]; then
    # Check for W&B API key
    if [[ -z "${WANDB_API_KEY:-}" ]]; then
        echo -e "${YELLOW}Warning: WANDB_API_KEY not set, skipping W&B integration${NC}"
        SKIP_WANDB=true
    else
        echo -e "${BLUE}Step 2: Fetching W&B data...${NC}"
        WANDB_DATA_FILE="wandb_data_$(date +%Y%m%d_%H%M%S).json"
        
        WANDB_CMD="python3 scripts/fixed-wandb-fetcher.py"
        WANDB_CMD="$WANDB_CMD --days $WANDB_DAYS"
        WANDB_CMD="$WANDB_CMD --limit $WANDB_LIMIT"
        WANDB_CMD="$WANDB_CMD --output $WANDB_DATA_FILE"
        
        if [[ "$VERBOSE" == "true" ]]; then
            WANDB_CMD="$WANDB_CMD --verbose"
        fi
        
        if $WANDB_CMD; then
            echo -e "${GREEN}✓ W&B data fetched successfully${NC}"
            echo "  Data saved to: $WANDB_DATA_FILE"
        else
            echo -e "${YELLOW}⚠ Failed to fetch W&B data, continuing without it${NC}"
            WANDB_DATA_FILE=""
        fi
    fi
else
    echo -e "${BLUE}Step 2: Skipping W&B data fetch${NC}"
fi

# Step 3: Generate static site
echo -e "${BLUE}Step 3: Generating static site...${NC}"
GENERATE_CMD="python3 scripts/generate-site-with-wandb.py"

if [[ -n "$WANDB_DATA_FILE" ]] && [[ -f "$WANDB_DATA_FILE" ]]; then
    GENERATE_CMD="$GENERATE_CMD --wandb-data $WANDB_DATA_FILE"
fi

if [[ "$VERBOSE" == "true" ]]; then
    GENERATE_CMD="$GENERATE_CMD --verbose"
fi

if $GENERATE_CMD; then
    echo -e "${GREEN}✓ Static site generated successfully${NC}"
else
    echo -e "${RED}✗ Failed to generate static site${NC}"
    exit 1
fi

# Step 4: Generate summary report
echo -e "${BLUE}Step 4: Generating summary report...${NC}"
if python3 scripts/aggregate-benchmarks.py --csv benchmark_summary.csv; then
    echo -e "${GREEN}✓ CSV summary exported${NC}"
    echo "  Summary saved to: benchmark_summary.csv"
fi

# Clean up old W&B data files (keep last 5)
if [[ "$SKIP_WANDB" == "false" ]]; then
    echo -e "${BLUE}Cleaning up old W&B data files...${NC}"
    ls -t wandb_data_*.json 2>/dev/null | tail -n +6 | xargs -r rm -f
fi

# Summary
echo ""
echo -e "${GREEN}=== Update Complete ===${NC}"
echo "Dashboard available at: file://$PROJECT_ROOT/index.html"

# Print statistics
if [[ -f "metadata.json" ]]; then
    TOTAL_RUNS=$(python3 -c "import json; print(json.load(open('metadata.json'))['total_runs'])")
    TOTAL_MODELS=$(python3 -c "import json; print(json.load(open('metadata.json'))['total_models'])")
    echo ""
    echo "Statistics:"
    echo "  Total runs: $TOTAL_RUNS"
    echo "  Models tested: $TOTAL_MODELS"
    
    if [[ -n "$WANDB_DATA_FILE" ]] && [[ -f "$WANDB_DATA_FILE" ]]; then
        WANDB_RUNS=$(python3 -c "import json; print(len(json.load(open('$WANDB_DATA_FILE'))))")
        echo "  W&B runs integrated: $WANDB_RUNS"
    fi
fi

# Offer to open in browser
if command -v open &> /dev/null; then
    echo ""
    read -p "Open dashboard in browser? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "$PROJECT_ROOT/index.html"
    fi
fi