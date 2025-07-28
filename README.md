# SND-Bench

A comprehensive benchmarking framework for language models with support for multiple evaluation harnesses, hardware optimizations, and automated workflows.

## Features

- **Multi-framework support**: Integrates with lm-evaluation-harness, llama.cpp, and custom evaluation pipelines
- **Hardware optimization**: Automatic detection and optimization for Apple Silicon (Metal), NVIDIA GPUs (CUDA), and CPU
- **Automated workflows**: n8n integration for complex benchmarking pipelines
- **Comprehensive logging**: Weights & Biases integration for experiment tracking
- **Flexible configuration**: YAML-based configuration system with hardware profiles

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/snd-bench.git
cd snd-bench
```

2. Install dependencies:
```bash
pip install -r requirements.txt
pip install -e .
```

3. Run a benchmark:
```bash
./run-benchmark.sh --model llama-7b --tasks hellaswag,arc_easy
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

## Documentation

See the `docs/` directory for detailed documentation on:
- Installation and setup
- Configuration guide
- Hardware optimization
- API reference
- Contributing guidelines

## License

This project is licensed under the MIT License - see the LICENSE file for details.