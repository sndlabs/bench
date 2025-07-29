#!/bin/bash
# Convenience script to activate the virtual environment

echo "Activating snd-bench virtual environment..."
source venv/bin/activate
echo "Virtual environment activated. Python: $(which python)"
echo "To deactivate, run: deactivate"