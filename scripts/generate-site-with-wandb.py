#!/usr/bin/env python3
"""
Static Site Generator with W&B Integration for SND-Bench

This script generates static HTML pages from benchmark results,
integrating W&B data and AI summaries.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import shutil
from jinja2 import Environment, FileSystemLoader, Template

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# HTML templates as strings (since we don't have a templates directory yet)
RUN_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ run_id }} - SND-Bench Results</title>
    <link rel="stylesheet" href="../../assets/css/dashboard.css">
    <style>
        .wandb-link { 
            background: #FFBE00; 
            color: #000; 
            padding: 5px 10px; 
            border-radius: 5px; 
            text-decoration: none; 
            font-weight: bold;
            display: inline-block;
            margin: 10px 0;
        }
        .metric-card {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        .ai-summary {
            background: #e8f4f8;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #2196F3;
        }
        .wandb-history {
            margin-top: 30px;
        }
        .history-item {
            background: #fff;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .accuracy-chart {
            margin: 20px 0;
            height: 300px;
        }
    </style>
</head>
<body>
    <header>
        <h1>SND-Bench Results</h1>
        <nav>
            <a href="../../index.html">Dashboard</a>
            <a href="../../compare.html">Compare</a>
        </nav>
    </header>
    
    <main>
        <div class="run-header">
            <h2>Run: {{ run_id }}</h2>
            <p>{{ timestamp }}</p>
            {% if wandb_url %}
            <a href="{{ wandb_url }}" target="_blank" class="wandb-link">View in W&B →</a>
            {% endif %}
        </div>
        
        <section class="model-info">
            <h3>Model Information</h3>
            <div class="metric-card">
                <p><strong>Name:</strong> {{ model.name }}</p>
                <p><strong>Path:</strong> {{ model.path }}</p>
                <p><strong>Size:</strong> {{ model.size }}</p>
            </div>
        </section>
        
        <section class="results">
            <h3>Benchmark Results</h3>
            <div class="metrics-grid">
                {% for task, metrics in results.items() %}
                <div class="metric-card">
                    <h4>{{ task }}</h4>
                    {% set acc = metrics.get('accuracy') or metrics.get('acc') or metrics.get('acc,none') %}
                    {% set stderr = metrics.get('stderr') or metrics.get('acc_stderr') or metrics.get('acc_stderr,none') %}
                    {% set acc_norm = metrics.get('acc_norm') or metrics.get('acc_norm,none') %}
                    {% set acc_norm_stderr = metrics.get('acc_norm_stderr') or metrics.get('acc_norm_stderr,none') %}
                    
                    {% if acc is not none %}
                    <p><strong>Accuracy:</strong> {{ "%.4f" | format(acc) }}</p>
                    {% endif %}
                    {% if stderr is not none %}
                    <p><strong>Stderr:</strong> ± {{ "%.4f" | format(stderr) }}</p>
                    {% endif %}
                    {% if acc_norm is not none %}
                    <p><strong>Normalized Accuracy:</strong> {{ "%.4f" | format(acc_norm) }}</p>
                    {% endif %}
                    {% if acc_norm_stderr is not none %}
                    <p><strong>Normalized Stderr:</strong> ± {{ "%.4f" | format(acc_norm_stderr) }}</p>
                    {% endif %}
                    {% if metrics.samples %}
                    <p><strong>Samples:</strong> {{ metrics.samples }}</p>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            
            <div class="metric-card">
                <h4>Overall Performance</h4>
                <p><strong>Average Accuracy:</strong> {{ "%.4f" | format(average_accuracy) }}</p>
                <p><strong>Total Tasks:</strong> {{ total_tasks }}</p>
            </div>
        </section>
        
        {% if summary %}
        <section class="ai-summary">
            <h3>AI Analysis Summary</h3>
            <div class="summary-content">{{ summary | replace('\\"', '"') | replace('\\n', '\n') | safe }}</div>
        </section>
        {% endif %}
        
        {% if wandb_data %}
        <section class="wandb-integration">
            <h3>W&B Integration</h3>
            
            {% if wandb_data.metrics %}
            <div class="metric-card">
                <h4>W&B Metrics</h4>
                {% for key, value in wandb_data.metrics.items() %}
                <p><strong>{{ key }}:</strong> {{ value }}</p>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if wandb_data.system_metrics %}
            <div class="metric-card">
                <h4>System Metrics</h4>
                <p><strong>Runtime:</strong> {{ wandb_data.system_metrics.runtime }}s</p>
                <p><strong>GPU Count:</strong> {{ wandb_data.system_metrics.gpu_count }}</p>
                <p><strong>CPU Count:</strong> {{ wandb_data.system_metrics.cpu_count }}</p>
            </div>
            {% endif %}
            
            {% if wandb_data.history %}
            <div class="accuracy-chart" id="accuracy-chart">
                <!-- Chart will be rendered by JavaScript -->
            </div>
            {% endif %}
        </section>
        {% endif %}
        
        {% if wandb_history %}
        <section class="wandb-history">
            <h3>Previous Runs (from W&B)</h3>
            <div class="history-list">
                {% for run in wandb_history %}
                <div class="history-item">
                    <h4><a href="{{ run.url }}" target="_blank">{{ run.name }}</a></h4>
                    <p><strong>ID:</strong> {{ run.id }}</p>
                    <p><strong>Created:</strong> {{ run.created_at }}</p>
                    <p><strong>Model:</strong> {{ run.model }}</p>
                    {% if run.metrics %}
                    <div class="metrics">
                        {% for key, value in run.metrics.items() %}
                        <span class="metric"><strong>{{ key }}:</strong> {{ value }}</span>
                        {% endfor %}
                    </div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
        </section>
        {% endif %}
    </main>
    
    <script src="../../assets/js/dashboard.js"></script>
    {% if wandb_data.history %}
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Render accuracy chart from W&B history
        const ctx = document.getElementById('accuracy-chart').getContext('2d');
        const historyData = {{ wandb_data.history | tojson }};
        
        // Extract accuracy data
        const accuracyData = historyData
            .filter(item => item.accuracy !== undefined)
            .map((item, index) => ({
                x: item._step || index,
                y: item.accuracy
            }));
        
        new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'Accuracy',
                    data: accuracyData,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'linear',
                        display: true,
                        title: {
                            display: true,
                            text: 'Step'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Accuracy'
                        }
                    }
                }
            }
        });
    </script>
    {% endif %}
</body>
</html>"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SND-Bench Dashboard</title>
    <link rel="stylesheet" href="assets/css/dashboard.css">
    <style>
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-card {
            background: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-card h3 {
            margin: 0 0 10px 0;
            color: #333;
        }
        .stat-card .value {
            font-size: 2em;
            font-weight: bold;
            color: #2196F3;
        }
        .wandb-badge {
            background: #FFBE00;
            color: #000;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 0.8em;
            margin-left: 5px;
        }
    </style>
</head>
<body>
    <header>
        <h1>SND-Bench Dashboard</h1>
        <nav>
            <a href="index.html" class="active">Dashboard</a>
            <a href="compare.html">Compare</a>
        </nav>
    </header>
    
    <main>
        <section class="stats">
            <h2>Overview</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Total Runs</h3>
                    <div class="value">{{ total_runs }}</div>
                </div>
                <div class="stat-card">
                    <h3>Models Tested</h3>
                    <div class="value">{{ unique_models }}</div>
                </div>
                <div class="stat-card">
                    <h3>Average Accuracy</h3>
                    <div class="value">{{ "%.2f" | format(avg_accuracy * 100) }}%</div>
                </div>
                <div class="stat-card">
                    <h3>W&B Runs</h3>
                    <div class="value">{{ wandb_runs }}</div>
                </div>
            </div>
        </section>
        
        <section class="recent-runs">
            <h2>Recent Runs</h2>
            <table class="results-table">
                <thead>
                    <tr>
                        <th>Run ID</th>
                        <th>Model</th>
                        <th>Tasks</th>
                        <th>Average Accuracy</th>
                        <th>Timestamp</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for run in runs %}
                    <tr>
                        <td>
                            <a href="runs/{{ run.run_id }}/index.html">{{ run.run_id }}</a>
                            {% if run.wandb_url %}
                            <span class="wandb-badge">W&B</span>
                            {% endif %}
                        </td>
                        <td>{{ run.model.name }}</td>
                        <td>{{ run.results.keys() | list | join(", ") }}</td>
                        <td>{{ "%.4f" | format(run.average_accuracy) }}</td>
                        <td>{{ run.timestamp }}</td>
                        <td>
                            <a href="runs/{{ run.run_id }}/index.html">View</a>
                            {% if run.wandb_url %}
                            | <a href="{{ run.wandb_url }}" target="_blank">W&B</a>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </section>
        
        <section class="models">
            <h2>Model Performance</h2>
            <div id="model-chart" style="height: 400px; margin: 20px 0;">
                <!-- Chart will be rendered by JavaScript -->
            </div>
        </section>
    </main>
    
    <script src="assets/js/dashboard.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Model performance chart
        const modelData = {{ model_stats | tojson }};
        const ctx = document.getElementById('model-chart').getContext('2d');
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(modelData),
                datasets: [{
                    label: 'Average Accuracy',
                    data: Object.values(modelData).map(m => m.avg_accuracy),
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1.0
                    }
                }
            }
        });
    </script>
</body>
</html>"""


