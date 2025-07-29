#!/usr/bin/env python3
"""
Benchmark Data Aggregator for SND-Bench

This script scans all benchmark runs, aggregates data, and creates
unified metadata for comparison and analysis.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import statistics
from collections import defaultdict
import csv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BenchmarkAggregator:
    """Aggregates benchmark data from multiple runs."""
    
    def __init__(self, project_root: Path):
        """
        Initialize aggregator.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.runs_dir = self.project_root / "runs"
        self.all_runs = []
        self.model_stats = defaultdict(lambda: {
            "runs": [],
            "accuracies": [],
            "best_run": None,
            "worst_run": None,
            "avg_accuracy": 0,
            "std_accuracy": 0,
            "median_accuracy": 0,
            "total_runs": 0,
            "task_results": defaultdict(list)
        })
        self.task_stats = defaultdict(lambda: {
            "models": [],
            "accuracies": [],
            "avg_accuracy": 0,
            "std_accuracy": 0,
            "best_model": None,
            "worst_model": None
        })
    
    def load_run_data(self, run_dir: Path) -> Optional[Dict[str, Any]]:
        """Load data.json from a run directory."""
        data_file = run_dir / "data.json"
        if not data_file.exists():
            logger.warning(f"No data.json found in {run_dir}")
            return None
        
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
                # Add run directory for reference
                data["_run_dir"] = str(run_dir.name)
                return data
        except Exception as e:
            logger.error(f"Error loading {data_file}: {e}")
            return None
    
    def scan_all_runs(self):
        """Scan all run directories and load data."""
        logger.info(f"Scanning runs directory: {self.runs_dir}")
        
        for run_dir in sorted(self.runs_dir.iterdir()):
            if run_dir.is_dir():
                run_data = self.load_run_data(run_dir)
                if run_data:
                    self.all_runs.append(run_data)
                    logger.debug(f"Loaded run: {run_dir.name}")
        
        logger.info(f"Loaded {len(self.all_runs)} runs")
    
    def aggregate_data(self):
        """Aggregate data across all runs."""
        for run in self.all_runs:
            model_name = run.get("model", {}).get("name", "unknown")
            run_id = run.get("run_id", run.get("_run_dir", "unknown"))
            avg_accuracy = run.get("average_accuracy", 0)
            
            # Update model statistics
            model_stat = self.model_stats[model_name]
            model_stat["runs"].append(run_id)
            model_stat["accuracies"].append(avg_accuracy)
            model_stat["total_runs"] += 1
            
            # Track best and worst runs
            if model_stat["best_run"] is None or avg_accuracy > model_stat["best_run"]["accuracy"]:
                model_stat["best_run"] = {
                    "run_id": run_id,
                    "accuracy": avg_accuracy,
                    "timestamp": run.get("timestamp", "")
                }
            
            if model_stat["worst_run"] is None or avg_accuracy < model_stat["worst_run"]["accuracy"]:
                model_stat["worst_run"] = {
                    "run_id": run_id,
                    "accuracy": avg_accuracy,
                    "timestamp": run.get("timestamp", "")
                }
            
            # Aggregate task-level results
            for task_name, task_results in run.get("results", {}).items():
                task_accuracy = task_results.get("accuracy", 0)
                model_stat["task_results"][task_name].append(task_accuracy)
                
                # Update task statistics
                task_stat = self.task_stats[task_name]
                if model_name not in task_stat["models"]:
                    task_stat["models"].append(model_name)
                task_stat["accuracies"].append({
                    "model": model_name,
                    "accuracy": task_accuracy,
                    "run_id": run_id
                })
        
        # Calculate aggregate statistics
        self._calculate_statistics()
    
    def _calculate_statistics(self):
        """Calculate statistical measures for models and tasks."""
        # Model statistics
        for model_name, stats in self.model_stats.items():
            accuracies = stats["accuracies"]
            if accuracies:
                stats["avg_accuracy"] = statistics.mean(accuracies)
                stats["median_accuracy"] = statistics.median(accuracies)
                if len(accuracies) > 1:
                    stats["std_accuracy"] = statistics.stdev(accuracies)
                else:
                    stats["std_accuracy"] = 0
                
                # Calculate task-level averages
                for task_name, task_accuracies in stats["task_results"].items():
                    if task_accuracies:
                        stats["task_results"][task_name] = {
                            "avg": statistics.mean(task_accuracies),
                            "std": statistics.stdev(task_accuracies) if len(task_accuracies) > 1 else 0,
                            "samples": len(task_accuracies)
                        }
        
        # Task statistics
        for task_name, stats in self.task_stats.items():
            if stats["accuracies"]:
                # Group by model for averages
                model_accuracies = defaultdict(list)
                for item in stats["accuracies"]:
                    model_accuracies[item["model"]].append(item["accuracy"])
                
                # Calculate overall task statistics
                all_accuracies = [item["accuracy"] for item in stats["accuracies"]]
                stats["avg_accuracy"] = statistics.mean(all_accuracies)
                if len(all_accuracies) > 1:
                    stats["std_accuracy"] = statistics.stdev(all_accuracies)
                
                # Find best and worst performing models
                model_avgs = {
                    model: statistics.mean(accs) 
                    for model, accs in model_accuracies.items()
                }
                
                if model_avgs:
                    best_model = max(model_avgs.items(), key=lambda x: x[1])
                    worst_model = min(model_avgs.items(), key=lambda x: x[1])
                    
                    stats["best_model"] = {
                        "name": best_model[0],
                        "avg_accuracy": best_model[1]
                    }
                    stats["worst_model"] = {
                        "name": worst_model[0],
                        "avg_accuracy": worst_model[1]
                    }
    
    def filter_runs(
        self,
        model_filter: Optional[str] = None,
        task_filter: Optional[str] = None,
        min_accuracy: Optional[float] = None,
        max_accuracy: Optional[float] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter runs based on criteria.
        
        Args:
            model_filter: Filter by model name (substring match)
            task_filter: Filter by task name
            min_accuracy: Minimum accuracy threshold
            max_accuracy: Maximum accuracy threshold
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            
        Returns:
            Filtered list of runs
        """
        filtered_runs = []
        
        for run in self.all_runs:
            # Model filter
            if model_filter:
                model_name = run.get("model", {}).get("name", "")
                if model_filter.lower() not in model_name.lower():
                    continue
            
            # Task filter
            if task_filter:
                tasks = run.get("results", {}).keys()
                if task_filter not in tasks:
                    continue
            
            # Accuracy filters
            avg_accuracy = run.get("average_accuracy", 0)
            if min_accuracy is not None and avg_accuracy < min_accuracy:
                continue
            if max_accuracy is not None and avg_accuracy > max_accuracy:
                continue
            
            # Date filters
            if start_date or end_date:
                timestamp = run.get("timestamp", "")
                if timestamp:
                    try:
                        run_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        if start_date:
                            start = datetime.fromisoformat(start_date)
                            if run_date < start:
                                continue
                        if end_date:
                            end = datetime.fromisoformat(end_date)
                            if run_date > end:
                                continue
                    except:
                        logger.warning(f"Invalid timestamp in run {run.get('run_id')}: {timestamp}")
            
            filtered_runs.append(run)
        
        return filtered_runs
    
    def sort_runs(
        self,
        runs: List[Dict[str, Any]],
        sort_by: str = "timestamp",
        reverse: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Sort runs by specified field.
        
        Args:
            runs: List of runs to sort
            sort_by: Field to sort by (timestamp, accuracy, model)
            reverse: Sort in descending order
            
        Returns:
            Sorted list of runs
        """
        if sort_by == "timestamp":
            key_func = lambda r: r.get("timestamp", "")
        elif sort_by == "accuracy":
            key_func = lambda r: r.get("average_accuracy", 0)
        elif sort_by == "model":
            key_func = lambda r: r.get("model", {}).get("name", "")
        else:
            logger.warning(f"Unknown sort field: {sort_by}, using timestamp")
            key_func = lambda r: r.get("timestamp", "")
        
        return sorted(runs, key=key_func, reverse=reverse)
    
    def generate_metadata(self, output_path: Path):
        """Generate unified metadata.json file."""
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "total_runs": len(self.all_runs),
            "total_models": len(self.model_stats),
            "total_tasks": len(self.task_stats),
            "models": {},
            "tasks": {},
            "runs": []
        }
        
        # Add model statistics
        for model_name, stats in self.model_stats.items():
            metadata["models"][model_name] = {
                "total_runs": stats["total_runs"],
                "avg_accuracy": round(stats["avg_accuracy"], 4),
                "std_accuracy": round(stats["std_accuracy"], 4),
                "median_accuracy": round(stats["median_accuracy"], 4),
                "best_run": stats["best_run"],
                "worst_run": stats["worst_run"],
                "task_performance": dict(stats["task_results"])
            }
        
        # Add task statistics
        for task_name, stats in self.task_stats.items():
            metadata["tasks"][task_name] = {
                "total_runs": len(stats["accuracies"]),
                "unique_models": len(stats["models"]),
                "avg_accuracy": round(stats["avg_accuracy"], 4),
                "std_accuracy": round(stats["std_accuracy"], 4),
                "best_model": stats["best_model"],
                "worst_model": stats["worst_model"]
            }
        
        # Add run summaries
        for run in self.all_runs:
            run_summary = {
                "run_id": run.get("run_id", run.get("_run_dir", "unknown")),
                "model": run.get("model", {}).get("name", "unknown"),
                "timestamp": run.get("timestamp", ""),
                "average_accuracy": round(run.get("average_accuracy", 0), 4),
                "tasks": list(run.get("results", {}).keys()),
                "wandb_url": None
            }
            
            # Extract W&B URL if available
            if run.get("wandb_history"):
                for entry in run["wandb_history"]:
                    if entry.get("name") and run_summary["run_id"] in entry["name"]:
                        run_summary["wandb_url"] = entry.get("url")
                        break
            
            metadata["runs"].append(run_summary)
        
        # Write metadata
        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Generated metadata: {output_path}")
    
    def export_csv(self, output_path: Path):
        """Export aggregated data to CSV format."""
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                "Run ID", "Model", "Timestamp", "Average Accuracy",
                "Tasks", "Task Count", "W&B URL"
            ])
            
            # Write run data
            for run in self.all_runs:
                run_id = run.get("run_id", run.get("_run_dir", "unknown"))
                model_name = run.get("model", {}).get("name", "unknown")
                timestamp = run.get("timestamp", "")
                avg_accuracy = round(run.get("average_accuracy", 0), 4)
                tasks = list(run.get("results", {}).keys())
                task_count = len(tasks)
                
                # Extract W&B URL
                wandb_url = ""
                if run.get("wandb_history"):
                    for entry in run["wandb_history"]:
                        if entry.get("name") and run_id in entry["name"]:
                            wandb_url = entry.get("url", "")
                            break
                
                writer.writerow([
                    run_id, model_name, timestamp, avg_accuracy,
                    ", ".join(tasks), task_count, wandb_url
                ])
        
        logger.info(f"Exported CSV: {output_path}")
    
    def print_summary(self):
        """Print summary statistics to console."""
        print("\n" + "="*60)
        print("BENCHMARK SUMMARY")
        print("="*60)
        print(f"Total Runs: {len(self.all_runs)}")
        print(f"Total Models: {len(self.model_stats)}")
        print(f"Total Tasks: {len(self.task_stats)}")
        print()
        
        # Model performance table
        print("MODEL PERFORMANCE:")
        print("-"*60)
        print(f"{'Model':<30} {'Runs':<6} {'Avg Acc':<10} {'Std Dev':<10}")
        print("-"*60)
        
        # Sort models by average accuracy
        sorted_models = sorted(
            self.model_stats.items(),
            key=lambda x: x[1]["avg_accuracy"],
            reverse=True
        )
        
        for model_name, stats in sorted_models[:10]:  # Top 10 models
            print(f"{model_name[:30]:<30} {stats['total_runs']:<6} "
                  f"{stats['avg_accuracy']:<10.4f} {stats['std_accuracy']:<10.4f}")
        
        if len(sorted_models) > 10:
            print(f"... and {len(sorted_models) - 10} more models")
        
        print()
        
        # Task difficulty table
        print("TASK DIFFICULTY (by average accuracy):")
        print("-"*60)
        print(f"{'Task':<30} {'Models':<8} {'Avg Acc':<10} {'Best Model':<20}")
        print("-"*60)
        
        # Sort tasks by average accuracy
        sorted_tasks = sorted(
            self.task_stats.items(),
            key=lambda x: x[1]["avg_accuracy"],
            reverse=True
        )
        
        for task_name, stats in sorted_tasks:
            best_model = stats.get("best_model", {})
            best_model_name = best_model.get("name", "N/A")[:20] if best_model else "N/A"
            
            print(f"{task_name[:30]:<30} {len(stats['models']):<8} "
                  f"{stats['avg_accuracy']:<10.4f} {best_model_name:<20}")
        
        print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate benchmark data from all runs"
    )
    parser.add_argument(
        "--project-root", "-p",
        default=".",
        help="Project root directory (default: current directory)"
    )
    parser.add_argument(
        "--output", "-o",
        default="metadata.json",
        help="Output metadata file (default: metadata.json)"
    )
    parser.add_argument(
        "--csv",
        help="Export data to CSV file"
    )
    parser.add_argument(
        "--filter-model", "-m",
        help="Filter by model name (substring match)"
    )
    parser.add_argument(
        "--filter-task", "-t",
        help="Filter by task name"
    )
    parser.add_argument(
        "--min-accuracy",
        type=float,
        help="Minimum accuracy threshold"
    )
    parser.add_argument(
        "--max-accuracy",
        type=float,
        help="Maximum accuracy threshold"
    )
    parser.add_argument(
        "--start-date",
        help="Start date for filtering (ISO format)"
    )
    parser.add_argument(
        "--end-date",
        help="End date for filtering (ISO format)"
    )
    parser.add_argument(
        "--sort-by",
        choices=["timestamp", "accuracy", "model"],
        default="timestamp",
        help="Sort field for output"
    )
    parser.add_argument(
        "--ascending",
        action="store_true",
        help="Sort in ascending order (default: descending)"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print summary statistics"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize aggregator
    aggregator = BenchmarkAggregator(Path(args.project_root))
    
    # Scan and aggregate data
    aggregator.scan_all_runs()
    aggregator.aggregate_data()
    
    # Apply filters if specified
    if any([args.filter_model, args.filter_task, args.min_accuracy, 
            args.max_accuracy, args.start_date, args.end_date]):
        filtered_runs = aggregator.filter_runs(
            model_filter=args.filter_model,
            task_filter=args.filter_task,
            min_accuracy=args.min_accuracy,
            max_accuracy=args.max_accuracy,
            start_date=args.start_date,
            end_date=args.end_date
        )
        logger.info(f"Filtered to {len(filtered_runs)} runs")
        
        # Update aggregator with filtered data
        aggregator.all_runs = filtered_runs
        aggregator.model_stats.clear()
        aggregator.task_stats.clear()
        aggregator.aggregate_data()
    
    # Sort runs
    aggregator.all_runs = aggregator.sort_runs(
        aggregator.all_runs,
        sort_by=args.sort_by,
        reverse=not args.ascending
    )
    
    # Generate output
    output_path = Path(args.project_root) / args.output
    aggregator.generate_metadata(output_path)
    
    # Export CSV if requested
    if args.csv:
        csv_path = Path(args.project_root) / args.csv
        aggregator.export_csv(csv_path)
    
    # Print summary if requested
    if args.summary:
        aggregator.print_summary()


if __name__ == "__main__":
    main()