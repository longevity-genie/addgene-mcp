"""
This file is the main entry point for pytest configuration.
We use it to set up the Scrapy/Twisted event loop reactor *before*
any tests are run, which is critical for ensuring that Scrapy and
the asyncio event loop used by pytest can coexist.
"""

import os
import pytest

# Set testing environment variables - these will be available for all tests
os.environ['TESTING'] = 'true'
os.environ['TEST_SCRAPY_DOWNLOAD_DELAY'] = '0.1'  # Faster for tests
os.environ['TEST_SCRAPY_CONCURRENT_REQUESTS_PER_DOMAIN'] = '1'
os.environ['TEST_SCRAPY_CONCURRENT_REQUESTS'] = '4'
os.environ['TEST_SCRAPY_AUTOTHROTTLE_START_DELAY'] = '0.5'
os.environ['TEST_SCRAPY_AUTOTHROTTLE_MAX_DELAY'] = '5.0'
os.environ['TEST_SCRAPY_DOWNLOAD_TIMEOUT'] = '30'
os.environ['TEST_SCRAPY_RETRY_TIMES'] = '2'
os.environ['SCRAPY_TIMEOUT_SECONDS'] = '120'

def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)
        
        # Mark potentially slow tests
        if any(keyword in item.nodeid.lower() for keyword in ["error_handling", "comprehensive"]):
            item.add_marker(pytest.mark.slow) 