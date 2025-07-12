"""Logging service for structured logging."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .redis_service import RedisService


class LoggingService:
    """Handles structured logging with file and console output."""
    
    def __init__(self, run_id: str, variation_id: str, log_dir: str, debug: bool = False):
        self.run_id = run_id
        self.variation_id = variation_id
        self.debug = debug
        self.redis_service: Optional["RedisService"] = None
        
        # Ensure log directory exists
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Setup file logger
        log_file = log_path / f"agent_{run_id}_{variation_id}.log"
        self.file_logger = self._setup_file_logger(log_file)
        
    def _setup_file_logger(self, log_file: Path) -> logging.Logger:
        """Setup file-only logger."""
        logger = logging.getLogger(f"agent_{self.run_id}_{self.variation_id}")
        logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        logger.handlers = []
        
        # Add file handler only
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        return logger
    
    def set_redis_service(self, redis_service: "RedisService") -> None:
        """Set Redis service for publishing logs."""
        self.redis_service = redis_service
    
    def log(self, message: str, level: str = "INFO", **kwargs) -> Dict[str, Any]:
        """Create structured log entry."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "run_id": self.run_id,
            "variation_id": self.variation_id,
            "level": level,
            "message": message,
            **kwargs
        }
        
        # Always output to stdout (not just in debug mode)
        print(json.dumps(log_entry), flush=True)
        
        # Log to file
        self.file_logger.log(
            getattr(logging, level, logging.INFO),
            f"{message} | {json.dumps(kwargs) if kwargs else ''}"
        )
        
        return log_entry
    
    def log_progress(self, message: str, detail: str = "") -> Dict[str, Any]:
        """Log progress update."""
        return self.log(f"⚡ {message}", "INFO", detail=detail)
    
    def log_error(self, error: str, exception: Optional[Exception] = None) -> Dict[str, Any]:
        """Log error with exception details."""
        error_data = {"error": error}
        if exception:
            error_data["exception"] = str(exception)
            error_data["exception_type"] = type(exception).__name__
        return self.log(f"❌ {error}", "ERROR", **error_data)