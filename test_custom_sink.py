# test_custom_sink.py
import os
import sys
import json
import time
import requests
from loguru import logger
from dotenv import load_dotenv

# 1. Load .env file
load_dotenv()
logtail_token = os.getenv("LOGTAIL_SOURCE_TOKEN")
logtail_endpoint = os.getenv("LOGTAIL_ENDPOINT")

# 2. Define our own custom sink function
def betterstack_sink(message):
    """
    This function is called by Loguru for each log record.
    It sends the log to Better Stack using the requests library.
    """
    try:
        # Prepare the log record in a format Better Stack understands
        payload = {
            "message": message.strip(),
            "level": message.record["level"].name,
            # Add any other metadata you want from the log record
            "module": message.record["extra"].get("module", "unknown"),
            "function": message.record["function"],
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {logtail_token}"
        }

        # THE FIX: We use requests directly and set verify=False.
        # This is the equivalent of curl's --insecure flag.
        response = requests.post(logtail_endpoint, json=[payload], headers=headers, verify=False)
        
        # This will raise an error if the server response is not OK (e.g., 401 Unauthorized)
        response.raise_for_status()

    except Exception as e:
        # This will print any errors to the console so we can see them
        print(f"ERROR: Could not send log to Better Stack: {e}", file=sys.stderr)


# 3. Check if config is loaded
if not logtail_token or not logtail_endpoint:
    print("ERROR: LOGTAIL_SOURCE_TOKEN or LOGTAIL_ENDPOINT not found in .env file.")
else:
    print("Config loaded successfully. Testing custom sink...")

    # 4. Configure Loguru to use our custom sink
    logger.remove() # Start fresh
    logger.add(betterstack_sink, level="INFO", enqueue=True) # Our remote logger
    logger.add(sys.stderr, level="INFO") # A local logger to see output

    # Bind a module name like your main app does
    test_logger = logger.bind(module="custom_sink_test")

    # 5. Send a test log
    test_logger.info("This is a final test using a fully custom sink.")
    print("Log sent via custom sink.")
    
    # Wait for the enqueued log to be sent
    time.sleep(5)
    print("Test finished.")