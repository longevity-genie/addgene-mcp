#!/usr/bin/env python3
"""
Test basic search functionality for Addgene MCP.
Tests basic plasmid search without filters.
"""

import pytest
import asyncio
import os
from typing import List, Dict, Any

from addgene_mcp.server import AddgeneMCP, SearchResult, PlasmidOverview
from eliot import start_action

# Set testing flag to use optimized scrapy settings
os.environ['TESTING'] = 'true'


class TestBasicSearch:
    """Test basic search functionality."""
    
    @pytest.fixture(scope="class")
    def mcp_server(self):
        """Set up the MCP server for testing."""
        return AddgeneMCP()
    
    def test_server_initialization(self, mcp_server):
        """Test that the server initializes correctly."""
        assert mcp_server is not None
        assert hasattr(mcp_server, 'search_plasmids')
    
    @pytest.mark.asyncio
    async def test_basic_search_small_results(self, mcp_server):
        """Test basic plasmid search with small result set."""
        with start_action(action_type="test_basic_search_small") as action:
            # Use a specific query likely to return results quickly
            result = await mcp_server.search_plasmids(
                query="pLKO.1",
                page_size=3,  # Small page size to avoid hanging
                page_number=1
            )
            
            action.log(
                message_type="basic_search_result",
                query="pLKO.1",
                count=result.count,
                returned=len(result.plasmids)
            )
            
            # Basic structure validation
            assert isinstance(result, SearchResult)
            assert result.query == "pLKO.1"
            assert result.page == 1
            assert result.page_size == 3
            assert result.count >= 0, "Should return valid count"
            assert isinstance(result.plasmids, list), "Should return list of plasmids"
            assert len(result.plasmids) <= 3, "Should not return more than requested page size"
            
            # Validate each plasmid structure if any results
            for plasmid in result.plasmids:
                assert isinstance(plasmid, PlasmidOverview)
                assert plasmid.id > 0, f"Plasmid should have valid ID, got {plasmid.id}"
                assert plasmid.name, f"Plasmid should have name, got '{plasmid.name}'"
                assert plasmid.depositor, f"Plasmid should have depositor, got '{plasmid.depositor}'"
                assert isinstance(plasmid.is_industry, bool), "is_industry should be boolean"
    
    @pytest.mark.asyncio
    async def test_search_with_no_query(self, mcp_server):
        """Test search with no specific query (browse mode)."""
        with start_action(action_type="test_no_query_search") as action:
            result = await mcp_server.search_plasmids(
                page_size=2,  # Very small page size
                page_number=1
            )
            
            action.log(
                message_type="no_query_search_result",
                count=result.count,
                returned=len(result.plasmids)
            )
            
            # Structure validation
            assert isinstance(result, SearchResult)
            assert result.page == 1
            assert result.page_size == 2
            assert result.count >= 0, "Should return valid count"
            assert len(result.plasmids) <= 2, "Should not return more than requested page size"
    
    @pytest.mark.asyncio
    async def test_empty_search_results(self, mcp_server):
        """Test handling of empty search results."""
        with start_action(action_type="test_empty_search_results") as action:
            # Search for something very unlikely to exist
            result = await mcp_server.search_plasmids(
                query="VERY_UNLIKELY_PLASMID_NAME_XYZVWTUP123456789",
                page_size=5
            )
            
            action.log(
                message_type="empty_search_result",
                query="VERY_UNLIKELY_PLASMID_NAME_XYZVWTUP123456789",
                count=result.count,
                returned=len(result.plasmids)
            )
            
            # Should handle empty results gracefully
            assert isinstance(result, SearchResult)
            assert isinstance(result.plasmids, list), "Should return empty list"
            assert result.count >= 0, "Count should be valid (>=0)"
            assert len(result.plasmids) >= 0, "Should return valid list length"
    
    @pytest.mark.asyncio
    async def test_search_data_types(self, mcp_server):
        """Test that search returns correct data types."""
        with start_action(action_type="test_search_data_types") as action:
            result = await mcp_server.search_plasmids(
                query="GFP",
                page_size=2
            )
            
            action.log(
                message_type="data_types_validation",
                plasmids_count=len(result.plasmids)
            )
            
            # Test each plasmid has correct data types
            for plasmid in result.plasmids:
                # Required fields
                assert isinstance(plasmid.id, int), f"ID should be integer, got {type(plasmid.id)}"
                assert isinstance(plasmid.name, str), f"Name should be string, got {type(plasmid.name)}"
                assert isinstance(plasmid.depositor, str), f"Depositor should be string, got {type(plasmid.depositor)}"
                assert isinstance(plasmid.is_industry, bool), f"is_industry should be boolean, got {type(plasmid.is_industry)}"
                
                # Optional fields validation
                if plasmid.expression:
                    assert isinstance(plasmid.expression, list), "Expression should be list"
                
                if plasmid.popularity:
                    assert isinstance(plasmid.popularity, str), "Popularity should be string"
                
                if plasmid.article_url:
                    assert str(plasmid.article_url).startswith("http"), \
                        f"Article URL should be valid URL: {plasmid.article_url}"
                
                if plasmid.map_url:
                    assert str(plasmid.map_url).startswith("http"), \
                        f"Map URL should be valid URL: {plasmid.map_url}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 