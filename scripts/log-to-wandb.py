#!/usr/bin/env python3
"""
Log benchmark results to Weights & Biases
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
import wandb
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def log_results_to_wandb(data_file, project, entity=None, run_id=None):
    """
    Log benchmark results to W&B
    
    Args:
        data_file: Path to the data.json file
        project: W&B project name
        entity: W&B entity (optional)
        run_id: Specific run ID to use (optional)
    """
    # Load data
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    # Extract key information
    model_name = data.get("model", {}).get("name", "unknown")
    tasks = data.get("tasks", [])
    results = data.get("results", {})
    avg_accuracy = data.get("average_accuracy", 0.0)
    hardware = data.get("hardware_profile", "unknown")
    
    # Initialize W&B run
    run = wandb.init(
        project=project,
        entity=entity,
        id=run_id or data.get("run_id"),
        resume="allow",
        config={
            "model": model_name,
            "tasks": tasks,
            "hardware": hardware,
            "framework": data.get("framework", "lm-eval"),
            "timestamp": data.get("timestamp", datetime.now().isoformat())
        }
    )
    
    # Log metrics
    metrics = {
        "average_accuracy": avg_accuracy,
        "total_tasks": len(tasks)
    }
    
    # Log individual task results
    for task, task_results in results.items():
        if isinstance(task_results, dict):
            if task_results.get("accuracy") is not None:
                metrics[f"{task}/accuracy"] = task_results["accuracy"]
            if task_results.get("stderr") is not None:
                metrics[f"{task}/stderr"] = task_results["stderr"]
            if task_results.get("acc_norm") is not None:
                metrics[f"{task}/acc_norm"] = task_results["acc_norm"]
            if task_results.get("acc_norm_stderr") is not None:
                metrics[f"{task}/acc_norm_stderr"] = task_results["acc_norm_stderr"]
    
    # Log all metrics
    wandb.log(metrics)
    
    # Log summary
    run.summary["average_accuracy"] = avg_accuracy
    run.summary["model"] = model_name
    run.summary["tasks"] = tasks
    run.summary["hardware"] = hardware
    run.summary["completed"] = data.get("completed", False)
    
    # Save the full data as an artifact
    artifact = wandb.Artifact(
        name=f"benchmark-results-{data.get('run_id', 'unknown')}",
        type="benchmark-results"
    )
    artifact.add_file(data_file)
    run.log_artifact(artifact)
    
    # Finish the run
    run.finish()
    
    logger.info(f"Results logged to W&B: {run.url}")
    return run.url


def main():
    parser = argparse.ArgumentParser(
        description="Log benchmark results to Weights & Biases"
    )
    parser.add_argument(
        "--data-file", "-d",
        required=True,
        help="Path to data.json file"
    )
    parser.add_argument(
        "--project", "-p",
        default=os.getenv("WANDB_PROJECT", "llm-bench"),
        help="W&B project name"
    )
    parser.add_argument(
        "--entity", "-e",
        default=os.getenv("WANDB_ENTITY"),
        help="W&B entity (username or team)"
    )
    parser.add_argument(
        "--run-id", "-r",
        help="Specific run ID to use"
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("WANDB_API_KEY"),
        help="W&B API key"
    )
    
    args = parser.parse_args()
    
    # Check for API key
    if not args.api_key:
        logger.error("W&B API key not found. Set WANDB_API_KEY environment variable or use --api-key")
        sys.exit(1)
    
    # Set API key
    os.environ["WANDB_API_KEY"] = args.api_key
    
    # Check if data file exists
    if not Path(args.data_file).exists():
        logger.error(f"Data file not found: {args.data_file}")
        sys.exit(1)
    
    try:
        url = log_results_to_wandb(
            args.data_file,
            args.project,
            args.entity,
            args.run_id
        )
        logger.info(f"Successfully logged to W&B: {url}")
    except Exception as e:
        logger.error(f"Failed to log to W&B: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()