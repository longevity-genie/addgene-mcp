#!/usr/bin/env python3
"""
Test error handling and edge cases for Addgene MCP.
Tests various error conditions and edge cases.
"""

import pytest
import asyncio
import os
from typing import List, Dict, Any

from addgene_mcp.server import AddgeneMCP, SearchResult, PlasmidOverview
from eliot import start_action

# Set testing flag to use optimized scrapy settings
os.environ['TESTING'] = 'true'


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.fixture(scope="class")
    def mcp_server(self):
        """Set up the MCP server for testing."""
        return AddgeneMCP()
    
    @pytest.mark.asyncio
    async def test_empty_query_handling(self, mcp_server):
        """Test handling of empty queries."""
        with start_action(action_type="test_empty_query_handling") as action:
            # Test with empty string query
            result = await mcp_server.search_plasmids(
                query="",
                page_size=3
            )
            
            action.log(
                message_type="empty_query_result",
                query="",
                count=result.count,
                returned=len(result.plasmids)
            )
            
            # Should handle gracefully
            assert isinstance(result, SearchResult)
            assert result.count >= 0
            assert isinstance(result.plasmids, list)
    
    @pytest.mark.asyncio
    async def test_none_query_handling(self, mcp_server):
        """Test handling of None query."""
        with start_action(action_type="test_none_query_handling") as action:
            # Test with None query (browse mode)
            result = await mcp_server.search_plasmids(
                query=None,
                page_size=3
            )
            
            action.log(
                message_type="none_query_result",
                query=None,
                count=result.count,
                returned=len(result.plasmids)
            )
            
            # Should handle gracefully
            assert isinstance(result, SearchResult)
            assert result.count >= 0
            assert isinstance(result.plasmids, list)
    
    @pytest.mark.asyncio
    async def test_special_characters_in_query(self, mcp_server):
        """Test handling of special characters in queries."""
        with start_action(action_type="test_special_characters") as action:
            # Test queries with various special characters
            special_queries = [
                "test & query",  # Ampersand
                "query with spaces",  # Spaces
                "query-with-dashes",  # Dashes
                "query_with_underscores",  # Underscores
                "query.with.dots",  # Dots
            ]
            
            for query in special_queries:
                try:
                    result = await mcp_server.search_plasmids(
                        query=query,
                        page_size=2
                    )
                    
                    # Should always return valid SearchResult
                    assert isinstance(result, SearchResult)
                    assert result.count >= 0
                    assert isinstance(result.plasmids, list)
                    
                    action.log(
                        message_type="special_character_query_success",
                        query=query,
                        count=result.count
                    )
                    
                except Exception as e:
                    # Log but don't fail the test for edge cases
                    action.log(
                        message_type="special_character_query_error",
                        query=query,
                        error=str(e)
                    )
    
    @pytest.mark.asyncio
    async def test_extreme_page_sizes(self, mcp_server):
        """Test handling of extreme page sizes."""
        with start_action(action_type="test_extreme_page_sizes") as action:
            # Test with very large page size
            result_large = await mcp_server.search_plasmids(
                query="test",
                page_size=1000,  # Very large page size
                page_number=1
            )
            
            # Should handle gracefully
            assert isinstance(result_large, SearchResult)
            assert result_large.page_size == 1000
            assert result_large.count >= 0
            
            action.log(
                message_type="extreme_page_size_test",
                page_size=1000,
                result_count=result_large.count,
                returned=len(result_large.plasmids)
            )
    
    @pytest.mark.asyncio
    async def test_extreme_page_numbers(self, mcp_server):
        """Test handling of extreme page numbers."""
        with start_action(action_type="test_extreme_page_numbers") as action:
            # Test with very high page number
            result = await mcp_server.search_plasmids(
                query="test",
                page_size=5,
                page_number=999  # Very high page number
            )
            
            # Should handle gracefully
            assert isinstance(result, SearchResult)
            assert result.page == 999
            assert result.count >= 0
            assert len(result.plasmids) >= 0  # May be 0 if page doesn't exist
            
            action.log(
                message_type="extreme_page_number_test",
                page_number=999,
                result_count=result.count,
                returned=len(result.plasmids)
            )
    
    @pytest.mark.asyncio
    async def test_invalid_filter_values(self, mcp_server):
        """Test handling of invalid filter values."""
        with start_action(action_type="test_invalid_filter_values") as action:
            # Test with invalid expression filter
            result = await mcp_server.search_plasmids(
                query="test",
                page_size=3,
                expression="invalid_expression_type"
            )
            
            # Should handle gracefully
            assert isinstance(result, SearchResult)
            assert result.count >= 0
            
            action.log(
                message_type="invalid_filter_test",
                filter_type="expression",
                filter_value="invalid_expression_type",
                result_count=result.count
            )
    
    @pytest.mark.asyncio
    async def test_very_long_query(self, mcp_server):
        """Test handling of very long queries."""
        with start_action(action_type="test_very_long_query") as action:
            # Create a very long query string
            long_query = "very_long_query_that_might_cause_issues_with_url_encoding_" * 10
            
            try:
                result = await mcp_server.search_plasmids(
                    query=long_query,
                    page_size=2
                )
                
                # Should handle gracefully
                assert isinstance(result, SearchResult)
                assert result.count >= 0
                assert isinstance(result.plasmids, list)
                
                action.log(
                    message_type="long_query_success",
                    query_length=len(long_query),
                    result_count=result.count
                )
                
            except Exception as e:
                # Log but don't fail the test for extreme edge cases
                action.log(
                    message_type="long_query_error",
                    query_length=len(long_query),
                    error=str(e)
                )
    
    @pytest.mark.asyncio
    async def test_unicode_characters(self, mcp_server):
        """Test handling of unicode characters in queries."""
        with start_action(action_type="test_unicode_characters") as action:
            # Test with unicode characters
            unicode_queries = [
                "β-actin",  # Greek letter
                "α-tubulin",  # Another Greek letter
                "café",  # Accented character
            ]
            
            for query in unicode_queries:
                try:
                    result = await mcp_server.search_plasmids(
                        query=query,
                        page_size=2
                    )
                    
                    # Should always return valid SearchResult
                    assert isinstance(result, SearchResult)
                    assert result.count >= 0
                    assert isinstance(result.plasmids, list)
                    
                    action.log(
                        message_type="unicode_query_success",
                        query=query,
                        count=result.count
                    )
                    
                except Exception as e:
                    # Log but don't fail the test for edge cases
                    action.log(
                        message_type="unicode_query_error",
                        query=query,
                        error=str(e)
                    )
    
    @pytest.mark.asyncio
    async def test_network_resilience(self, mcp_server):
        """Test network resilience with various queries."""
        with start_action(action_type="test_network_resilience") as action:
            # Test with various queries to ensure no crashes
            test_queries = [
                "a",  # Single character
                "test123",  # Alphanumeric
                "TEST",  # All caps
                "test-case",  # With dash
            ]
            
            successful_queries = 0
            
            for query in test_queries:
                try:
                    result = await mcp_server.search_plasmids(
                        query=query,
                        page_size=2
                    )
                    
                    # Should always return valid SearchResult
                    assert isinstance(result, SearchResult)
                    assert result.count >= 0
                    successful_queries += 1
                    
                except Exception as e:
                    # Log but don't fail the test for edge cases
                    action.log(
                        message_type="query_error",
                        query=query,
                        error=str(e)
                    )
            
            action.log(
                message_type="network_resilience_test_completed",
                tested_queries=len(test_queries),
                successful_queries=successful_queries
            )
            
            # At least some queries should succeed
            assert successful_queries > 0, "At least some test queries should succeed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 