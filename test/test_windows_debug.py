#!/usr/bin/env python3
"""Debug test for Windows-specific issues."""

import pytest
import asyncio
import sys
import os
from pathlib import Path
from addgene_mcp.scrapy_addgene.runner import ScrapyManager


@pytest.mark.asyncio
async def test_windows_subprocess_debug():
    """Debug test to check subprocess execution on Windows."""
    
    print(f"Platform: {sys.platform}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Check if environment variables are set correctly
    env_vars = ['TESTING', 'PYTHONIOENCODING', 'PYTHONUNBUFFERED', 'PYTHONUTF8']
    for var in env_vars:
        print(f"{var}: {os.environ.get(var, 'not set')}")
    
    # Check if we can find scrapy
    try:
        import scrapy
        print(f"Scrapy version: {scrapy.__version__}")
        print(f"Scrapy location: {scrapy.__file__}")
    except ImportError as e:
        print(f"Scrapy import error: {e}")
        pytest.skip("Scrapy not available")
    
    # Check PYTHONPATH
    pythonpath = os.environ.get('PYTHONPATH', 'not set')
    print(f"PYTHONPATH: {pythonpath}")
    
    # Test subprocess execution with a simple command first
    try:
        # On Windows with ProactorEventLoop, shell must be False
        process = await asyncio.create_subprocess_exec(
            sys.executable, '-c', 'print("Hello from subprocess")',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if isinstance(stdout, bytes):
            stdout = stdout.decode('utf-8', errors='replace')
        if isinstance(stderr, bytes):
            stderr = stderr.decode('utf-8', errors='replace')
            
        print(f"Simple subprocess test - Return code: {process.returncode}")
        print(f"Stdout: {stdout.strip()}")
        print(f"Stderr: {stderr.strip()}")
        
        assert process.returncode == 0, "Simple subprocess test should succeed"
        
    except Exception as e:
        print(f"Simple subprocess test failed: {e}")
        pytest.fail(f"Basic subprocess execution failed: {e}")
    
    # Test scrapy command availability
    try:
        # On Windows with ProactorEventLoop, shell must be False
        process = await asyncio.create_subprocess_exec(
            sys.executable, '-m', 'scrapy', '--help',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if isinstance(stdout, bytes):
            stdout = stdout.decode('utf-8', errors='replace')
        if isinstance(stderr, bytes):
            stderr = stderr.decode('utf-8', errors='replace')
            
        print(f"Scrapy help test - Return code: {process.returncode}")
        print(f"Stdout preview: {stdout[:200]}...")
        print(f"Stderr preview: {stderr[:200]}...")
        
        if process.returncode != 0:
            print(f"Scrapy help command failed with return code {process.returncode}")
        
    except Exception as e:
        print(f"Scrapy help test failed: {e}")
    
    # Now test our ScrapyManager
    print("\nTesting ScrapyManager...")
    manager = ScrapyManager()
    
    # Test a simple search
    try:
        results = await manager.search_plasmids(query="test", page_size=5, page_number=1)
        print(f"ScrapyManager search returned {len(results)} results")
        
        if len(results) == 0:
            print("Warning: No results returned from ScrapyManager")
        else:
            print("ScrapyManager test successful!")
            
    except Exception as e:
        print(f"ScrapyManager test failed: {e}")
        # Don't fail the test, just report the issue
        pass


if __name__ == "__main__":
    asyncio.run(test_windows_subprocess_debug()) 