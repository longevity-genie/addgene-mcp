#!/usr/bin/env python3
"""Test case for Alzheimer plasmid search using Addgene MCP functions."""

import pytest
import asyncio
from typing import List, Dict, Any

from addgene_mcp.server import AddgeneMCP, SearchResult, PlasmidOverview
from eliot import start_action


class TestAlzheimerSearch:
    """Test cases for Alzheimer-related plasmid searches."""
    
    @pytest.fixture(scope="class")
    def mcp_server(self):
        """Set up the MCP server for testing."""
        return AddgeneMCP()
    
    @pytest.mark.asyncio
    async def test_alzheimer_search_basic(self, mcp_server):
        """Test basic Alzheimer search functionality."""
        with start_action(action_type="test_alzheimer_search_basic") as action:
            # Search for "alzheimer" with a reasonable page size to get more results
            result = await mcp_server.search_plasmids(
                query="alzheimer",
                page_size=60,  # Get more than expected 52 to ensure we capture all
                page_number=1
            )
            
            # Verify the result structure
            assert isinstance(result, SearchResult)
            assert result.query == "alzheimer"
            assert result.page == 1
            assert result.page_size == 60
            
            # Log the actual results for debugging
            action.log(
                message_type="search_results",
                total_count=result.count,
                actual_plasmids=len(result.plasmids)
            )
            
            # Basic assertion - we should get some results
            assert result.count > 0, "Should find at least some Alzheimer-related plasmids"
            assert len(result.plasmids) > 0, "Should return actual plasmid objects"
            
            # Verify each plasmid has required fields
            for plasmid in result.plasmids:
                assert isinstance(plasmid, PlasmidOverview)
                assert plasmid.id > 0, f"Plasmid should have valid ID, got {plasmid.id}"
                assert plasmid.name, f"Plasmid should have name, got '{plasmid.name}'"
                assert plasmid.depositor, f"Plasmid should have depositor, got '{plasmid.depositor}'"
            
            return result
    
    @pytest.mark.asyncio
    async def test_alzheimer_search_expected_count(self, mcp_server):
        """Test that Alzheimer search returns exactly 52 results."""
        with start_action(action_type="test_alzheimer_search_expected_count") as action:
            # Search with larger page size to capture all results
            result = await mcp_server.search_plasmids(
                query="alzheimer",
                page_size=100,  # Large enough to get all results
                page_number=1
            )
            
            action.log(
                message_type="count_verification",
                expected_count=52,
                actual_count=result.count,
                plasmids_returned=len(result.plasmids)
            )
            
            # Direct assertion as specified by user
            assert result.count == 52, f"Expected exactly 52 results, got {result.count}"
            
            return result
    
    @pytest.mark.asyncio
    async def test_pt7c_hspa1l_in_results(self, mcp_server):
        """Test that pT7C-HSPA1L plasmid (ID 177660) appears in the search results."""
        with start_action(action_type="test_pt7c_hspa1l_in_results") as action:
            # Search for alzheimer and look for the specific plasmid
            result = await mcp_server.search_plasmids(
                query="alzheimer",
                page_size=60,  # Should be enough to include this plasmid
                page_number=1
            )
            
            # Look for the specific plasmid
            target_plasmid = None
            target_id = 177660
            target_name = "pT7C-HSPA1L"
            
            for plasmid in result.plasmids:
                if plasmid.id == target_id:
                    target_plasmid = plasmid
                    break
            
            action.log(
                message_type="target_plasmid_search",
                target_id=target_id,
                target_name=target_name,
                found=target_plasmid is not None,
                plasmid_data=target_plasmid.model_dump() if target_plasmid else None
            )
            
            # Direct assertions as specified by user
            assert target_plasmid is not None, f"Should find plasmid ID {target_id} in Alzheimer search results"
            assert target_plasmid.id == target_id, f"Expected ID {target_id}, got {target_plasmid.id}"
            assert target_name in target_plasmid.name, f"Expected name to contain '{target_name}', got '{target_plasmid.name}'"
            
            return target_plasmid
    
    @pytest.mark.asyncio
    async def test_alzheimer_search_early_results(self, mcp_server):
        """Test that pT7C-HSPA1L appears in the beginning of search results."""
        with start_action(action_type="test_alzheimer_search_early_results") as action:
            # Get first 10 results to check if target plasmid appears in beginning
            result = await mcp_server.search_plasmids(
                query="alzheimer",
                page_size=10,
                page_number=1
            )
            
            target_id = 177660
            found_position = None
            
            for i, plasmid in enumerate(result.plasmids):
                if plasmid.id == target_id:
                    found_position = i + 1  # 1-based position
                    break
            
            action.log(
                message_type="early_results_check",
                target_id=target_id,
                found_position=found_position,
                total_in_first_page=len(result.plasmids)
            )
            
            # Direct assertion: plasmid should be in the beginning (first 10 results)
            assert found_position is not None, f"Should find plasmid ID {target_id} in first 10 results (beginning)"
            
            return found_position
    
    @pytest.mark.asyncio
    async def test_alzheimer_search_pagination(self, mcp_server):
        """Test pagination functionality with Alzheimer search."""
        with start_action(action_type="test_alzheimer_search_pagination") as action:
            # Test first page
            page1 = await mcp_server.search_plasmids(
                query="alzheimer",
                page_size=10,
                page_number=1
            )
            
            # Test second page
            page2 = await mcp_server.search_plasmids(
                query="alzheimer",
                page_size=10,
                page_number=2
            )
            
            action.log(
                message_type="pagination_test",
                page1_count=len(page1.plasmids),
                page2_count=len(page2.plasmids),
                page1_total=page1.count,
                page2_total=page2.count
            )
            
            # Basic pagination checks
            assert page1.page == 1
            assert page2.page == 2
            assert page1.page_size == 10
            assert page2.page_size == 10
            
            # Should have some results on both pages
            assert len(page1.plasmids) > 0, "First page should have results"
            # Second page might be empty if there are fewer than 10 total results
            
            # Total count should be consistent
            assert page1.count == page2.count, "Total count should be consistent across pages"
            
            # Results should be different (no duplicates between pages)
            if len(page2.plasmids) > 0:
                page1_ids = {p.id for p in page1.plasmids}
                page2_ids = {p.id for p in page2.plasmids}
                overlap = page1_ids.intersection(page2_ids)
                assert len(overlap) == 0, f"Should not have duplicate plasmids between pages, found overlap: {overlap}"
            
            return {"page1": page1, "page2": page2}
    
    @pytest.mark.asyncio
    async def test_alzheimer_search_filters(self, mcp_server):
        """Test Alzheimer search with additional filters."""
        with start_action(action_type="test_alzheimer_search_filters") as action:
            # Test with mammalian expression filter - should get 18-50 results
            mammalian_result = await mcp_server.search_plasmids(
                query="alzheimer",
                expression="mammalian",
                page_size=60  # Ensure we get all results
            )
            
            # Test with high popularity filter
            popular_result = await mcp_server.search_plasmids(
                query="alzheimer",
                popularity="high",
                page_size=20
            )
            
            action.log(
                message_type="filter_test",
                mammalian_count=mammalian_result.count,
                popular_count=popular_result.count
            )
            
            # Test mammalian expression filter range (18-50 results expected)
            assert mammalian_result.count >= 18, f"Expected at least 18 results with mammalian expression filter, got {mammalian_result.count}"
            assert mammalian_result.count <= 50, f"Expected at most 50 results with mammalian expression filter, got {mammalian_result.count}"
            
            # Basic filter checks
            assert popular_result.count >= 0, "Popularity filter should return valid count"
            
            # Verify filter is applied (if we have results)
            for plasmid in mammalian_result.plasmids:
                if plasmid.expression:
                    assert any("mammalian" in expr.lower() for expr in plasmid.expression), \
                        f"Plasmid {plasmid.id} should have mammalian expression"
            
            for plasmid in popular_result.plasmids:
                if plasmid.popularity:
                    assert plasmid.popularity.lower() == "high", \
                        f"Plasmid {plasmid.id} should have high popularity"
            
            return {"mammalian": mammalian_result, "popular": popular_result}


