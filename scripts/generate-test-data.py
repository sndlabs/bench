#!/usr/bin/env python3
"""Generate test data for the comparison page."""

import json
import os
from datetime import datetime, timedelta
import random

def generate_test_run(run_id, model_name, days_ago=0):
    """Generate a test run with mock data."""
    timestamp = datetime.now() - timedelta(days=days_ago)
    
    # Generate some mock metrics
    accuracy = random.uniform(0.6, 0.95)
    perplexity = random.uniform(5, 20)
    
    run_data = {
        "run_id": run_id,
        "timestamp": timestamp.isoformat(),
        "model": {
            "name": model_name,
            "path": f"/models/{model_name}",
            "size": f"{random.uniform(0.5, 13):.1f}G"
        },
        "results": {
            "hellaswag": {
                "accuracy": accuracy,
                "stderr": 0.02,
                "samples": 10042
            },
            "arc_easy": {
                "accuracy": accuracy + random.uniform(-0.1, 0.1),
                "stderr": 0.02,
                "samples": 2376
            }
        },
        "average_accuracy": accuracy,
        "total_tasks": 2,
        "wandb_history": [{
            "id": f"test{run_id}",
            "name": f"{model_name}-{run_id}",
            "created_at": timestamp.isoformat(),
            "url": f"https://wandb.ai/sndlabs/llm-bench/runs/test{run_id}",
            "model": model_name,
            "metrics": {
                "average_accuracy": accuracy,
                "model_size_gb": random.uniform(0.5, 13),
                "task_perplexity": perplexity
            }
        }],
        "summary": f"Test model {model_name} achieved {accuracy:.2%} accuracy with a perplexity of {perplexity:.2f}."
    }
    
    return run_data

def main():
    """Generate test data for multiple models."""
    models = [
        "llama-3-8b-q4_0.gguf",
        "llama-3-8b-q8_0.gguf",
        "mistral-7b-v0.3-q4_k_m.gguf",
        "qwen2.5-7b-instruct-q4_k_m.gguf",
        "phi-3-mini-4k-q4_k_m.gguf"
    ]
    
    # Create runs directory if it doesn't exist
    os.makedirs("runs", exist_ok=True)
    
    # Generate test runs
    for i, model in enumerate(models):
        run_id = f"test_{datetime.now().strftime('%Y%m%d')}_{i:03d}"
        run_dir = f"runs/{run_id}"
        os.makedirs(run_dir, exist_ok=True)
        
        # Generate run data
        run_data = generate_test_run(run_id, model, days_ago=i)
        
        # Save data.json
        with open(f"{run_dir}/data.json", "w") as f:
            json.dump(run_data, f, indent=2)
        
        print(f"Generated test data for {model} in {run_dir}")
    
    # Run aggregation to update metadata.json
    print("\nAggregating benchmark data...")
    os.system("python scripts/aggregate-benchmarks.py")
    
    print("\nTest data generation complete!")

if __name__ == "__main__":
    main()