#!/bin/bash

# Test script to verify the setup

echo "=== SND-Bench Setup Test ==="
echo

# Check Python
echo "Python version:"
python --version
echo

# Check if we're on the right branch
echo "Current git branch:"
git branch --show-current
echo

# Check directory structure
echo "Directory structure:"
find . -type d -name "__pycache__" -prune -o -type d -name ".git" -prune -o -type d -print | head -20
echo

# Check if required files exist
echo "Checking required files..."
required_files=(
    "run-benchmark.sh"
    "bench/__init__.py"
    "bench/config/merger.py"
    "bench/run_lm_eval.py"
    "scripts/fixed-wandb-fetcher.py"
    "scripts/generate-site-with-wandb.py"
    "scripts/aggregate-benchmarks.py"
    "requirements.txt"
    "setup.py"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
    fi
done
echo

# Check if scripts are executable
echo "Checking executable permissions..."
if [ -x "run-benchmark.sh" ]; then
    echo "✅ run-benchmark.sh is executable"
else
    echo "❌ run-benchmark.sh is not executable"
    chmod +x run-benchmark.sh
    echo "   Fixed: made executable"
fi
echo

echo "=== Setup test complete ==="