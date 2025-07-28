#!/bin/bash

# SND-Bench Main Orchestrator Script
# This script coordinates benchmarking runs across multiple frameworks

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Default values
MODEL=""
TASKS="hellaswag"
FRAMEWORK="lm-eval"
OUTPUT_DIR="$PROJECT_ROOT/results"
LOG_DIR="$PROJECT_ROOT/logs"
CONFIG_FILE=""
HARDWARE_PROFILE="auto"
WANDB_PROJECT="snd-bench"
VERBOSE=false
DRY_RUN=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

SND-Bench: Comprehensive Language Model Benchmarking Framework

OPTIONS:
    -m, --model PATH         Path to model file or model identifier (required)
    -t, --tasks TASKS        Comma-separated list of evaluation tasks (default: hellaswag)
    -f, --framework NAME     Evaluation framework to use (default: lm-eval)
                            Options: lm-eval, llama-cpp, custom
    -o, --output DIR        Output directory for results (default: ./results)
    -c, --config FILE       Configuration file path
    -p, --profile NAME      Hardware profile (default: auto)
    --wandb-project NAME    Weights & Biases project name (default: snd-bench)
    -v, --verbose           Enable verbose output
    -n, --dry-run          Show what would be executed without running
    -h, --help             Show this help message

EXAMPLES:
    # Basic benchmark with lm-evaluation-harness
    $0 --model gpt2 --tasks hellaswag,arc_easy

    # Benchmark with llama.cpp
    $0 --model models/llama-7b.gguf --framework llama-cpp --tasks perplexity

    # Use specific hardware profile
    $0 --model gpt2 --profile apple-m4-max-48gb

    # Dry run to see commands
    $0 --model gpt2 --tasks hellaswag --dry-run

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -m|--model)
                MODEL="$2"
                shift 2
                ;;
            -t|--tasks)
                TASKS="$2"
                shift 2
                ;;
            -f|--framework)
                FRAMEWORK="$2"
                shift 2
                ;;
            -o|--output)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            -c|--config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            -p|--profile)
                HARDWARE_PROFILE="$2"
                shift 2
                ;;
            --wandb-project)
                WANDB_PROJECT="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -n|--dry-run)
                DRY_RUN=true
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
}

# Validate inputs
validate_inputs() {
    if [[ -z "$MODEL" ]]; then
        echo -e "${RED}Error: Model path or identifier is required${NC}"
        usage
        exit 1
    fi

    if [[ ! "$FRAMEWORK" =~ ^(lm-eval|llama-cpp|custom)$ ]]; then
        echo -e "${RED}Error: Invalid framework: $FRAMEWORK${NC}"
        echo "Valid options: lm-eval, llama-cpp, custom"
        exit 1
    fi

    # Create directories if they don't exist
    mkdir -p "$OUTPUT_DIR" "$LOG_DIR"
}

# Detect hardware if profile is auto
detect_hardware() {
    if [[ "$HARDWARE_PROFILE" == "auto" ]]; then
        echo -e "${BLUE}Detecting hardware...${NC}"
        
        # Check for Apple Silicon
        if [[ "$(uname -s)" == "Darwin" ]] && [[ "$(uname -m)" == "arm64" ]]; then
            # Try to determine specific model
            if command -v system_profiler &> /dev/null; then
                local chip_info=$(system_profiler SPHardwareDataType | grep "Chip" | head -1)
                if [[ "$chip_info" =~ "M4 Max" ]]; then
                    HARDWARE_PROFILE="apple-m4-max"
                elif [[ "$chip_info" =~ "M4" ]]; then
                    HARDWARE_PROFILE="apple-m4"
                elif [[ "$chip_info" =~ "M3" ]]; then
                    HARDWARE_PROFILE="apple-m3"
                elif [[ "$chip_info" =~ "M2" ]]; then
                    HARDWARE_PROFILE="apple-m2"
                elif [[ "$chip_info" =~ "M1" ]]; then
                    HARDWARE_PROFILE="apple-m1"
                else
                    HARDWARE_PROFILE="apple-silicon"
                fi
            else
                HARDWARE_PROFILE="apple-silicon"
            fi
        # Check for NVIDIA GPU
        elif command -v nvidia-smi &> /dev/null; then
            HARDWARE_PROFILE="nvidia-gpu"
        # Default to CPU
        else
            HARDWARE_PROFILE="cpu"
        fi
        
        echo -e "${GREEN}Detected hardware profile: $HARDWARE_PROFILE${NC}"
    fi
}

# Load configuration
load_config() {
    local config_path=""
    
    # Check for config file in order of precedence
    if [[ -n "$CONFIG_FILE" ]] && [[ -f "$CONFIG_FILE" ]]; then
        config_path="$CONFIG_FILE"
    elif [[ -f "$PROJECT_ROOT/config/benchmark.yaml" ]]; then
        config_path="$PROJECT_ROOT/config/benchmark.yaml"
    elif [[ -f "$PROJECT_ROOT/bench/config/default.yaml" ]]; then
        config_path="$PROJECT_ROOT/bench/config/default.yaml"
    fi
    
    if [[ -n "$config_path" ]]; then
        echo -e "${BLUE}Loading configuration from: $config_path${NC}"
        # TODO: Implement YAML parsing
    fi
}

