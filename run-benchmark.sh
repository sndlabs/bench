#!/bin/bash

# SND-Bench Interactive Benchmark Orchestrator
# This script provides an interactive menu for running benchmarks with W&B integration and AI summaries

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d "$PROJECT_ROOT/venv" ]; then
    echo "Activating virtual environment..."
    source "$PROJECT_ROOT/venv/bin/activate"
    # Ensure venv bin is in PATH
    export PATH="$PROJECT_ROOT/venv/bin:$PATH"
else
    echo "Warning: Virtual environment not found. Run ./setup-venv.sh to create it."
    echo "Continuing without virtual environment..."
fi

# Load environment variables
if [[ -f "$PROJECT_ROOT/.env" ]]; then
    source "$PROJECT_ROOT/.env"
fi

# Default values
MODEL=""
TASKS=""
FRAMEWORK="lm-eval"
OUTPUT_DIR="$PROJECT_ROOT/results"
LOG_DIR="$PROJECT_ROOT/logs"
RUNS_DIR="$PROJECT_ROOT/runs"
CONFIG_FILE=""
HARDWARE_PROFILE="auto"
WANDB_PROJECT="${WANDB_PROJECT:-snd-bench}"
VERBOSE=false
DRY_RUN=false
COMPARE_MODELS=""
SKIP_DEPLOY=false
DEBUG_API=false
INTERACTIVE_MODE=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    if [[ "$VERBOSE" == "true" ]] || [[ "$DEBUG_API" == "true" ]]; then
        echo -e "${MAGENTA}[DEBUG]${NC} $1"
    fi
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

SND-Bench: Enhanced Language Model Benchmarking Framework with W&B Integration

OPTIONS:
    -m, --model PATH         Path to model file or model identifier (required)
    -t, --tasks TASKS        Comma-separated list of evaluation tasks (default: hellaswag)
    -f, --framework NAME     Evaluation framework to use (default: lm-eval)
                            Options: lm-eval, llama-cpp, custom
    -o, --output DIR        Output directory for results (default: ./results)
    -c, --config FILE       Configuration file path
    -p, --profile NAME      Hardware profile (default: auto)
    --wandb-project NAME    Weights & Biases project name (default: snd-bench)
    --compare MODELS        Compare with other models (comma-separated list)
    --skip-deploy          Skip deployment to GitHub Pages
    --debug-api            Enable detailed API debugging logs
    -v, --verbose          Enable verbose output
    -n, --dry-run          Show what would be executed without running
    -h, --help             Show this help message

EXAMPLES:
    # Basic benchmark with lm-evaluation-harness
    $0 --model gpt2 --tasks hellaswag,arc_easy

    # Benchmark with llama.cpp and W&B tracking
    $0 --model models/llama-7b.gguf --framework llama-cpp --tasks perplexity

    # Compare multiple models
    $0 --model gpt2 --compare "gpt2-medium,gpt2-large" --tasks hellaswag

    # Debug API issues
    $0 --model gpt2 --tasks hellaswag --debug-api

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -m|--model)
                MODEL="$2"
                INTERACTIVE_MODE=false
                shift 2
                ;;
            -t|--tasks)
                TASKS="$2"
                INTERACTIVE_MODE=false
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
            --compare)
                COMPARE_MODELS="$2"
                shift 2
                ;;
            --skip-deploy)
                SKIP_DEPLOY=true
                shift
                ;;
            --debug-api)
                DEBUG_API=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -n|--dry-run)
                DRY_RUN=true
                shift
                ;;
            --non-interactive)
                INTERACTIVE_MODE=false
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown option $1"
                usage
                exit 1
                ;;
        esac
    done
}

