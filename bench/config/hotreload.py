"""Hot reload functionality for configuration files."""

import os
import time
import threading
import logging
from pathlib import Path
from typing import Dict, Any, Callable, Optional, Set

from .merger import ConfigPriority, load_config_file, merge_configs

logger = logging.getLogger(__name__)


class ConfigWatcher:
    """Watch configuration files for changes and reload them."""
    
    def __init__(self, check_interval: float = 1.0):
        """
        Initialize configuration watcher.
        
        Args:
            check_interval: Seconds between file checks
        """
        self.check_interval = check_interval
        self.watched_files: Dict[Path, float] = {}
        self.callbacks: Set[Callable[[Dict[str, Any]], None]] = set()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
    def watch(self, path: Path, callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> None:
        """
        Add a file to watch for changes.
        
        Args:
            path: Path to configuration file
            callback: Optional callback for when this file changes
        """
        path = Path(path).resolve()
        
        with self._lock:
            if path.exists():
                self.watched_files[path] = path.stat().st_mtime
                logger.info(f"Watching configuration file: {path}")
            else:
                logger.warning(f"Cannot watch non-existent file: {path}")
                
            if callback:
                self.callbacks.add(callback)
                
    def unwatch(self, path: Path) -> None:
        """
        Remove a file from the watch list.
        
        Args:
            path: Path to stop watching
        """
        path = Path(path).resolve()
        
        with self._lock:
            if path in self.watched_files:
                del self.watched_files[path]
                logger.info(f"Stopped watching: {path}")
                
    def start(self) -> None:
        """Start the watcher thread."""
        if self._running:
            logger.warning("ConfigWatcher is already running")
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        logger.info("ConfigWatcher started")
        
    def stop(self) -> None:
        """Stop the watcher thread."""
        if not self._running:
            return
            
        self._running = False
        if self._thread:
            self._thread.join(timeout=self.check_interval * 2)
        logger.info("ConfigWatcher stopped")
        
    def _watch_loop(self) -> None:
        """Main watch loop."""
        while self._running:
            try:
                self._check_files()
            except Exception as e:
                logger.error(f"Error in watch loop: {e}")
                
            time.sleep(self.check_interval)
            
    def _check_files(self) -> None:
        """Check all watched files for changes."""
        with self._lock:
            files_to_check = list(self.watched_files.items())
            
        changed_configs = []
        
        for path, last_mtime in files_to_check:
            if not path.exists():
                logger.warning(f"Watched file disappeared: {path}")
                continue
                
            current_mtime = path.stat().st_mtime
            if current_mtime > last_mtime:
                logger.info(f"Configuration file changed: {path}")
                
                # Update mtime
                with self._lock:
                    self.watched_files[path] = current_mtime
                    
                # Load new configuration
                config = load_config_file(path)
                if config:
                    changed_configs.append(config)
                    
        # Notify callbacks if any files changed
        if changed_configs and self.callbacks:
            merged_config = merge_configs(
                changed_configs, 
                [ConfigPriority.HOT_RELOAD] * len(changed_configs)
            )
            
            for callback in self.callbacks:
                try:
                    callback(merged_config)
                except Exception as e:
                    logger.error(f"Error in config reload callback: {e}")
                    

class HotReloadConfig:
    """Configuration with hot reload support."""
    
    def __init__(self, base_config: Dict[str, Any] = None):
        """
        Initialize hot reload configuration.
        
        Args:
            base_config: Initial configuration
        """
        self.config = base_config or {}
        self.watcher = ConfigWatcher()
        self._lock = threading.RLock()
        
    def add_config_file(self, path: Path) -> None:
        """
        Add a configuration file with hot reload.
        
        Args:
            path: Path to configuration file
        """
        # Load initial config
        config = load_config_file(path)
        if config:
            with self._lock:
                self.config = merge_configs(
                    [self.config, config],
                    [ConfigPriority.FILE, ConfigPriority.HOT_RELOAD]
                )
                
        # Watch for changes
        self.watcher.watch(path, self._on_config_changed)
        
    def start(self) -> None:
        """Start hot reload monitoring."""
        self.watcher.start()
        
    def stop(self) -> None:
        """Stop hot reload monitoring."""
        self.watcher.stop()
        
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        with self._lock:
            value = self.config
            
            for part in key.split('.'):
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
                    
            return value
            
    def _on_config_changed(self, new_config: Dict[str, Any]) -> None:
        """Handle configuration change."""
        with self._lock:
            self.config = merge_configs(
                [self.config, new_config],
                [ConfigPriority.FILE, ConfigPriority.HOT_RELOAD]
            )
            logger.info("Configuration reloaded")