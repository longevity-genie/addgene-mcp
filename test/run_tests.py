#!/usr/bin/env python3
"""
Test runner script for Addgene MCP tests.
Runs split test files with proper organization and reporting.
"""

import subprocess
import sys
import os
from pathlib import Path

# Set testing environment variables
os.environ['TESTING'] = 'true'
os.environ['TEST_SCRAPY_DOWNLOAD_DELAY'] = '0.5'
os.environ['TEST_SCRAPY_CONCURRENT_REQUESTS_PER_DOMAIN'] = '1'
os.environ['TEST_SCRAPY_CONCURRENT_REQUESTS'] = '4'
os.environ['TEST_SCRAPY_AUTOTHROTTLE_START_DELAY'] = '0.5'
os.environ['TEST_SCRAPY_AUTOTHROTTLE_MAX_DELAY'] = '5.0'
os.environ['TEST_SCRAPY_DOWNLOAD_TIMEOUT'] = '30'
os.environ['TEST_SCRAPY_RETRY_TIMES'] = '2'
os.environ['SCRAPY_TIMEOUT_SECONDS'] = '120'

def run_test_file(test_file: str, description: str) -> bool:
    """Run a single test file and return success status."""
    print(f"\n{'='*60}")
    print(f"🧪 Running {description}")
    print(f"📄 File: {test_file}")
    print(f"{'='*60}")
    
    try:
        # Run pytest on the specific file
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            test_file, 
            "-v", 
            "--tb=short",
            "-x"  # Stop on first failure
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            return False
            
    except Exception as e:
        print(f"💥 {description} - ERROR: {e}")
        return False

def main():
    """Run all split test files."""
    print("🚀 Addgene MCP Test Suite")
    print("=" * 60)
    
    # Get the test directory
    test_dir = Path(__file__).parent
    
    # Define test files in order of execution
    test_files = [
        (test_dir / "test_simple_validation.py", "Simple Validation Tests"),
        (test_dir / "test_basic_search.py", "Basic Search Tests"),
        (test_dir / "test_pagination.py", "Pagination Tests"),
        (test_dir / "test_filters.py", "Filter Tests"),
        (test_dir / "test_error_handling.py", "Error Handling Tests"),
    ]
    
    # Track results
    results = []
    
    for test_file, description in test_files:
        if test_file.exists():
            success = run_test_file(str(test_file), description)
            results.append((description, success))
        else:
            print(f"⚠️  Test file not found: {test_file}")
            results.append((description, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {description}")
    
    print(f"\n🎯 Results: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All test suites passed!")
        return 0
    else:
        print("💔 Some test suites failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 