class SiteGenerator:
    """Generates static site from benchmark results with W&B integration."""
    
    def __init__(self, project_root: Path, wandb_data_path: Optional[Path] = None):
        """
        Initialize site generator.
        
        Args:
            project_root: Root directory of the project
            wandb_data_path: Path to W&B data JSON file
        """
        self.project_root = Path(project_root)
        self.runs_dir = self.project_root / "runs"
        self.assets_dir = self.project_root / "assets"
        self.wandb_data = {}
        
        # Load W&B data if provided
        if wandb_data_path and wandb_data_path.exists():
            with open(wandb_data_path, 'r') as f:
                wandb_runs = json.load(f)
                # Index by run name for easy lookup
                for run in wandb_runs:
                    self.wandb_data[run['name']] = run
                logger.info(f"Loaded {len(self.wandb_data)} W&B runs")
        
        # Set up Jinja2 environment
        self.env = Environment(autoescape=True)
        self.env.globals['format'] = format
    
    def load_run_data(self, run_dir: Path) -> Optional[Dict[str, Any]]:
        """Load data.json from a run directory."""
        data_file = run_dir / "data.json"
        if not data_file.exists():
            logger.warning(f"No data.json found in {run_dir}")
            return None
        
        with open(data_file, 'r') as f:
            return json.load(f)
    
    def get_wandb_data_for_run(self, run_id: str, model_name: str) -> Optional[Dict[str, Any]]:
        """Get W&B data for a specific run."""
        # Try to find by exact run name match
        run_name = f"{model_name}-{run_id}"
        if run_name in self.wandb_data:
            return self.wandb_data[run_name]
        
        # Try partial matches
        for name, data in self.wandb_data.items():
            if run_id in name or (model_name in name and run_id[:8] in name):
                return data
        
        return None
    
    def generate_run_page(self, run_dir: Path):
        """Generate HTML page for a single run."""
        run_data = self.load_run_data(run_dir)
        if not run_data:
            return
        
        run_id = run_data.get("run_id", run_dir.name)
        model_name = run_data.get("model", {}).get("name", "unknown")
        
        # Get W&B data for this run
        wandb_run_data = self.get_wandb_data_for_run(run_id, model_name)
        
        # Extract W&B URL from run data or W&B data
        wandb_url = None
        if run_data.get("wandb_history"):
            # Get URL from the most recent W&B history entry
            for entry in run_data["wandb_history"]:
                if entry.get("name") and run_id in entry["name"]:
                    wandb_url = entry.get("url")
                    break
        elif wandb_run_data:
            wandb_url = wandb_run_data.get("url")
        
        # Prepare template context
        context = {
            "run_id": run_id,
            "timestamp": run_data.get("timestamp", ""),
            "model": run_data.get("model", {}),
            "results": run_data.get("results", {}),
            "average_accuracy": run_data.get("average_accuracy", 0),
            "total_tasks": run_data.get("total_tasks", 0),
            "summary": run_data.get("summary", ""),
            "wandb_history": run_data.get("wandb_history", []),
            "wandb_url": wandb_url,
            "wandb_data": wandb_run_data,
        }
        
        # Render template
        template = self.env.from_string(RUN_TEMPLATE)
        html = template.render(**context)
        
        # Write to file
        output_file = run_dir / "index.html"
        with open(output_file, 'w') as f:
            f.write(html)
        
        logger.info(f"Generated page for run {run_id}")
    
    def generate_index_page(self):
        """Generate main dashboard index page."""
        all_runs = []
        model_stats = {}
        
        # Collect all run data
        for run_dir in sorted(self.runs_dir.iterdir(), reverse=True):
            if run_dir.is_dir():
                run_data = self.load_run_data(run_dir)
                if run_data:
                    # Add W&B URL if available
                    model_name = run_data.get("model", {}).get("name", "unknown")
                    wandb_run_data = self.get_wandb_data_for_run(
                        run_data.get("run_id", run_dir.name),
                        model_name
                    )
                    if wandb_run_data:
                        run_data["wandb_url"] = wandb_run_data.get("url")
                    
                    all_runs.append(run_data)
                    
                    # Update model stats
                    if model_name not in model_stats:
                        model_stats[model_name] = {
                            "runs": 0,
                            "total_accuracy": 0,
                            "avg_accuracy": 0
                        }
                    
                    model_stats[model_name]["runs"] += 1
                    model_stats[model_name]["total_accuracy"] += run_data.get("average_accuracy", 0)
        
        # Calculate model averages
        for model_name, stats in model_stats.items():
            if stats["runs"] > 0:
                stats["avg_accuracy"] = stats["total_accuracy"] / stats["runs"]
        
        # Calculate overall stats
        total_runs = len(all_runs)
        unique_models = len(model_stats)
        avg_accuracy = sum(r.get("average_accuracy", 0) for r in all_runs) / total_runs if total_runs > 0 else 0
        wandb_runs = len([r for r in all_runs if r.get("wandb_url")])
        
        # Prepare template context
        context = {
            "runs": all_runs[:20],  # Show latest 20 runs
            "total_runs": total_runs,
            "unique_models": unique_models,
            "avg_accuracy": avg_accuracy,
            "wandb_runs": wandb_runs,
            "model_stats": model_stats,
        }
        
        # Render template
        template = self.env.from_string(INDEX_TEMPLATE)
        html = template.render(**context)
        
        # Write to file
        output_file = self.project_root / "index.html"
        with open(output_file, 'w') as f:
            f.write(html)
        
        logger.info("Generated main dashboard page")
    
    def update_metadata(self):
        """Update metadata.json with all runs information."""
        metadata = {
            "last_updated": datetime.now().isoformat(),
            "total_runs": 0,
            "models": {},
            "runs": []
        }
        
        for run_dir in sorted(self.runs_dir.iterdir()):
            if run_dir.is_dir():
                run_data = self.load_run_data(run_dir)
                if run_data:
                    run_id = run_data.get("run_id", run_dir.name)
                    model_name = run_data.get("model", {}).get("name", "unknown")
                    
                    # Add W&B info
                    wandb_run_data = self.get_wandb_data_for_run(run_id, model_name)
                    
                    run_info = {
                        "run_id": run_id,
                        "model": model_name,
                        "timestamp": run_data.get("timestamp", ""),
                        "average_accuracy": run_data.get("average_accuracy", 0),
                        "tasks": list(run_data.get("results", {}).keys()),
                        "wandb_url": wandb_run_data.get("url") if wandb_run_data else None,
                        "wandb_id": wandb_run_data.get("id") if wandb_run_data else None,
                    }
                    
                    metadata["runs"].append(run_info)
                    metadata["total_runs"] += 1
                    
                    # Update model stats
                    if model_name not in metadata["models"]:
                        metadata["models"][model_name] = {
                            "runs": 0,
                            "best_accuracy": 0,
                            "latest_run": None
                        }
                    
                    metadata["models"][model_name]["runs"] += 1
                    if run_data.get("average_accuracy", 0) > metadata["models"][model_name]["best_accuracy"]:
                        metadata["models"][model_name]["best_accuracy"] = run_data.get("average_accuracy", 0)
                    metadata["models"][model_name]["latest_run"] = run_id
        
        # Write metadata
        metadata_file = self.project_root / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info("Updated metadata.json")
    
    def generate_runs_index(self) -> List[Dict[str, Any]]:
        """Generate runs index with metadata for all runs."""
        logger.info("Generating runs index...")
        
        run_infos = []
        for run_dir in self.runs_dir.iterdir():
            if run_dir.is_dir():
                run_data = self.load_run_data(run_dir)
                if run_data:
                    # Extract essential info for the index
                    run_info = {
                        "run_id": run_data.get("run_id", run_dir.name),
                        "timestamp": run_data.get("timestamp"),
                        "model": {
                            "name": run_data.get("model", {}).get("name", "Unknown"),
                            "path": run_data.get("model", {}).get("path", "")
                        },
                        "average_accuracy": run_data.get("average_accuracy", 0),
                        "total_tasks": run_data.get("total_tasks", 0),
                        "tasks": list(run_data.get("results", {}).keys()),
                        "framework": run_data.get("framework", "lm-eval"),
                        "hardware_profile": run_data.get("hardware_profile", "unknown"),
                        "has_summary": "summary" in run_data,
                        "has_wandb": bool(run_data.get("wandb_history"))
                    }
                    
                    # Add W&B URL if available
                    wandb_data = self.get_wandb_data_for_run(
                        run_info["run_id"], 
                        run_info["model"]["name"]
                    )
                    if wandb_data:
                        run_info["wandb_url"] = wandb_data.get("url", "")
                    
                    run_infos.append(run_info)
        
        # Sort by timestamp (newest first)
        run_infos.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Save runs index
        runs_index = {
            "generated": datetime.now().isoformat(),
            "version": "2.0.0",
            "total_runs": len(run_infos),
            "runs": run_infos
        }
        
        runs_index_path = self.project_root / "runs-index.json"
        with open(runs_index_path, "w") as f:
            json.dump(runs_index, f, indent=2)
        
        logger.info(f"Generated runs index with {len(run_infos)} runs")
        return run_infos

    def generate_all(self):
        """Generate all pages."""
        logger.info("Starting site generation...")
        
        # Generate runs index first
        run_infos = self.generate_runs_index()
        
        # Generate individual run pages
        for run_dir in self.runs_dir.iterdir():
            if run_dir.is_dir():
                self.generate_run_page(run_dir)
        
        # Generate index page
        self.generate_index_page()
        
        # Update metadata with run count
        self.update_metadata()
        
        logger.info("Site generation complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Generate static site with W&B data integration"
    )
    parser.add_argument(
        "--project-root", "-p",
        default=".",
        help="Project root directory (default: current directory)"
    )
    parser.add_argument(
        "--wandb-data", "-w",
        help="Path to W&B data JSON file (from fixed-wandb-fetcher.py)"
    )
    parser.add_argument(
        "--run", "-r",
        help="Generate page for specific run only"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize generator
    generator = SiteGenerator(
        project_root=Path(args.project_root),
        wandb_data_path=Path(args.wandb_data) if args.wandb_data else None
    )
    
    # Generate pages
    if args.run:
        run_dir = generator.runs_dir / args.run
        if run_dir.exists():
            generator.generate_run_page(run_dir)
        else:
            logger.error(f"Run directory not found: {run_dir}")
            sys.exit(1)
    else:
        generator.generate_all()


if __name__ == "__main__":
    main()