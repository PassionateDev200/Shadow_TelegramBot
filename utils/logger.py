import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from config import config

def setup_logging():
    """Enhanced logging setup with file rotation and better formatting"""
    
    # Ensure log directory exists
    log_dir = config.LOG_DIR if os.path.isabs(config.LOG_DIR) else os.path.join(config.BASE_DIR, config.LOG_DIR)
    os.makedirs(log_dir, exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s:%(lineno)-4d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # Main log file with rotation
    main_log_file = os.path.join(log_dir, 'shadow_bot.log')
    main_handler = RotatingFileHandler(
        main_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    main_handler.setLevel(logging.INFO)
    main_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(main_handler)
    
    # Error log file
    error_log_file = os.path.join(log_dir, 'errors.log')
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # Rebalancing activity log
    rebalance_log_file = os.path.join(log_dir, 'rebalancing.log')
    rebalance_handler = RotatingFileHandler(
        rebalance_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    rebalance_handler.setLevel(logging.INFO)
    rebalance_handler.setFormatter(detailed_formatter)
    
    # Create rebalancing logger
    rebalance_logger = logging.getLogger('rebalancing')
    rebalance_logger.addHandler(rebalance_handler)
    rebalance_logger.setLevel(logging.INFO)
    rebalance_logger.propagate = False  # Don't propagate to root logger
    
    # Reduce noise from external libraries
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('playwright').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    # Log startup message
    logging.info("=" * 60)
    logging.info(f"Shadow Liquidity Bot Starting - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"Log Directory: {log_dir}")
    logging.info(f"Main Log: {main_log_file}")
    logging.info(f"Error Log: {error_log_file}")
    logging.info(f"Rebalancing Log: {rebalance_log_file}")
    logging.info("=" * 60)

def get_rebalance_logger():
    """Get the dedicated rebalancing logger"""
    return logging.getLogger('rebalancing')

def log_rebalance_event(pool_id: str, event: str, details: dict = None):
    """Log rebalancing events with structured data"""
    rebalance_logger = get_rebalance_logger()
    
    message = f"Pool {pool_id}: {event}"
    if details:
        detail_str = " | ".join([f"{k}={v}" for k, v in details.items()])
        message += f" | {detail_str}"
    
    rebalance_logger.info(message)
