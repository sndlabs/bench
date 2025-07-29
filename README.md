# SND-Bench

A comprehensive benchmarking framework for language models with support for multiple evaluation harnesses, hardware optimizations, and automated workflows.

## Features

- **Interactive Mode**: User-friendly menu system for selecting models and benchmarks
- **Multi-framework support**: Integrates with lm-evaluation-harness, llama.cpp, and custom evaluation pipelines
- **Multilingual Benchmarks**: Comprehensive support for both English and Korean language evaluations
- **Hardware optimization**: Automatic detection and optimization for Apple Silicon (Metal), NVIDIA GPUs (CUDA), and CPU
- **Automated workflows**: W&B integration for experiment tracking and AI-powered summaries
- **GitHub Pages Integration**: Automatic deployment of results to a professional dashboard
- **Flexible configuration**: YAML-based configuration system with hardware profiles
- **Virtual Environment**: Isolated Python environment for consistent dependencies

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/snd-bench.git
cd snd-bench
```

2. Set up virtual environment:
```bash
./setup-venv.sh
```

3. Copy and configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Run benchmarks:

### Interactive Mode (Recommended)
```bash
./run-benchmark.sh
# This will guide you through model and task selection
```

### Command Line Mode
```bash
# English benchmarks
./run-benchmark.sh --model gpt2 --tasks hellaswag,arc_easy

# Korean benchmarks
./run-benchmark.sh --model gpt2 --tasks kobest_boolq,kmmlu

# Mixed multilingual evaluation
./run-benchmark.sh --model meta-llama/Llama-2-7b-hf --tasks hellaswag,kobest_hellaswag
```

## Project Structure

```
snd-bench/
├── bench/              # Core benchmarking components
│   ├── config/        # Configuration files
│   ├── models/        # Model-specific code
│   ├── scripts/       # Utility scripts
│   └── integrations/  # Third-party integrations
├── scripts/           # Top-level scripts
├── src/              # Source code
├── tests/            # Test suite
├── docs/             # Documentation
├── config/           # Global configuration
├── models/           # Model storage
├── datasets/         # Dataset storage
├── results/          # Benchmark results
├── logs/             # Log files
└── assets/           # Web assets for reports
```

## Virtual Environment

The project uses a Python virtual environment to manage dependencies:

- **Setup**: Run `./setup-venv.sh` to create and configure the virtual environment
- **Activate**: Use `source venv/bin/activate` or `./activate.sh`
- **Deactivate**: Run `deactivate`
- **Auto-activation**: The `run-benchmark.sh` script automatically activates the virtual environment if it exists

Benefits of using the virtual environment:
- Isolated dependencies from system Python
- Consistent package versions across different machines
- Easy cleanup (just delete the `venv` directory)
- No conflicts with other Python projects

## Korean Language Support

SND-Bench includes comprehensive support for Korean language benchmarks:

- **KoBEST**: Korean NLU benchmark suite (BoolQ, COPA, HellaSwag, etc.)
- **KMMLU**: Korean Massive Multitask Language Understanding
- **KLUE**: Korean Language Understanding Evaluation
- **Additional benchmarks**: NSMC, Korean hate speech detection, and more

For detailed information, see [Korean Benchmarks Guide](docs/korean-benchmarks.md).

## Documentation

See the `docs/` directory for detailed documentation on:
- Installation and setup
- Configuration guide
- Hardware optimization
- Korean benchmarks guide
- API reference
- Contributing guidelines

## License

This project is licensed under the MIT License - see the LICENSE file for details.