# Interactive menu for model selection
select_model() {
    echo -e "\n${CYAN}=== Model Selection ===${NC}"
    echo "Select a model or enter a custom path:"
    echo "1) gpt2"
    echo "2) gpt2-medium"
    echo "3) gpt2-large"
    echo "4) gpt2-xl"
    echo "5) EleutherAI/pythia-70m"
    echo "6) EleutherAI/pythia-160m"
    echo "7) EleutherAI/pythia-410m"
    echo "8) EleutherAI/pythia-1b"
    echo "9) meta-llama/Llama-2-7b-hf"
    echo "10) mistralai/Mistral-7B-v0.1"
    echo "11) Custom model (enter path)"
    echo -n "Enter your choice (1-11): "
    
    read choice
    case $choice in
        1) MODEL="gpt2" ;;
        2) MODEL="gpt2-medium" ;;
        3) MODEL="gpt2-large" ;;
        4) MODEL="gpt2-xl" ;;
        5) MODEL="EleutherAI/pythia-70m" ;;
        6) MODEL="EleutherAI/pythia-160m" ;;
        7) MODEL="EleutherAI/pythia-410m" ;;
        8) MODEL="EleutherAI/pythia-1b" ;;
        9) MODEL="meta-llama/Llama-2-7b-hf" ;;
        10) MODEL="mistralai/Mistral-7B-v0.1" ;;
        11)
            echo -n "Enter custom model path or HuggingFace ID: "
            read MODEL
            ;;
        *)
            log_error "Invalid choice"
            exit 1
            ;;
    esac
    
    log_info "Selected model: $MODEL"
}

# Interactive menu for task selection
select_tasks() {
    echo -e "\n${CYAN}=== Task Selection ===${NC}"
    echo "Select benchmark tasks:"
    echo ""
    echo "${YELLOW}Korean Language Understanding:${NC}"
    echo "1) kmmlu - Korean MMLU (대규모 다중 과제 언어 이해)"
    echo "2) haerae - HAE-RAE Benchmark (한국어 이해 평가)"
    echo ""
    echo "${GREEN}Instruction Following:${NC}"
    echo "3) ifeval - Instruction Following Evaluation"
    echo ""
    echo "${MAGENTA}Quick Sets:${NC}"
    echo "4) All Tasks (kmmlu,haerae,ifeval)"
    echo "5) Korean Only (kmmlu,haerae)"
    echo "6) Custom (enter comma-separated task names)"
    echo ""
    echo -n "Enter your choice (1-6): "
    
    read choices
    
    # Task mapping using case statement for compatibility
    get_task_by_number() {
        case $1 in
            1) echo "kmmlu" ;;
            2) echo "haerae" ;;
            3) echo "ifeval" ;;
            4) echo "kmmlu,haerae,ifeval" ;;
            5) echo "kmmlu,haerae" ;;
            *) echo "" ;;
        esac
    }
    
    if [[ "$choices" == "6" ]]; then
        echo -n "Enter custom task names (comma-separated): "
        read TASKS
    else
        TASKS=""
        IFS=',' read -ra CHOICE_ARRAY <<< "$choices"
        for choice in "${CHOICE_ARRAY[@]}"; do
            choice=$(echo $choice | tr -d ' ')
            task_value=$(get_task_by_number "$choice")
            if [[ -n "$task_value" ]]; then
                if [[ -z "$TASKS" ]]; then
                    TASKS="$task_value"
                else
                    # Avoid duplicates when using quick sets
                    for task in $(echo "$task_value" | tr ',' ' '); do
                        if [[ ! ",$TASKS," =~ ",$task," ]]; then
                            TASKS="$TASKS,$task"
                        fi
                    done
                fi
            else
                log_error "Invalid choice: $choice"
                exit 1
            fi
        done
    fi
    
    log_info "Selected tasks: $TASKS"
}

# Interactive menu for framework selection
select_framework() {
    echo -e "\n${CYAN}=== Framework Selection ===${NC}"
    echo "Select evaluation framework:"
    echo "1) lm-evaluation-harness (recommended for most models)"
    echo "2) llama.cpp (for GGUF models with Metal/CUDA)"
    echo "3) Custom framework"
    echo -n "Enter your choice (1-3) [default: 1]: "
    
    read choice
    case ${choice:-1} in
        1) FRAMEWORK="lm-eval" ;;
        2) FRAMEWORK="llama-cpp" ;;
        3) FRAMEWORK="custom" ;;
        *)
            log_error "Invalid choice"
            exit 1
            ;;
    esac
    
    log_info "Selected framework: $FRAMEWORK"
}

