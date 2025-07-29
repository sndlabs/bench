"""Custom model registration for lm-evaluation-harness.

This module allows registering custom model implementations
that can be used with the lm-evaluation-harness.
"""

import logging
from typing import Dict, Type, Any

logger = logging.getLogger(__name__)

# Registry for custom model classes
MODEL_REGISTRY: Dict[str, Type[Any]] = {}


def register_model(name: str):
    """
    Decorator to register a custom model class.
    
    Usage:
        @register_model("my_custom_model")
        class MyCustomModel(LM):
            ...
    """
    def decorator(cls):
        MODEL_REGISTRY[name] = cls
        logger.info(f"Registered custom model: {name}")
        return cls
    return decorator


def get_model_class(name: str) -> Type[Any]:
    """
    Get a registered model class by name.
    
    Args:
        name: Name of the model
        
    Returns:
        Model class
        
    Raises:
        KeyError: If model not found
    """
    if name not in MODEL_REGISTRY:
        raise KeyError(f"Model '{name}' not found in registry. Available models: {list(MODEL_REGISTRY.keys())}")
    return MODEL_REGISTRY[name]


# Import and register any custom models here
# Example:
# from .llama_cpp_model import LlamaCppModel