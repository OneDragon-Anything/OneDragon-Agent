"""
Logging configuration module for OneDragon-Agent

Supports log output control via environment variables:
- ODA_DIR: Base directory for storing logs, runtime data, etc. Logs are stored in ODA_DIR/log
- ODA_LOG_LEVEL: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
"""

import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional


class OdaLogger:
    """OneDragon-Agent logger manager"""

    _instance: Optional["OdaLogger"] = None
    _initialized: bool = False

    def __new__(cls) -> "OdaLogger":
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize logger manager"""
        # Note: We don't check _initialized here to allow re-initialization in tests
        # This is needed because tests may set different environment variables

        self.log_path: str | None = None
        self.log_level: str = "INFO"
        self.logger: logging.Logger | None = None

        # We still set a flag to track if we've been initialized at least once
        if not hasattr(self, "_first_init"):
            self._first_init = True
        else:
            self._first_init = False

    def initialize(self, log_dir: str | None = None) -> None:
        """
        Initialize logging system
        
        Args:
            log_dir: Log directory path, if None then read from environment variable
        """
        # Read configuration from parameter or environment variable
        if log_dir is not None:
            self.log_path = log_dir
        else:
            oda_dir = os.getenv("ODA_DIR", "").strip()
            if oda_dir:
                self.log_path = os.path.join(oda_dir, "log")
            else:
                self.log_path = ""
            
        self.log_level = os.getenv("ODA_LOG_LEVEL", "INFO").upper()

        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_levels:
            print(f"Warning: Invalid log level '{self.log_level}', using default level 'INFO'")
            self.log_level = "INFO"

        # Create root logger
        self.logger = logging.getLogger("one_dragon_agent")
        self.logger.setLevel(getattr(logging, self.log_level))

        # Clear existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Set log format
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        formatter = logging.Formatter(log_format)

        # File handler (only created when log_path is not empty)
        if self.log_path:
            try:
                # Create log directory
                log_dir_path = Path(self.log_path)
                log_dir_path.mkdir(parents=True, exist_ok=True)

                # Daily rotating file handler
                log_file = log_dir_path / "oda_log.txt"
                timed_handler = TimedRotatingFileHandler(
                    log_file, 
                    when="midnight", 
                    interval=1, 
                    backupCount=3,  # Keep 3 days of logs
                    encoding="utf-8"
                )
                timed_handler.setLevel(logging.DEBUG)  # File always records DEBUG level
                timed_handler.setFormatter(formatter)
                timed_handler.suffix = "%Y%m%d"  # Set rotation file suffix format
                self.logger.addHandler(timed_handler)

                console_handler = logging.StreamHandler()
                console_handler.setLevel(self.log_level)
                console_handler.setFormatter(formatter)
                self.logger.addHandler(console_handler)

                # Log initialization information
                self.logger.info("Logging system initialized successfully")
                self.logger.info(f"Log directory: {self.log_path}")
                self.logger.info(f"Log file base name: {log_file}")
                self.logger.info(f"Log level: {self.log_level}")

            except Exception as e:
                print(f"Error: Cannot create log directory '{self.log_path}': {e}")
                print("Logs will only be output to console")
        # Ensure logger exists even without file output
        elif self.logger.handlers:
            self.logger.info("Logging system initialized successfully (console output only)")
            self.logger.info(f"Log level: {self.log_level}")

        # Set up third-party library log levels
        self._setup_third_party_logging()

    def reconfigure(self, log_dir: str | None = None) -> None:
        """
        Reconfigure logging system (called by OdaServer)
        
        Args:
            log_dir: Log directory path
        """
        self.logger.info("Reconfiguring logging system")
        # Reinitialize logging system
        self.initialize(log_dir)
        self.logger.info("Logging system reconfiguration completed")

    def _setup_third_party_logging(self) -> None:
        """Set up third-party library log levels"""
        if not self.logger:
            return


    def get_logger(self, name: str | None = None) -> logging.Logger:
        """Get system logger"""
        if not self.logger:
            self.initialize()

        if name:
            return logging.getLogger(f"one_dragon_agent.{name}")
        return self.logger or logging.getLogger("one_dragon_agent")

    def is_debug_enabled(self) -> bool:
        """Check if DEBUG level is enabled"""
        return self.log_level == "DEBUG"

    def is_file_logging_enabled(self) -> bool:
        """Check if file logging is enabled"""
        return bool(self.log_path)


# Global logger manager instance
_od_logger = OdaLogger()


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Get OneDragon-Agent system logger

    Args:
        name: Logger name, typically use module name

    Returns:
        logging.Logger: Configured logger
    """
    return _od_logger.get_logger(name)


def initialize_logging(log_dir: str | None = None, force_reinitialize: bool = False) -> None:
    """
    Initialize OneDragon-Agent logging system
    
    Args:
        log_dir: Log directory path
        force_reinitialize: Whether to force reinitialization
    """
    if force_reinitialize:
        # Reset the initialization flag to allow re-initialization
        OdaLogger._initialized = False
    _od_logger.initialize(log_dir)
