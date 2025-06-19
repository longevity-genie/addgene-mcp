#!/usr/bin/env python3
"""
Simple validation tests that don't require scrapy.
These tests validate the basic structure and setup.
"""

import pytest
import asyncio
import os
from typing import List, Dict, Any

from addgene_mcp.server import AddgeneMCP, SearchResult, PlasmidOverview
from eliot import start_action

# Set testing flag to use optimized scrapy settings
os.environ['TESTING'] = 'true'


class TestSimpleValidation:
    """Simple validation tests that don't require network access."""
    
    def test_server_initialization(self):
        """Test that the server initializes correctly."""
        server = AddgeneMCP()
        assert server is not None
        assert hasattr(server, 'search_plasmids')
    
    def test_plasmid_overview_model(self):
        """Test PlasmidOverview model creation and validation."""
        plasmid = PlasmidOverview(
            id=12345,
            name="Test Plasmid",
            depositor="Test Lab",
            purpose="Testing purposes",
            plasmid_type="single_insert",
            vector_type="Lentiviral",
            popularity="high",
            expression=["mammalian"],
            is_industry=False
        )
        
        # Validate structure
        assert isinstance(plasmid.id, int)
        assert isinstance(plasmid.name, str)
        assert isinstance(plasmid.depositor, str)
        assert isinstance(plasmid.is_industry, bool)
        assert isinstance(plasmid.expression, list)
        assert plasmid.expression[0] == "mammalian"
    
    def test_search_result_model(self):
        """Test SearchResult model creation and validation."""
        plasmid = PlasmidOverview(
            id=12345,
            name="Test Plasmid",
            depositor="Test Lab",
            is_industry=False
        )
        
        result = SearchResult(
            plasmids=[plasmid],
            count=1,
            query="test",
            page=1,
            page_size=10
        )
        
        # Validate structure
        assert isinstance(result, SearchResult)
        assert result.query == "test"
        assert result.page == 1
        assert result.page_size == 10
        assert result.count == 1
        assert isinstance(result.plasmids, list)
        assert len(result.plasmids) == 1
    
    def test_environment_variables(self):
        """Test that environment variables are properly set for testing."""
        assert os.getenv('TESTING') == 'true'
        
        # Check if testing variables are available (may not be set yet)
        download_delay = os.getenv('TEST_SCRAPY_DOWNLOAD_DELAY')
        if download_delay:
            assert float(download_delay) <= 1.0  # Should be optimized for testing
    
    @pytest.mark.asyncio
    async def test_simple_async_function(self):
        """Test that async functions work correctly."""
        
        async def simple_async_task():
            await asyncio.sleep(0.1)  # Very short sleep
            return "async_result"
        
        result = await simple_async_task()
        assert result == "async_result"
    
    def test_eliot_logging(self):
        """Test that eliot logging works correctly."""
        with start_action(action_type="test_eliot_logging") as action:
            action.log(message_type="test_message", test_data="test_value")
            # If we get here without exception, logging works
            assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 