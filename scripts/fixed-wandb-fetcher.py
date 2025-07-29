#!/usr/bin/env python3
"""
Weights & Biases Data Fetcher for SND-Bench

This script fetches benchmark run data from the W&B API and exports it in JSON format.
It handles pagination, error handling, and supports various filtering options.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import wandb
from pathlib import Path
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WandbFetcher:
    """Handles fetching data from Weights & Biases API."""
    
    def __init__(self, entity: str, project: str, api_key: Optional[str] = None):
        """
        Initialize W&B fetcher.
        
        Args:
            entity: W&B entity (username or team)
            project: W&B project name
            api_key: Optional API key (will use env var if not provided)
        """
        self.entity = entity
        self.project = project
        
        # Initialize W&B API
        if api_key:
            os.environ["WANDB_API_KEY"] = api_key
        
        try:
            self.api = wandb.Api()
            logger.info(f"Connected to W&B API for {entity}/{project}")
        except Exception as e:
            logger.error(f"Failed to initialize W&B API: {e}")
            raise
    
    def fetch_runs(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order: str = "-created_at",
        limit: Optional[int] = None,
        include_history: bool = True,
        include_summary: bool = True,
        include_config: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetch runs from W&B with pagination support.
        
        Args:
            filters: Optional filters for runs
            order: Sort order (default: newest first)
            limit: Maximum number of runs to fetch
            include_history: Include run history data
            include_summary: Include run summary data
            include_config: Include run configuration
            
        Returns:
            List of run data dictionaries
        """
        runs_data = []
        page_size = 50  # W&B API page size
        
        try:
            runs = self.api.runs(
                f"{self.entity}/{self.project}",
                filters=filters,
                order=order,
                per_page=page_size
            )
            
            count = 0
            for run in runs:
                if limit and count >= limit:
                    break
                
                logger.info(f"Processing run: {run.id} - {run.name}")
                
                run_data = {
                    "id": run.id,
                    "name": run.name,
                    "state": run.state,
                    "created_at": run.created_at,
                    "updated_at": run.updated_at,
                    "url": run.url,
                    "tags": run.tags,
                    "notes": run.notes,
                }
                
                # Add config if requested
                if include_config:
                    run_data["config"] = dict(run.config)
                
                # Add summary metrics if requested
                if include_summary:
                    run_data["summary"] = dict(run.summary)
                
                # Add history if requested
                if include_history:
                    try:
                        history = run.history()
                        if not history.empty:
                            # Convert to list of dicts for JSON serialization
                            run_data["history"] = history.to_dict('records')
                        else:
                            run_data["history"] = []
                    except Exception as e:
                        logger.warning(f"Failed to fetch history for run {run.id}: {e}")
                        run_data["history"] = []
                
                # Add system metrics
                run_data["system_metrics"] = {
                    "runtime": run.summary.get("_runtime", 0),
                    "gpu_count": run.summary.get("_wandb", {}).get("gpu_count", 0),
                    "cpu_count": run.summary.get("_wandb", {}).get("cpu_count", 0),
                }
                
                runs_data.append(run_data)
                count += 1
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error fetching runs: {e}")
            raise
        
        logger.info(f"Fetched {len(runs_data)} runs")
        return runs_data
    
    def fetch_run_by_id(self, run_id: str) -> Dict[str, Any]:
        """
        Fetch a specific run by ID.
        
        Args:
            run_id: W&B run ID
            
        Returns:
            Run data dictionary
        """
        try:
            run = self.api.run(f"{self.entity}/{self.project}/{run_id}")
            
            run_data = {
                "id": run.id,
                "name": run.name,
                "state": run.state,
                "created_at": run.created_at,
                "updated_at": run.updated_at,
                "url": run.url,
                "tags": run.tags,
                "notes": run.notes,
                "config": dict(run.config),
                "summary": dict(run.summary),
            }
            
            # Get full history
            history = run.history()
            if not history.empty:
                run_data["history"] = history.to_dict('records')
            else:
                run_data["history"] = []
            
            # Get files
            files = run.files()
            run_data["files"] = [
                {
                    "name": f.name,
                    "size": f.size,
                    "url": f.url,
                }
                for f in files
            ]
            
            return run_data
            
        except Exception as e:
            logger.error(f"Error fetching run {run_id}: {e}")
            raise
    
    def fetch_model_runs(self, model_name: str) -> List[Dict[str, Any]]:
        """
        Fetch all runs for a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            List of run data dictionaries
        """
        filters = {"config.model": model_name}
        return self.fetch_runs(filters=filters)
    
    def fetch_recent_runs(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Fetch runs from the last N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of run data dictionaries
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        filters = {"created_at": {"$gte": cutoff_date.isoformat()}}
        return self.fetch_runs(filters=filters)
    
    def export_to_json(self, runs_data: List[Dict[str, Any]], output_path: str):
        """
        Export runs data to JSON file.
        
        Args:
            runs_data: List of run data dictionaries
            output_path: Path to output JSON file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert datetime objects to strings
        def serialize_datetime(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            return obj
        
        with open(output_path, 'w') as f:
            json.dump(runs_data, f, indent=2, default=serialize_datetime)
        
        logger.info(f"Exported {len(runs_data)} runs to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch benchmark data from Weights & Biases"
    )
    parser.add_argument(
        "--entity", "-e",
        default=os.getenv("WANDB_ENTITY", "sndlabs"),
        help="W&B entity (username or team)"
    )
    parser.add_argument(
        "--project", "-p",
        default=os.getenv("WANDB_PROJECT", "llm-bench"),
        help="W&B project name"
    )
    parser.add_argument(
        "--output", "-o",
        default="wandb_data.json",
        help="Output JSON file path"
    )
    parser.add_argument(
        "--run-id", "-r",
        help="Fetch specific run by ID"
    )
    parser.add_argument(
        "--model", "-m",
        help="Filter runs by model name"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        help="Maximum number of runs to fetch"
    )
    parser.add_argument(
        "--days", "-d",
        type=int,
        help="Fetch runs from last N days"
    )
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="Skip fetching run history (faster)"
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Skip fetching run summary"
    )
    parser.add_argument(
        "--no-config",
        action="store_true",
        help="Skip fetching run config"
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("WANDB_API_KEY"),
        help="W&B API key (can also use WANDB_API_KEY env var)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check for API key
    if not args.api_key:
        logger.error("W&B API key not found. Set WANDB_API_KEY environment variable or use --api-key")
        sys.exit(1)
    
    try:
        # Initialize fetcher
        fetcher = WandbFetcher(
            entity=args.entity,
            project=args.project,
            api_key=args.api_key
        )
        
        # Fetch runs based on arguments
        if args.run_id:
            logger.info(f"Fetching run {args.run_id}")
            runs_data = [fetcher.fetch_run_by_id(args.run_id)]
        elif args.model:
            logger.info(f"Fetching runs for model: {args.model}")
            runs_data = fetcher.fetch_model_runs(args.model)
        elif args.days:
            logger.info(f"Fetching runs from last {args.days} days")
            runs_data = fetcher.fetch_recent_runs(args.days)
        else:
            logger.info("Fetching all runs")
            runs_data = fetcher.fetch_runs(
                limit=args.limit,
                include_history=not args.no_history,
                include_summary=not args.no_summary,
                include_config=not args.no_config
            )
        
        # Export to JSON
        fetcher.export_to_json(runs_data, args.output)
        
        # Print summary
        logger.info(f"Successfully fetched {len(runs_data)} runs")
        logger.info(f"Data exported to: {args.output}")
        
    except Exception as e:
        logger.error(f"Failed to fetch W&B data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()