# Addgene MCP Testing

This directory contains comprehensive tests for the Addgene MCP server, split into focused test files for better organization and maintainability.

## Test Structure

The comprehensive test suite has been split into the following files:

### 🔍 `test_basic_search.py`
Tests basic search functionality without filters:
- Server initialization
- Basic plasmid search with small result sets
- Search with no query (browse mode)
- Empty search results handling
- Data type validation

### 📄 `test_pagination.py`
Tests pagination functionality:
- Different page sizes
- Different page numbers
- Pagination consistency across pages
- Edge cases (extreme page sizes/numbers)

### 🔧 `test_filters.py`
Tests search filter functionality:
- Expression system filters (mammalian, bacterial, etc.)
- Vector type filters (lentiviral, CRISPR, etc.)
- Species filters (human, mouse, etc.)
- Popularity filters
- Plasmid type filters
- Resistance marker filters
- Multiple filter combinations

### ⚠️ `test_error_handling.py`
Tests error handling and edge cases:
- Empty/None queries
- Special characters in queries
- Unicode characters
- Extreme parameter values
- Invalid filter values
- Network resilience

## Environment Configuration

The tests use environment variables for Scrapy configuration to avoid hanging and provide reasonable defaults:

### Testing-Specific Settings
When `TESTING=true` is set, the following optimized settings are used:

```bash
# Download delays (faster for testing)
TEST_SCRAPY_DOWNLOAD_DELAY=0.5
TEST_SCRAPY_AUTOTHROTTLE_START_DELAY=0.5
TEST_SCRAPY_AUTOTHROTTLE_MAX_DELAY=5.0

# Concurrency (reduced for testing)
TEST_SCRAPY_CONCURRENT_REQUESTS_PER_DOMAIN=1
TEST_SCRAPY_CONCURRENT_REQUESTS=4

# Timeouts (shorter for testing)
TEST_SCRAPY_DOWNLOAD_TIMEOUT=30
TEST_SCRAPY_RETRY_TIMES=2
SCRAPY_TIMEOUT_SECONDS=120
```

### Production Settings
For production use, the following environment variables can be configured:

```bash
# Basic settings
SCRAPY_ROBOTSTXT_OBEY=true
SCRAPY_DOWNLOAD_DELAY=1.0
SCRAPY_RANDOMIZE_DOWNLOAD_DELAY=true

# Concurrency
SCRAPY_CONCURRENT_REQUESTS_PER_DOMAIN=2
SCRAPY_CONCURRENT_REQUESTS=8

# AutoThrottle
SCRAPY_AUTOTHROTTLE_ENABLED=true
SCRAPY_AUTOTHROTTLE_START_DELAY=1.0
SCRAPY_AUTOTHROTTLE_MAX_DELAY=10.0
SCRAPY_AUTOTHROTTLE_TARGET_CONCURRENCY=2.0

# Caching
SCRAPY_HTTPCACHE_ENABLED=true
SCRAPY_HTTPCACHE_EXPIRATION_SECS=3600

# Retry settings
SCRAPY_RETRY_ENABLED=true
SCRAPY_RETRY_TIMES=3

# User agent
SCRAPY_USER_AGENT="addgene-mcp/0.1.0 (+https://github.com/your-repo/addgene-mcp)"
```

## Running Tests

### Run All Tests
```bash
# Using the test runner script
python test/run_tests.py

# Or using pytest directly
pytest test/ -v
```

### Run Individual Test Files
```bash
# Basic search tests
pytest test/test_basic_search.py -v

# Pagination tests
pytest test/test_pagination.py -v

# Filter tests
pytest test/test_filters.py -v

# Error handling tests
pytest test/test_error_handling.py -v
```

### Run with Specific Markers
```bash
# Run only slow tests
pytest test/ -m slow -v

# Skip slow tests
pytest test/ -m "not slow" -v

# Run integration tests
pytest test/ -m integration -v
```

## Async Handling Improvements

The tests now include proper async handling to prevent hanging:

1. **Timeout Management**: All spider operations have configurable timeouts
2. **Reactor Setup**: Improved Twisted reactor installation and management
3. **Error Recovery**: Graceful handling of timeouts and errors
4. **Resource Cleanup**: Proper cleanup of async resources

## Test Configuration

The `pytest.ini` file includes:
- Async mode configuration
- Warning filters for Scrapy/Twisted
- Environment variable setup
- Timeout configuration
- Test markers

## Troubleshooting

### Tests Hanging
If tests hang:
1. Check `SCRAPY_TIMEOUT_SECONDS` environment variable
2. Reduce `TEST_SCRAPY_DOWNLOAD_DELAY` for faster testing
3. Ensure `TESTING=true` is set for optimized settings

### Network Issues
If network issues occur:
1. Check internet connectivity
2. Verify Addgene website accessibility
3. Adjust retry settings via environment variables

### Reactor Issues
If Twisted reactor issues occur:
1. Ensure only one reactor is installed per process
2. Check for conflicting async libraries
3. Use separate test processes for isolation

## Real Requests vs Mocking

These tests perform **real requests** to the Addgene website as requested. This means:
- Tests require internet connectivity
- Tests may be slower than mocked tests
- Tests validate actual website functionality
- Tests may occasionally fail due to network issues

For faster development cycles, consider creating additional mock tests alongside these integration tests. 