"""
This file is the main entry point for pytest configuration.
We use it to set up the Scrapy/Twisted event loop reactor *before*
any tests are run, which is critical for ensuring that Scrapy and
the asyncio event loop used by pytest can coexist.
"""

import os
import pytest

# Set testing environment variables
os.environ['TESTING'] = 'true'
os.environ['TEST_SCRAPY_DOWNLOAD_DELAY'] = '0.1' 