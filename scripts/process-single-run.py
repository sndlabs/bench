#!/usr/bin/env python3
"""
Process a single benchmark run result and create data.json
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Process single benchmark run results")
    parser.add_argument("--input", required=True, help="Input results.json file")
    parser.add_argument("--output", required=True, help="Output data.json file")
    parser.add_argument("--run-id", required=True, help="Run ID")
    parser.add_argument("--model", required=True, help="Model name/path")
    parser.add_argument("--tasks", required=True, help="Comma-separated list of tasks")
    parser.add_argument("--framework", required=True, help="Framework used")
    parser.add_argument("--hardware", required=True, help="Hardware profile")
    
    args = parser.parse_args()
    
    # Load results if file exists
    results = {}
    if Path(args.input).exists():
        try:
            with open(args.input, 'r') as f:
                data = json.load(f)
                # Handle different result formats
                if 'results' in data:
                    results = data['results']
                else:
                    results = data
        except Exception as e:
            print(f"Warning: Could not load results from {args.input}: {e}")
    
    # Process results to standardized format
    processed_results = {}
    accuracies = []
    
    for task, metrics in results.items():
        if isinstance(metrics, dict):
            # Keep the raw metrics for compatibility
            processed_results[task] = metrics
            
            # Extract accuracy for average calculation
            for key in ['acc', 'accuracy', 'acc,none']:
                if key in metrics:
                    value = metrics[key]
                    if isinstance(value, (int, float)):
                        accuracies.append(value)
                        break
    
    avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
    
    # Create output data
    output_data = {
        "run_id": args.run_id,
        "timestamp": datetime.now().isoformat(),
        "model": {
            "name": args.model,
            "path": args.model
        },
        "framework": args.framework,
        "hardware_profile": args.hardware,
        "tasks": args.tasks.split(','),
        "total_tasks": len(args.tasks.split(',')),
        "results": processed_results,
        "average_accuracy": avg_accuracy,
        "completed": True
    }
    
    # Save output
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Processed results saved to {args.output}")
    print(f"Average accuracy: {avg_accuracy:.4f}")

if __name__ == "__main__":
    main()