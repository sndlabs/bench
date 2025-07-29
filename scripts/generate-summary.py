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
    summary_parts.append(f"# Benchmark Summary - {results_data.get('run_id', 'Unknown')}")
    summary_parts.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Model info
    model_info = results_data.get('model', {})
    summary_parts.append(f"\n## Model: {model_info.get('name', 'Unknown')}")
    
    # Results summary
    results = results_data.get('results', {})
    if results:
        summary_parts.append("\n## Results Overview")
        summary_parts.append(f"- **Tasks evaluated:** {len(results)}")
        summary_parts.append(f"- **Average accuracy:** {results_data.get('average_accuracy', 0):.4f}")
        
        summary_parts.append("\n### Task Performance:")
        for task, metrics in results.items():
            # Handle different metric formats
            accuracy = metrics.get('accuracy') or metrics.get('acc') or metrics.get('acc,none', 0)
            stderr = metrics.get('stderr') or metrics.get('acc_stderr') or metrics.get('acc_stderr,none', 0)
            summary_parts.append(f"- **{task}:** {accuracy:.4f} (±{stderr:.4f})")
    
    # W&B integration
    if wandb_data:
        summary_parts.append("\n## W&B Integration")
        if isinstance(wandb_data, list) and len(wandb_data) > 0:
            run = wandb_data[0]  # Latest run
            summary_parts.append(f"- **W&B Run:** [{run.get('name')}]({run.get('url', '#')})")
            summary_parts.append(f"- **Project:** {run.get('project', 'Unknown')}")
            
            # System metrics
            system_metrics = run.get('system_metrics', {})
            if system_metrics:
                summary_parts.append("\n### System Metrics:")
                summary_parts.append(f"- **Runtime:** {system_metrics.get('runtime', 0):.2f}s")
                summary_parts.append(f"- **GPU Count:** {system_metrics.get('gpu_count', 0)}")
                summary_parts.append(f"- **CPU Count:** {system_metrics.get('cpu_count', 0)}")
    
    # Performance insights
    summary_parts.append("\n## Key Insights")
    
    # Analyze performance
    if results:
        def get_accuracy(task_metrics):
            return task_metrics[1].get('accuracy') or task_metrics[1].get('acc') or task_metrics[1].get('acc,none', 0)
        
        best_task = max(results.items(), key=get_accuracy)
        worst_task = min(results.items(), key=get_accuracy)
        
        best_acc = get_accuracy(best_task)
        worst_acc = get_accuracy(worst_task)
        
        summary_parts.append(f"- **Best performance:** {best_task[0]} ({best_acc:.4f})")
        summary_parts.append(f"- **Needs improvement:** {worst_task[0]} ({worst_acc:.4f})")
    
    # Hardware utilization
    summary_parts.append(f"\n## Hardware Profile: {results_data.get('hardware_profile', 'Unknown')}")
    
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