# Standalone test functions for manual testing
async def manual_test_alzheimer_search():
    """Manual test function for Alzheimer search."""
    print("🧬 Testing Alzheimer Search Functionality")
    print("=" * 50)
    
    mcp = AddgeneMCP()
    
    try:
        # Basic search
        print("🔍 Performing basic Alzheimer search...")
        result = await mcp.search_plasmids(query="alzheimer", page_size=60)
        
        print(f"📊 Results: {result.count} plasmids found")
        print(f"📄 Returned: {len(result.plasmids)} plasmids")
        
        # Look for target plasmid
        target_found = False
        target_position = None
        
        for i, plasmid in enumerate(result.plasmids):
            if plasmid.id == 177660 or "pT7C-HSPA1L" in plasmid.name:
                target_found = True
                target_position = i + 1
                print(f"🎯 Found target plasmid at position {target_position}:")
                print(f"   ID: {plasmid.id}")
                print(f"   Name: {plasmid.name}")
                print(f"   Depositor: {plasmid.depositor}")
                break
        
        if not target_found:
            print("❌ Target plasmid pT7C-HSPA1L (ID: 177660) not found in results")
            print("📋 First 5 results:")
            for i, plasmid in enumerate(result.plasmids[:5]):
                print(f"   {i+1}. {plasmid.name} (ID: {plasmid.id}) - {plasmid.depositor}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error during manual test: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Run manual test
    asyncio.run(manual_test_alzheimer_search()) 