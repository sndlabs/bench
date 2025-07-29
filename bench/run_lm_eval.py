#!/usr/bin/env python3
"""Main evaluation runner for snd-bench using lm-evaluation-harness."""

import os
import sys
import argparse
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now we can import bench modules
import bench.models  # This registers custom models
from bench.config.merger import merge_configs, load_config_file, load_env_config, ConfigPriority
from bench.config.hotreload import HotReloadConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LMEvalRunner:
    """Runner for lm-evaluation-harness evaluations."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the evaluation runner.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.results_dir = Path(config.get('results_dir', 'results'))
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    def run_evaluation(self, 
                      model: str,
                      tasks: List[str],
                      model_args: Optional[Dict[str, Any]] = None,
                      **kwargs) -> Dict[str, Any]:
        """
        Run evaluation on specified tasks.
        
        Args:
            model: Model type/name
            tasks: List of tasks to evaluate
            model_args: Arguments for model initialization
            **kwargs: Additional arguments for lm_eval
            
        Returns:
            Evaluation results
        """
        try:
            # Import lm_eval here to avoid import errors if not installed
            from lm_eval import evaluator
            from lm_eval.models import get_model
        except ImportError as e:
            logger.error("lm-evaluation-harness not installed. Please run: pip install lm-eval")
            raise
            
        # Prepare model arguments
        model_args = model_args or {}
        
        # Check if it's a custom model
        if model in bench.models.MODEL_REGISTRY:
            logger.info(f"Using custom model: {model}")
            model_class = bench.models.get_model_class(model)
            model_instance = model_class(**model_args)
        else:
            # Use built-in lm-eval model
            logger.info(f"Using built-in model: {model}")
            model_instance = get_model(model).create_from_arg_string(
                ",".join(f"{k}={v}" for k, v in model_args.items())
            )
            
        # Run evaluation
        logger.info(f"Running evaluation on tasks: {tasks}")
        results = evaluator.simple_evaluate(
            model=model_instance,
            tasks=tasks,
            **kwargs
        )
        
        # Save results
        self._save_results(results, model, tasks)
        
        return results
        
    def _save_results(self, results: Dict[str, Any], model: str, tasks: List[str]) -> None:
        """Save evaluation results to file."""
        import time
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{model}_{'-'.join(tasks)}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Results saved to: {filepath}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run lm-evaluation-harness evaluations"
    )
    
    # Model arguments
    parser.add_argument(
        "--model", 
        type=str, 
        required=True,
        help="Model type (e.g., 'hf', 'openai', 'llama_cpp', or custom model name)"
    )
    parser.add_argument(
        "--model_args",
        type=str,
        help="Model arguments as key=value pairs separated by commas"
    )
    
    # Task arguments
    parser.add_argument(
        "--tasks",
        type=str,
        required=True,
        help="Comma-separated list of tasks to evaluate"
    )
    
    # Configuration
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--hot_reload",
        action="store_true",
        help="Enable hot reload for configuration"
    )
    
    # Evaluation options
    parser.add_argument(
        "--num_fewshot",
        type=int,
        help="Number of few-shot examples"
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        help="Batch size for evaluation"
    )
    parser.add_argument(
        "--device",
        type=str,
        help="Device to use (e.g., 'cuda', 'cpu')"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of examples per task"
    )
    
    # Output options
    parser.add_argument(
        "--output_path",
        type=str,
        help="Path to save results"
    )
    parser.add_argument(
        "--log_samples",
        action="store_true",
        help="Log individual samples"
    )
    
    return parser.parse_args()


def parse_model_args(model_args_str: str) -> Dict[str, Any]:
    """Parse model arguments from string."""
    if not model_args_str:
        return {}
        
    args = {}
    for pair in model_args_str.split(','):
        if '=' not in pair:
            logger.warning(f"Invalid model argument: {pair}")
            continue
            
        key, value = pair.split('=', 1)
        
        # Try to parse value as JSON
        try:
            args[key] = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # If not JSON, use as string
            args[key] = value
            
    return args


def main():
    """Main entry point."""
    args = parse_args()
    
    # Load configuration
    configs = []
    priorities = []
    
    # Default configuration
    default_config = {
        'results_dir': 'results',
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }
    configs.append(default_config)
    priorities.append(ConfigPriority.DEFAULT)
    
    # File configuration
    if args.config:
        config_path = Path(args.config)
        file_config = load_config_file(config_path)
        if file_config:
            configs.append(file_config)
            priorities.append(ConfigPriority.FILE)
            
    # Environment configuration
    env_config = load_env_config()
    if env_config:
        configs.append(env_config)
        priorities.append(ConfigPriority.ENVIRONMENT)
        
    # Runtime configuration from args
    runtime_config = {}
    if args.output_path:
        runtime_config['results_dir'] = args.output_path
    configs.append(runtime_config)
    priorities.append(ConfigPriority.RUNTIME)
    
    # Merge configurations
    config = merge_configs(configs, priorities)
    
    # Setup hot reload if requested
    if args.hot_reload and args.config:
        hot_config = HotReloadConfig(config)
        hot_config.add_config_file(Path(args.config))
        hot_config.start()
        config = hot_config.config
        
    # Initialize runner
    runner = LMEvalRunner(config)
    
    # Parse arguments
    model_args = parse_model_args(args.model_args)
    tasks = [t.strip() for t in args.tasks.split(',')]
    
    # Prepare evaluation kwargs
    eval_kwargs = {}
    if args.num_fewshot is not None:
        eval_kwargs['num_fewshot'] = args.num_fewshot
    if args.batch_size is not None:
        eval_kwargs['batch_size'] = args.batch_size
    if args.device is not None:
        eval_kwargs['device'] = args.device
    if args.limit is not None:
        eval_kwargs['limit'] = args.limit
    if args.log_samples:
        eval_kwargs['log_samples'] = True
        
    try:
        # Run evaluation
        results = runner.run_evaluation(
            model=args.model,
            tasks=tasks,
            model_args=model_args,
            **eval_kwargs
        )
        
        # Print summary
        logger.info("Evaluation completed!")
        for task, task_results in results['results'].items():
            logger.info(f"\nTask: {task}")
            for metric, value in task_results.items():
                if not metric.startswith('_'):
                    logger.info(f"  {metric}: {value}")
                    
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        sys.exit(1)
    finally:
        # Stop hot reload if enabled
        if args.hot_reload and 'hot_config' in locals():
            hot_config.stop()


if __name__ == "__main__":
    main()