# Setup environment
setup_environment() {
    echo -e "${BLUE}Setting up environment...${NC}"
    
    # Load .env if exists
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        source "$PROJECT_ROOT/.env"
    fi
    
    # Set up Weights & Biases if available
    if command -v wandb &> /dev/null && [[ -n "${WANDB_API_KEY:-}" ]]; then
        export WANDB_PROJECT="$WANDB_PROJECT"
        echo -e "${GREEN}Weights & Biases tracking enabled${NC}"
    else
        echo -e "${YELLOW}Weights & Biases not configured${NC}"
    fi
    
    # Set timestamp for this run
    export RUN_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    export RUN_ID="${FRAMEWORK}_${RUN_TIMESTAMP}"
}

# Run lm-evaluation-harness
run_lm_eval() {
    echo -e "${BLUE}Running lm-evaluation-harness...${NC}"
    
    local cmd="lm_eval --model hf --model_args pretrained=$MODEL"
    cmd="$cmd --tasks $TASKS"
    cmd="$cmd --output_path $OUTPUT_DIR/lm-eval_${RUN_TIMESTAMP}"
    cmd="$cmd --log_samples"
    
    if [[ "$VERBOSE" == "true" ]]; then
        cmd="$cmd --verbosity DEBUG"
    fi
    
    echo -e "${YELLOW}Command: $cmd${NC}"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        eval "$cmd" 2>&1 | tee "$LOG_DIR/lm-eval_${RUN_TIMESTAMP}.log"
    fi
}

# Run llama.cpp benchmark
run_llama_cpp() {
    echo -e "${BLUE}Running llama.cpp benchmark...${NC}"
    
    # Check if llama.cpp is available
    local llama_path="$PROJECT_ROOT/llama.cpp/build/bin/llama-cli"
    if [[ ! -f "$llama_path" ]]; then
        echo -e "${RED}Error: llama.cpp not found at $llama_path${NC}"
        echo "Please build llama.cpp first"
        exit 1
    fi
    
    local cmd="$llama_path --model $MODEL"
    
    # Add hardware-specific flags
    case "$HARDWARE_PROFILE" in
        apple-*)
            cmd="$cmd --n-gpu-layers -1"  # Use Metal
            ;;
        nvidia-gpu)
            cmd="$cmd --n-gpu-layers 99"  # Use CUDA
            ;;
    esac
    
    # Add task-specific parameters
    if [[ "$TASKS" == "perplexity" ]]; then
        cmd="$cmd --perplexity --ppl-stride 1"
    else
        cmd="$cmd --prompt \"Test prompt for benchmarking\""
    fi
    
    echo -e "${YELLOW}Command: $cmd${NC}"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        eval "$cmd" 2>&1 | tee "$LOG_DIR/llama-cpp_${RUN_TIMESTAMP}.log"
    fi
}

# Run custom benchmark
run_custom() {
    echo -e "${BLUE}Running custom benchmark...${NC}"
    
    local script="$PROJECT_ROOT/bench/scripts/custom_benchmark.py"
    if [[ ! -f "$script" ]]; then
        echo -e "${RED}Error: Custom benchmark script not found at $script${NC}"
        exit 1
    fi
    
    local cmd="python $script --model $MODEL --tasks $TASKS"
    cmd="$cmd --output-dir $OUTPUT_DIR/custom_${RUN_TIMESTAMP}"
    
    echo -e "${YELLOW}Command: $cmd${NC}"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        eval "$cmd" 2>&1 | tee "$LOG_DIR/custom_${RUN_TIMESTAMP}.log"
    fi
}

# Generate report
generate_report() {
    echo -e "${BLUE}Generating benchmark report...${NC}"
    
    local report_file="$OUTPUT_DIR/report_${RUN_TIMESTAMP}.md"
    
    cat > "$report_file" << EOF
# Benchmark Report

**Run ID**: $RUN_ID
**Timestamp**: $(date)
**Model**: $MODEL
**Tasks**: $TASKS
**Framework**: $FRAMEWORK
**Hardware Profile**: $HARDWARE_PROFILE

## Results

EOF
    
    # TODO: Parse and add actual results
    
    echo -e "${GREEN}Report generated: $report_file${NC}"
}

# Main execution
main() {
    echo -e "${GREEN}=== SND-Bench Orchestrator ===${NC}"
    
    parse_args "$@"
    validate_inputs
    detect_hardware
    load_config
    setup_environment
    
    # Run appropriate benchmark
    case "$FRAMEWORK" in
        lm-eval)
            run_lm_eval
            ;;
        llama-cpp)
            run_llama_cpp
            ;;
        custom)
            run_custom
            ;;
    esac
    
    # Generate report
    generate_report
    
    echo -e "${GREEN}Benchmark complete!${NC}"
    echo -e "Results saved to: $OUTPUT_DIR"
    echo -e "Logs saved to: $LOG_DIR"
}

# Run main function
main "$@"