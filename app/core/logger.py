# app/core/logger.py - FINAL PRODUCTION VERSION

import os
import sys
import json
from pathlib import Path

import requests
from loguru import logger
from dotenv import load_dotenv

# --- Suppress InsecureRequestWarning ---
# This disables the warning message from requests, cleaning up your journalctl output.
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


# --- Load Environment Variables ---
load_dotenv()
LOGTAIL_TOKEN = os.getenv("LOGTAIL_SOURCE_TOKEN")
LOGTAIL_ENDPOINT = os.getenv("LOGTAIL_ENDPOINT")


# --- Define the Custom Sink for Better Stack ---
def betterstack_sink(message):
    """
    This function is called by Loguru for each log record.
    It sends the log to Better Stack using the requests library.
    """
    try:
        record = message.record
        payload = {
            "message": message.strip(),
            "level": record["level"].name,
            "timestamp": record["time"].isoformat(),
            # Add structured data from the log record for better searching
            "metadata": {
                "module": record["extra"].get("module", "unknown"),
                "function": record["function"],
                "line": record["line"],
            }
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LOGTAIL_TOKEN}"
        }
        # Send the request with a timeout
        response = requests.post(LOGTAIL_ENDPOINT, json=[payload], headers=headers, verify=False, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
    except Exception as e:
        # If sending fails, print a single, clear error to stderr.
        # This will appear in `journalctl` if there's a problem.
        print(f"ERROR: [betterstack_sink] Failed to send log: {e}", file=sys.stderr)


# --- Configure Loguru ---
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger.remove() # Start with a clean slate

# Sink 1: Local File Logging (still enqueued for performance)
# This is your reliable local backup.
logger.add(
    LOG_DIR / "assistant.log",
    rotation="500 KB",
    retention="7 days",
    level="DEBUG",
    backtrace=True,
    diagnose=True,
    enqueue=True, # Keep local file logging fast and non-blocking
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[module]}:{function}:{line} - {message}"
)

# Sink 2: Remote Cloud Logging (synchronous for reliability)
if LOGTAIL_TOKEN and LOGTAIL_ENDPOINT:
    logger.add(
        betterstack_sink,
        level="INFO",
        # THE FIX: Run synchronously to guarantee logs are sent from a service.
        enqueue=False,
    )
else:
    # If remote logging is disabled, add a console sink as a fallback so you still see output.
    logger.add(sys.stderr, level="INFO")
    logger.warning("Remote logging is disabled. Check .env file.")


# --- Your Original get_logger Function (Unchanged) ---
def get_logger(name: str):
    """Binds the module name to the logger context."""
    return logger.bind(module=name)

# --- Log initial status ---
# This log will now be sent synchronously to the cloud if configured.
initial_log = logger.bind(module="logger_setup")
if LOGTAIL_TOKEN and LOGTAIL_ENDPOINT:
    initial_log.info("Logger initialized. Remote logging is active.")
else:
    initial_log.warning("Logger initialized. Remote logging is disabled.")