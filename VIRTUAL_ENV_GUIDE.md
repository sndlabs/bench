# Virtual Environment Guide for SND-Bench

## Overview

SND-Bench uses a Python virtual environment to ensure consistent dependencies and avoid conflicts with system packages.

## Quick Commands

- **First-time setup**: `./setup-venv.sh`
- **Activate**: `source venv/bin/activate` or `./activate.sh`
- **Deactivate**: `deactivate`
- **Check if activated**: `which python` (should show `venv/bin/python`)

## Automatic Activation

The `run-benchmark.sh` script automatically activates the virtual environment if it exists, so you don't need to manually activate it before running benchmarks.

## Manual Setup

If you prefer to set up manually:

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

## Troubleshooting

1. **Python version issues**: The project requires Python 3.8+. Check with `python3 --version`

2. **Missing venv module**: Install with `sudo apt-get install python3-venv` (Ubuntu) or `brew install python3` (macOS)

3. **Permission errors**: Ensure you have write permissions in the project directory

4. **Corrupted venv**: Delete with `rm -rf venv` and run `./setup-venv.sh` again

## Benefits

- **Isolation**: Dependencies don't affect system Python
- **Reproducibility**: Same package versions across all developers
- **Easy cleanup**: Just delete the `venv` directory
- **Multiple Python versions**: Can use different Python version than system

## VS Code Integration

If using VS Code, it should automatically detect the virtual environment. If not:

1. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
2. Type "Python: Select Interpreter"
3. Choose the interpreter at `./venv/bin/python`

## PyCharm Integration

PyCharm should automatically detect the virtual environment. If not:

1. Go to Settings → Project → Python Interpreter
2. Click the gear icon → Add
3. Select "Existing environment"
4. Browse to `./venv/bin/python`