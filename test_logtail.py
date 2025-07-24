# test_logtail.py
import os
import time
from loguru import logger
from dotenv import load_dotenv
from logtail import LogtailHandler

# 1. Load .env file from the current directory
load_dotenv()
logtail_token = os.getenv("LOGTAIL_SOURCE_TOKEN")
logtail_endpoint = os.getenv("LOGTAIL_ENDPOINT") # Your specific URL

# 2. Check if token and endpoint were found
if not logtail_token or not logtail_endpoint:
    print("ERROR: LOGTAIL_SOURCE_TOKEN or LOGTAIL_ENDPOINT not found in .env file.")
else:
    print(f"Token loaded successfully. First 4 chars: {logtail_token[:4]}...")
    print(f"Endpoint loaded successfully: {logtail_endpoint}")

    # 3. Configure logger
    logger.remove()
    handler = LogtailHandler(source_token=logtail_token)

    # 4. THE FIX: Manually override the URL in the handler object
    handler._url = logtail_endpoint

    logger.add(handler, level="INFO")

    # 5. Send a test log
    print("Sending a test log to your specific Better Stack endpoint...")
    logger.info("This is a test log using the manual URL override. It should work now!")
    print("Log sent.")

    # 6. Wait for the log to be sent over the network
    time.sleep(5)
    print("Test finished.")