# Interactive menu for additional options
select_options() {
    echo -e "\n${CYAN}=== Additional Options ===${NC}"
    
    # W&B integration
    if [[ -n "${WANDB_API_KEY:-}" ]]; then
        echo "Weights & Biases integration is available."
    else
        echo "${YELLOW}Weights & Biases API key not found in environment.${NC}"
    fi
    
    # GitHub Pages deployment
    echo -n "Deploy results to GitHub Pages? (y/N): "
    read deploy_choice
    if [[ "$deploy_choice" =~ ^[Yy]$ ]]; then
        SKIP_DEPLOY=false
        if [[ -z "${GITHUB_TOKEN:-}" ]]; then
            echo "${YELLOW}Warning: GITHUB_TOKEN not set. Deployment may fail.${NC}"
        fi
    else
        SKIP_DEPLOY=true
    fi
    
    # Verbose mode
    echo -n "Enable verbose output? (y/N): "
    read verbose_choice
    if [[ "$verbose_choice" =~ ^[Yy]$ ]]; then
        VERBOSE=true
    fi
    
    # Dry run
    echo -n "Perform dry run (show commands without executing)? (y/N): "
    read dryrun_choice
    if [[ "$dryrun_choice" =~ ^[Yy]$ ]]; then
        DRY_RUN=true
    fi
}

# Interactive mode runner
run_interactive() {
    echo -e "${GREEN}=== SND-Bench Interactive Mode ===${NC}"
    echo "Welcome to the SND-Bench benchmarking framework!"
    echo ""
    
    # Check for required dependencies first
    check_dependencies
    
    # Model selection
    select_model
    
    # Task selection
    select_tasks
    
    # Framework selection
    select_framework
    
    # Additional options
    select_options
    
    # Show summary
    echo -e "\n${CYAN}=== Configuration Summary ===${NC}"
    echo "Model: $MODEL"
    echo "Tasks: $TASKS"
    echo "Framework: $FRAMEWORK"
    echo "W&B Project: $WANDB_PROJECT"
    echo "Deploy to GitHub Pages: $([ "$SKIP_DEPLOY" = "false" ] && echo "Yes" || echo "No")"
    echo "Verbose: $VERBOSE"
    echo "Dry Run: $DRY_RUN"
    echo ""
    
    echo -n "Proceed with benchmark? (Y/n): "
    read proceed
    if [[ "$proceed" =~ ^[Nn]$ ]]; then
        log_info "Benchmark cancelled by user"
        exit 0
    fi
}

# Validate inputs
validate_inputs() {
    if [[ -z "$MODEL" ]]; then
        log_error "Model path or identifier is required"
        usage
        exit 1
    fi
    
    if [[ -z "$TASKS" ]]; then
        log_error "No tasks selected"
        exit 1
    fi

    if [[ ! "$FRAMEWORK" =~ ^(lm-eval|llama-cpp|custom)$ ]]; then
        log_error "Invalid framework: $FRAMEWORK"
        echo "Valid options: lm-eval, llama-cpp, custom"
        exit 1
    fi

    # Create directories if they don't exist
    mkdir -p "$OUTPUT_DIR" "$LOG_DIR" "$RUNS_DIR"
}

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    local missing_deps=()
    
    # Check for required commands
    for cmd in python3 git jq; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    # Check for W&B
    if ! python3 -c "import wandb" 2>/dev/null; then
        log_warning "Weights & Biases not installed. Install with: pip install wandb"
    fi
    
    # Check for lm_eval
    if [[ "$FRAMEWORK" == "lm-eval" ]] && ! command -v lm_eval &> /dev/null; then
        log_warning "lm-evaluation-harness not found. Install with: pip install lm-eval"
    fi
    
    # Check for llama.cpp
    if [[ "$FRAMEWORK" == "llama-cpp" ]]; then
        local llama_path="$PROJECT_ROOT/llama.cpp/build/bin/llama-cli"
        if [[ ! -f "$llama_path" ]]; then
            log_warning "llama.cpp not found at $llama_path"
        fi
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        exit 1
    fi
    
    log_success "All required dependencies found"
}

# Detect hardware if profile is auto
detect_hardware() {
    if [[ "$HARDWARE_PROFILE" == "auto" ]]; then
        log_info "Detecting hardware..."
        
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
        
        log_success "Detected hardware profile: $HARDWARE_PROFILE"
    fi
}

