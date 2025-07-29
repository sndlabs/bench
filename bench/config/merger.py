"""Configuration merger with priority-based merging."""

import os
import json
import logging
from enum import IntEnum
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

logger = logging.getLogger(__name__)


class ConfigPriority(IntEnum):
    """Configuration priority levels (higher number = higher priority)."""
    DEFAULT = 0
    FILE = 1
    ENVIRONMENT = 2
    RUNTIME = 3
    HOT_RELOAD = 4


def merge_configs(
    configs: List[Dict[str, Any]], 
    priorities: Optional[List[ConfigPriority]] = None
) -> Dict[str, Any]:
    """
    Merge multiple configuration dictionaries based on priority.
    
    Args:
        configs: List of configuration dictionaries
        priorities: List of priorities for each config (same order)
        
    Returns:
        Merged configuration dictionary
    """
    if not configs:
        return {}
        
    if priorities is None:
        priorities = [ConfigPriority.FILE] * len(configs)
        
    if len(configs) != len(priorities):
        raise ValueError("Number of configs must match number of priorities")
    
    # Sort by priority (lowest to highest)
    sorted_pairs = sorted(zip(configs, priorities), key=lambda x: x[1])
    
    merged = {}
    for config, priority in sorted_pairs:
        merged = _deep_merge(merged, config)
        
    return merged


def _deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: Base dictionary
        dict2: Dictionary to merge (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
            
    return result


def load_config_file(path: Path) -> Dict[str, Any]:
    """
    Load configuration from a file.
    
    Args:
        path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    if not path.exists():
        logger.warning(f"Configuration file not found: {path}")
        return {}
        
    try:
        with open(path, 'r') as f:
            if path.suffix == '.json':
                return json.load(f)
            elif path.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f) or {}
            else:
                logger.error(f"Unsupported config file format: {path.suffix}")
                return {}
    except Exception as e:
        logger.error(f"Error loading config file {path}: {e}")
        return {}


def load_env_config(prefix: str = "SND_BENCH_") -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Args:
        prefix: Prefix for environment variables
        
    Returns:
        Configuration dictionary from environment
    """
    config = {}
    
    for key, value in os.environ.items():
        if key.startswith(prefix):
            # Remove prefix and convert to lowercase
            config_key = key[len(prefix):].lower()
            
            # Try to parse JSON values
            try:
                config[config_key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # If not JSON, use as string
                config[config_key] = value
                
    return config