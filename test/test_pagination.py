#!/usr/bin/env python3
"""
Test pagination functionality for Addgene MCP.
Tests different page sizes and page numbers.
"""

import pytest
import asyncio
import os
from typing import List, Dict, Any

from addgene_mcp.server import AddgeneMCP, SearchResult, PlasmidOverview
from eliot import start_action

# Set testing flag to use optimized scrapy settings
os.environ['TESTING'] = 'true'


class TestPagination:
    """Test pagination functionality."""
    
    @pytest.fixture(scope="class")
    def mcp_server(self):
        """Set up the MCP server for testing."""
        return AddgeneMCP()
    
    @pytest.mark.asyncio
    async def test_pagination_parameters(self, mcp_server):
        """Test pagination parameters with different page sizes."""
        with start_action(action_type="test_pagination_parameters") as action:
            search_query = "GFP"
            
            # Test different page sizes (small values to avoid hanging)
            test_page_sizes = [1, 2, 5]
            
            for page_size in test_page_sizes:
                result = await mcp_server.search_plasmids(
                    query=search_query,
                    page_size=page_size,
                    page_number=1
                )
                
                assert result.page_size == page_size, f"Page size should be {page_size}"
                assert result.page == 1, "Page number should be 1"
                assert len(result.plasmids) <= page_size, f"Should not return more than {page_size} results"
                
                action.log(
                    message_type="page_size_test",
                    page_size=page_size,
                    actual_results=len(result.plasmids)
                )
            
            action.log(
                message_type="pagination_parameters_completed",
                tested_page_sizes=test_page_sizes
            )
    
    @pytest.mark.asyncio
    async def test_pagination_page_numbers(self, mcp_server):
        """Test different page numbers."""
        with start_action(action_type="test_pagination_page_numbers") as action:
            search_query = "p53"
            page_size = 3
            
            # Test different page numbers
            test_pages = [1, 2]
            
            for page_number in test_pages:
                result = await mcp_server.search_plasmids(
                    query=search_query,
                    page_size=page_size,
                    page_number=page_number
                )
                
                assert result.page == page_number, f"Page number should be {page_number}"
                assert result.page_size == page_size, f"Page size should be {page_size}"
                
                action.log(
                    message_type="page_number_test",
                    page_number=page_number,
                    actual_results=len(result.plasmids)
                )
            
            action.log(
                message_type="pagination_page_numbers_completed",
                tested_page_numbers=test_pages
            )
    
    @pytest.mark.asyncio
    async def test_pagination_consistency(self, mcp_server):
        """Test pagination consistency across pages."""
        with start_action(action_type="test_pagination_consistency") as action:
            search_query = "plasmid"
            page_size = 2
            
            # Get first two pages
            page1 = await mcp_server.search_plasmids(
                query=search_query,
                page_size=page_size,
                page_number=1
            )
            
            page2 = await mcp_server.search_plasmids(
                query=search_query,
                page_size=page_size,
                page_number=2
            )
            
            action.log(
                message_type="pagination_consistency_check",
                page1_count=len(page1.plasmids),
                page2_count=len(page2.plasmids),
                page1_total=page1.count,
                page2_total=page2.count
            )
            
            # Total count should be consistent (if both pages have results)
            if len(page1.plasmids) > 0 and len(page2.plasmids) > 0:
                assert page1.count == page2.count, "Total count should be consistent across pages"
                
                # No duplicates between pages
                page1_ids = {p.id for p in page1.plasmids}
                page2_ids = {p.id for p in page2.plasmids}
                overlap = page1_ids.intersection(page2_ids)
                assert len(overlap) == 0, f"Should not have duplicate plasmids between pages, found overlap: {overlap}"
    
    @pytest.mark.asyncio
    async def test_edge_case_page_sizes(self, mcp_server):
        """Test edge cases for page sizes."""
        with start_action(action_type="test_edge_case_page_sizes") as action:
            search_query = "test"
            
            # Test very small page size
            result_small = await mcp_server.search_plasmids(
                query=search_query,
                page_size=1,
                page_number=1
            )
            
            assert result_small.page_size == 1
            assert len(result_small.plasmids) <= 1
            
            # Test larger but reasonable page size
            result_large = await mcp_server.search_plasmids(
                query=search_query,
                page_size=10,
                page_number=1
            )
            
            assert result_large.page_size == 10
            assert len(result_large.plasmids) <= 10
            
            action.log(
                message_type="edge_case_page_sizes_completed",
                small_page_results=len(result_small.plasmids),
                large_page_results=len(result_large.plasmids)
            )
    
    @pytest.mark.asyncio
    async def test_high_page_numbers(self, mcp_server):
        """Test behavior with high page numbers."""
        with start_action(action_type="test_high_page_numbers") as action:
            search_query = "vector"
            
            # Test with a high page number that may not exist
            result = await mcp_server.search_plasmids(
                query=search_query,
                page_size=5,
                page_number=100  # Likely beyond available results
            )
            
            # Should handle gracefully
            assert isinstance(result, SearchResult)
            assert result.page == 100
            assert result.page_size == 5
            assert result.count >= 0
            assert len(result.plasmids) >= 0  # May be 0 if page doesn't exist
            
            action.log(
                message_type="high_page_number_test",
                page_number=100,
                results_found=len(result.plasmids),
                total_count=result.count
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 