# Setup environment
setup_environment() {
    log_info "Setting up environment..."
    
    # Set up Weights & Biases if available
    if command -v wandb &> /dev/null && [[ -n "${WANDB_API_KEY:-}" ]]; then
        export WANDB_PROJECT="$WANDB_PROJECT"
        export WANDB_MODE="${WANDB_MODE:-online}"
        log_success "Weights & Biases tracking enabled (project: $WANDB_PROJECT)"
    else
        log_warning "Weights & Biases not configured (WANDB_API_KEY not set)"
    fi
    
    # Set timestamp for this run
    export RUN_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    export RUN_ID="${FRAMEWORK}_${RUN_TIMESTAMP}"
    export RUN_DIR="$RUNS_DIR/$RUN_ID"
    
    # Create run directory
    mkdir -p "$RUN_DIR"
    
    log_info "Run ID: $RUN_ID"
    log_info "Run directory: $RUN_DIR"
}

# Run lm-evaluation-harness
run_lm_eval() {
    log_info "Running lm-evaluation-harness..."
    
    local output_path="$OUTPUT_DIR/lm-eval_${RUN_TIMESTAMP}"
    
    # Detect device - use MPS for Apple Silicon, CUDA for NVIDIA, CPU as fallback
    local device="cpu"
    if [[ "$HARDWARE_PROFILE" == *"apple"* ]] || [[ "$(uname -m)" == "arm64" ]]; then
        # Check if MPS is available
        if python -c "import torch; print(torch.backends.mps.is_available())" 2>/dev/null | grep -q "True"; then
            device="mps"
            log_info "Using Metal Performance Shaders (MPS) for Apple Silicon"
        else
            device="cpu"
            log_info "MPS not available, using CPU"
        fi
    elif command -v nvidia-smi &> /dev/null; then
        device="cuda"
        log_info "Using CUDA for GPU acceleration"
    fi
    
    local cmd="lm_eval --model hf --model_args pretrained=$MODEL,device=$device"
    cmd="$cmd --tasks $TASKS"
    cmd="$cmd --output_path $output_path"
    cmd="$cmd --log_samples"
    
    if [[ "$VERBOSE" == "true" ]]; then
        cmd="$cmd --verbosity DEBUG"
    fi
    
    # Note: W&B integration in lm-eval has changed
    # The newer versions may handle W&B tracking differently
    # For now, we'll rely on environment variables for W&B tracking
    if [[ -n "${WANDB_API_KEY:-}" ]]; then
        log_info "W&B tracking will use environment variables (WANDB_PROJECT=$WANDB_PROJECT)"
        export WANDB_PROJECT=$WANDB_PROJECT
        export WANDB_RUN_ID=$RUN_ID
        export WANDB_RUN_NAME=$RUN_ID
    fi
    
    log_info "Command: $cmd"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        eval "$cmd" 2>&1 | tee "$LOG_DIR/lm-eval_${RUN_TIMESTAMP}.log"
        
        # Copy results to run directory
        if [[ -d "$output_path" ]]; then
            cp -r "$output_path"/* "$RUN_DIR/"
        fi
    fi
}

# Run llama.cpp benchmark
run_llama_cpp() {
    log_info "Running llama.cpp benchmark..."
    
    # Check if llama.cpp is available
    local llama_path="$PROJECT_ROOT/llama.cpp/build/bin/llama-cli"
    if [[ ! -f "$llama_path" ]]; then
        log_error "llama.cpp not found at $llama_path"
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
    
    log_info "Command: $cmd"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        eval "$cmd" 2>&1 | tee "$LOG_DIR/llama-cpp_${RUN_TIMESTAMP}.log"
    fi
}

# Process results and generate data.json
process_results() {
    log_info "Processing benchmark results..."
    
    local results_file="$RUN_DIR/results.json"
    local data_file="$RUN_DIR/data.json"
    
    # Find the actual results file from lm-eval
    if [[ "$FRAMEWORK" == "lm-eval" ]]; then
        # Look for results_*.json files in the model subdirectory
        local lm_eval_results=$(find "$OUTPUT_DIR/lm-eval_${RUN_TIMESTAMP}" -name "results_*.json" -type f | head -1)
        if [[ -f "$lm_eval_results" ]]; then
            cp "$lm_eval_results" "$results_file"
            log_info "Found lm-eval results at: $lm_eval_results"
        else
            # Try the old format too
            lm_eval_results=$(find "$OUTPUT_DIR/lm-eval_${RUN_TIMESTAMP}" -name "results.json" -type f | head -1)
            if [[ -f "$lm_eval_results" ]]; then
                cp "$lm_eval_results" "$results_file"
                log_info "Found lm-eval results at: $lm_eval_results"
            else
                log_warning "No results.json or results_*.json found from lm-eval"
                # Create a dummy results file
                echo '{"results": {}, "config": {}}' > "$results_file"
            fi
        fi
    fi
    
    # Process results and create data.json
    python3 "$PROJECT_ROOT/scripts/process-single-run.py" \
        --input "$results_file" \
        --output "$data_file" \
        --run-id "$RUN_ID" \
        --model "$MODEL" \
        --tasks "$TASKS" \
        --framework "$FRAMEWORK" \
        --hardware "$HARDWARE_PROFILE"
    
    log_success "Results processed and saved to $data_file"
}

# Log results to W&B
log_to_wandb() {
    log_info "Logging results to Weights & Biases..."
    
    if [[ -z "${WANDB_API_KEY:-}" ]]; then
        log_warning "WANDB_API_KEY not set, skipping W&B logging"
        return 0
    fi
    
    local data_file="$RUN_DIR/data.json"
    
    if [[ ! -f "$data_file" ]]; then
        log_error "No data.json found at $data_file"
        return 1
    fi
    
    # Run W&B logging script
    local cmd="python3 $PROJECT_ROOT/scripts/log-to-wandb.py"
    cmd="$cmd --data-file $data_file"
    cmd="$cmd --project $WANDB_PROJECT"
    cmd="$cmd --run-id $RUN_ID"
    
    if [[ -n "${WANDB_ENTITY:-}" ]]; then
        cmd="$cmd --entity $WANDB_ENTITY"
    fi
    
    log_debug "Command: $cmd"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        if eval "$cmd"; then
            log_success "Results logged to W&B successfully"
        else
            log_warning "Failed to log results to W&B (continuing anyway)"
            # Don't fail the entire benchmark just because W&B logging failed
            return 0
        fi
    fi
    
    return 0
}

# Generate AI summary
generate_summary() {
    log_info "Generating AI summary..."
    
    local data_file="$RUN_DIR/data.json"
    local wandb_file="$RUN_DIR/wandb_data.json"
    local summary_file="$RUN_DIR/summary.md"
    
    if [[ ! -f "$data_file" ]]; then
        log_error "No data.json found at $data_file"
        return 1
    fi
    
    # Check if AI summary script exists, if not create it
    local summary_script="$PROJECT_ROOT/scripts/generate-summary.py"
    if [[ ! -f "$summary_script" ]]; then
        log_warning "AI summary script not found, creating basic version..."
        create_ai_summary_script "$summary_script"
    fi
    
    # Run AI summary generation
    local cmd="python3 $summary_script"
    cmd="$cmd --results $data_file"
    
    # Add W&B data if available
    if [[ -f "$wandb_file" ]]; then
        cmd="$cmd --wandb-data $wandb_file"
    fi
    
    cmd="$cmd --output $summary_file"
    
    if [[ "$DEBUG_API" == "true" ]]; then
        cmd="$cmd --debug"
    fi
    
    log_debug "Command: $cmd"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        if eval "$cmd"; then
            log_success "AI summary generated successfully"
            
            # Append summary to data.json
            if [[ -f "$summary_file" ]]; then
                local summary_content=$(cat "$summary_file" | jq -Rs .)
                jq --arg summary "$summary_content" '. + {summary: $summary}' "$data_file" > "$data_file.tmp"
                mv "$data_file.tmp" "$data_file"
            fi
        else
            log_error "Failed to generate AI summary"
            # Don't fail the entire pipeline if summary fails
        fi
    fi
}

# Create basic AI summary script
create_ai_summary_script() {
    local script_path="$1"
    
    cat > "$script_path" << 'EOF'
#!/usr/bin/env python3
"""
AI Summary Generator for SND-Bench
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_summary(results_data, wandb_data=None, debug=False):
    """Generate AI summary from results and W&B data."""
    
    summary_parts = []
    
    # Header
    summary_parts.append(f"# 벤치마크 요약 - {results_data.get('run_id', 'Unknown')}")
    summary_parts.append(f"\n**생성 시간:** {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}")
    
    # Model info
    model_info = results_data.get('model', {})
    summary_parts.append(f"\n## 모델: {model_info.get('name', 'Unknown')}")
    
    # Results summary
    results = results_data.get('results', {})
    if results:
        summary_parts.append("\n## 결과 개요")
        summary_parts.append(f"- **평가된 작업 수:** {len(results)}개")
        summary_parts.append(f"- **평균 정확도:** {results_data.get('average_accuracy', 0):.4f}")
        
        summary_parts.append("\n### 작업별 성능:")
        for task, metrics in results.items():
            summary_parts.append(f"- **{task}:** {metrics.get('accuracy', 0):.4f} (±{metrics.get('stderr', 0):.4f})")
    
    # W&B integration
    if wandb_data:
        summary_parts.append("\n## W&B 연동")
        if isinstance(wandb_data, list) and len(wandb_data) > 0:
            run = wandb_data[0]  # Latest run
            summary_parts.append(f"- **W&B 실행:** [{run.get('name')}]({run.get('url', '#')})")
            summary_parts.append(f"- **프로젝트:** {run.get('project', 'Unknown')}")
            
            # System metrics
            system_metrics = run.get('system_metrics', {})
            if system_metrics:
                summary_parts.append("\n### 시스템 메트릭:")
                summary_parts.append(f"- **실행 시간:** {system_metrics.get('runtime', 0):.2f}초")
                summary_parts.append(f"- **GPU 개수:** {system_metrics.get('gpu_count', 0)}개")
                summary_parts.append(f"- **CPU 코어:** {system_metrics.get('cpu_count', 0)}개")
    
    # Performance insights
    summary_parts.append("\n## 주요 인사이트")
    
    # Analyze performance
    if results:
        best_task = max(results.items(), key=lambda x: x[1].get('accuracy', 0))
        worst_task = min(results.items(), key=lambda x: x[1].get('accuracy', 0))
        
        summary_parts.append(f"- **최고 성능:** {best_task[0]} ({best_task[1].get('accuracy', 0):.4f})")
        summary_parts.append(f"- **개선 필요:** {worst_task[0]} ({worst_task[1].get('accuracy', 0):.4f})")
    
    # Hardware utilization
    summary_parts.append(f"\n## 하드웨어 프로필: {results_data.get('hardware_profile', 'Unknown')}")
    
    return "\n".join(summary_parts)

def main():
    parser = argparse.ArgumentParser(description="Generate AI summary for benchmark results")
    parser.add_argument("--results", required=True, help="Path to results JSON file")
    parser.add_argument("--wandb-data", help="Path to W&B data JSON file")
    parser.add_argument("--output", required=True, help="Output path for summary")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load results
    with open(args.results, 'r') as f:
        results_data = json.load(f)
    
    # Load W&B data if provided
    wandb_data = None
    if args.wandb_data and Path(args.wandb_data).exists():
        with open(args.wandb_data, 'r') as f:
            wandb_data = json.load(f)
    
    # Generate summary
    summary = generate_summary(results_data, wandb_data, args.debug)
    
    # Save summary
    with open(args.output, 'w') as f:
        f.write(summary)
    
    logger.info(f"Summary saved to {args.output}")

if __name__ == "__main__":
    main()
EOF

    chmod +x "$script_path"
}

# Generate static site
generate_site() {
    log_info "Generating static site..."
    
    local wandb_data_file="$RUN_DIR/wandb_data.json"
    
    # Run site generation
    local cmd="python3 $PROJECT_ROOT/scripts/generate-site-with-wandb.py"
    cmd="$cmd --project-root $PROJECT_ROOT"
    
    if [[ -f "$wandb_data_file" ]]; then
        cmd="$cmd --wandb-data $wandb_data_file"
    fi
    
    if [[ "$VERBOSE" == "true" ]]; then
        cmd="$cmd --verbose"
    fi
    
    log_debug "Command: $cmd"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        eval "$cmd"
        log_success "Static site generated"
    fi
}

# Deploy to GitHub Pages (using docs/ folder)
deploy_to_pages() {
    if [[ "$SKIP_DEPLOY" == "true" ]]; then
        log_info "Skipping deployment (--skip-deploy flag set)"
        return 0
    fi
    
    log_info "Deploying to docs/ folder for GitHub Pages..."
    
    # Create docs folder if it doesn't exist
    mkdir -p "$PROJECT_ROOT/docs"
    
    # Copy site files to docs/
    log_debug "Copying site files to docs/..."
    cp -r "$PROJECT_ROOT"/index.html "$PROJECT_ROOT/docs/" 2>/dev/null || true
    cp -r "$PROJECT_ROOT"/runs "$PROJECT_ROOT/docs/" 2>/dev/null || true
    cp -r "$PROJECT_ROOT"/assets "$PROJECT_ROOT/docs/" 2>/dev/null || true
    cp -r "$PROJECT_ROOT"/metadata.json "$PROJECT_ROOT/docs/" 2>/dev/null || true
    cp -r "$PROJECT_ROOT"/runs-index.json "$PROJECT_ROOT/docs/" 2>/dev/null || true
    cp -r "$PROJECT_ROOT"/compare.html "$PROJECT_ROOT/docs/" 2>/dev/null || true
    cp -r "$PROJECT_ROOT"/service-worker.js "$PROJECT_ROOT/docs/" 2>/dev/null || true
    
    log_success "Site files copied to docs/ folder"
    log_info "Note: Configure GitHub Pages to serve from /docs folder in repository settings"
    log_info "Settings → Pages → Source → Deploy from a branch → Branch: main → Folder: /docs"
}

# Compare with other models
run_comparison() {
    if [[ -z "$COMPARE_MODELS" ]]; then
        return 0
    fi
    
    log_info "Running model comparison..."
    
    # TODO: Implement model comparison logic
    log_warning "Model comparison not yet implemented"
}

# Generate final report
generate_report() {
    log_info "Generating final report..."
    
    local report_file="$RUN_DIR/report.md"
    
    cat > "$report_file" << EOF
# Benchmark Report

**Run ID**: $RUN_ID
**Timestamp**: $(date)
**Model**: $MODEL
**Tasks**: $TASKS
**Framework**: $FRAMEWORK
**Hardware Profile**: $HARDWARE_PROFILE

## Results Summary

See data.json for detailed results.

## Logs

- Benchmark log: $LOG_DIR/${FRAMEWORK}_${RUN_TIMESTAMP}.log
- W&B data: $RUN_DIR/wandb_data.json
- AI summary: $RUN_DIR/summary.md

## Static Site

Results are available on the dashboard at index.html

EOF
    
    log_success "Report generated: $report_file"
}

# Main execution
main() {
    # Parse arguments first to check for non-interactive mode
    parse_args "$@"
    
    # Run interactive mode if no model/tasks specified via CLI
    if [[ "$INTERACTIVE_MODE" == "true" ]]; then
        run_interactive
    else
        echo -e "${GREEN}=== SND-Bench Enhanced Orchestrator ===${NC}"
        echo -e "Version: 2.0.0"
        echo ""
    fi
    
    # Validate inputs
    validate_inputs
    
    # Check dependencies
    check_dependencies
    
    # Detect hardware
    detect_hardware
    
    # Setup environment
    setup_environment
    
    # Run appropriate benchmark
    log_info "Starting benchmark with $FRAMEWORK..."
    case "$FRAMEWORK" in
        lm-eval)
            run_lm_eval
            ;;
        llama-cpp)
            run_llama_cpp
            ;;
        custom)
            log_error "Custom framework not yet implemented"
            exit 1
            ;;
    esac
    
    # Process results
    process_results
    
    # Log to W&B (before AI summary so it can use the data)
    log_to_wandb
    
    # Generate AI summary (always run, uses W&B data if available)
    generate_summary
    
    # Run model comparison if requested
    run_comparison
    
    # Generate static site
    generate_site
    
    # Deploy to GitHub Pages
    deploy_to_pages
    
    # Generate final report
    generate_report
    
    echo ""
    log_success "Benchmark complete!"
    log_info "Results saved to: $RUN_DIR"
    log_info "Logs saved to: $LOG_DIR"
    
    if [[ -f "$RUN_DIR/wandb_data.json" ]]; then
        log_info "W&B tracking data available"
    fi
    
    if [[ -f "$RUN_DIR/summary.md" ]]; then
        echo ""
        log_info "AI Summary:"
        echo "----------------------------------------"
        cat "$RUN_DIR/summary.md"
        echo "----------------------------------------"
    fi
}

# Run main function
main "$@"