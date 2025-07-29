#!/bin/bash
# Setup script to create and configure the virtual environment

echo "=== SND-Bench Virtual Environment Setup ==="
echo

# Check if venv already exists
if [ -d "venv" ]; then
    echo "Virtual environment already exists."
    read -p "Do you want to recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing virtual environment..."
        rm -rf venv
    else
        echo "Using existing virtual environment."
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Requirements installed"
else
    echo "❌ requirements.txt not found"
fi

# Ensure lm-eval is installed (it's also in requirements.txt)
echo "Verifying lm-eval installation..."
if ! command -v lm_eval &> /dev/null; then
    echo "Installing lm-eval..."
    pip install lm-eval
fi
echo "✅ lm-eval is installed"

# Install package in development mode
echo "Installing snd-bench in development mode..."
if [ -f "setup.py" ]; then
    pip install -e .
    echo "✅ snd-bench installed in development mode"
else
    echo "❌ setup.py not found"
fi

# Show installed packages
echo
echo "Installed packages:"
pip list | head -20
echo "..."
echo

echo "=== Setup complete ==="
echo
echo "To activate the environment in the future, run:"
echo "  source venv/bin/activate"
echo "or"
echo "  ./activate.sh"
echo
echo "To deactivate, run:"
echo "  deactivate"