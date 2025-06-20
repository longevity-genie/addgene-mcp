"""Scrapy settings for addgene scraping project."""

import os
import sys

BOT_NAME = 'addgene_scraper'

SPIDER_MODULES = ['addgene_mcp.scrapy_addgene.spiders']
NEWSPIDER_MODULE = 'addgene_mcp.scrapy_addgene.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = os.getenv('SCRAPY_ROBOTSTXT_OBEY', 'True').lower() == 'true'

# Configure a delay for requests (in seconds)
DOWNLOAD_DELAY = float(os.getenv('SCRAPY_DOWNLOAD_DELAY', '1.0'))
RANDOMIZE_DOWNLOAD_DELAY = os.getenv('SCRAPY_RANDOMIZE_DOWNLOAD_DELAY', 'True').lower() == 'true'

# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = int(os.getenv('SCRAPY_CONCURRENT_REQUESTS_PER_DOMAIN', '2'))
CONCURRENT_REQUESTS = int(os.getenv('SCRAPY_CONCURRENT_REQUESTS', '8'))

# Disable cookies (enabled by default)
COOKIES_ENABLED = os.getenv('SCRAPY_COOKIES_ENABLED', 'False').lower() == 'true'

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = os.getenv('SCRAPY_TELNETCONSOLE_ENABLED', 'False').lower() == 'true'

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
   'Accept-Language': 'en',
   'User-Agent': os.getenv('SCRAPY_USER_AGENT', 'addgene-mcp/0.1.0 (+https://github.com/your-repo/addgene-mcp)'),
}

# Enable or disable spider middlewares
SPIDER_MIDDLEWARES = {
    'scrapy.spidermiddlewares.httperror.HttpErrorMiddleware': 50,
    'scrapy.spidermiddlewares.offsite.OffsiteMiddleware': 500,
    'scrapy.spidermiddlewares.referer.RefererMiddleware': 700,
    'scrapy.spidermiddlewares.urllength.UrlLengthMiddleware': 800,
    'scrapy.spidermiddlewares.depth.DepthMiddleware': 900,
}

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
}

# Configure item pipelines
ITEM_PIPELINES = {
    'addgene_mcp.scrapy_addgene.pipelines.validation.ValidationPipeline': 300,
    'addgene_mcp.scrapy_addgene.pipelines.duplicates.DuplicatesPipeline': 400,
}

# Enable and configure the AutoThrottle extension
AUTOTHROTTLE_ENABLED = os.getenv('SCRAPY_AUTOTHROTTLE_ENABLED', 'True').lower() == 'true'
AUTOTHROTTLE_START_DELAY = float(os.getenv('SCRAPY_AUTOTHROTTLE_START_DELAY', '1.0'))
AUTOTHROTTLE_MAX_DELAY = float(os.getenv('SCRAPY_AUTOTHROTTLE_MAX_DELAY', '10.0'))
AUTOTHROTTLE_TARGET_CONCURRENCY = float(os.getenv('SCRAPY_AUTOTHROTTLE_TARGET_CONCURRENCY', '2.0'))
AUTOTHROTTLE_DEBUG = os.getenv('SCRAPY_AUTOTHROTTLE_DEBUG', 'False').lower() == 'true'

# Enable and configure HTTP caching
HTTPCACHE_ENABLED = os.getenv('SCRAPY_HTTPCACHE_ENABLED', 'True').lower() == 'true'
HTTPCACHE_EXPIRATION_SECS = int(os.getenv('SCRAPY_HTTPCACHE_EXPIRATION_SECS', '3600'))
HTTPCACHE_DIR = os.getenv('SCRAPY_HTTPCACHE_DIR', 'httpcache')
HTTPCACHE_IGNORE_HTTP_CODES = [403, 404, 500, 502, 503, 504]

# Retry settings
RETRY_ENABLED = os.getenv('SCRAPY_RETRY_ENABLED', 'True').lower() == 'true'
RETRY_TIMES = int(os.getenv('SCRAPY_RETRY_TIMES', '3'))
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Request fingerprinting
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'

# Set settings whose default value is deprecated
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'

# Windows-specific settings
if sys.platform.startswith('win'):
    # Use more conservative settings on Windows
    DOWNLOAD_DELAY = float(os.getenv('SCRAPY_DOWNLOAD_DELAY', '2.0'))
    CONCURRENT_REQUESTS_PER_DOMAIN = int(os.getenv('SCRAPY_CONCURRENT_REQUESTS_PER_DOMAIN', '1'))
    CONCURRENT_REQUESTS = int(os.getenv('SCRAPY_CONCURRENT_REQUESTS', '4'))
    AUTOTHROTTLE_START_DELAY = float(os.getenv('SCRAPY_AUTOTHROTTLE_START_DELAY', '2.0'))
    AUTOTHROTTLE_MAX_DELAY = float(os.getenv('SCRAPY_AUTOTHROTTLE_MAX_DELAY', '15.0'))

# Test specific settings - use smaller values for testing to avoid hanging
if os.getenv('TESTING', 'False').lower() == 'true':
    DOWNLOAD_DELAY = float(os.getenv('TEST_SCRAPY_DOWNLOAD_DELAY', '0.5'))
    CONCURRENT_REQUESTS_PER_DOMAIN = int(os.getenv('TEST_SCRAPY_CONCURRENT_REQUESTS_PER_DOMAIN', '1'))
    CONCURRENT_REQUESTS = int(os.getenv('TEST_SCRAPY_CONCURRENT_REQUESTS', '4'))
    AUTOTHROTTLE_START_DELAY = float(os.getenv('TEST_SCRAPY_AUTOTHROTTLE_START_DELAY', '0.5'))
    AUTOTHROTTLE_MAX_DELAY = float(os.getenv('TEST_SCRAPY_AUTOTHROTTLE_MAX_DELAY', '5.0'))
    HTTPCACHE_EXPIRATION_SECS = int(os.getenv('TEST_SCRAPY_HTTPCACHE_EXPIRATION_SECS', '1800'))
    
    # Windows test specific settings
    if sys.platform.startswith('win'):
        DOWNLOAD_DELAY = float(os.getenv('TEST_SCRAPY_DOWNLOAD_DELAY', '1.0'))
        CONCURRENT_REQUESTS_PER_DOMAIN = int(os.getenv('TEST_SCRAPY_CONCURRENT_REQUESTS_PER_DOMAIN', '1'))
        CONCURRENT_REQUESTS = int(os.getenv('TEST_SCRAPY_CONCURRENT_REQUESTS', '2'))
        AUTOTHROTTLE_START_DELAY = float(os.getenv('TEST_SCRAPY_AUTOTHROTTLE_START_DELAY', '1.0'))
        AUTOTHROTTLE_MAX_DELAY = float(os.getenv('TEST_SCRAPY_AUTOTHROTTLE_MAX_DELAY', '8.0')) 