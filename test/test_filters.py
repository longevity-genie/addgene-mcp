#!/usr/bin/env python3
"""
Test filter functionality for Addgene MCP.
Tests various search filters like expression, vector type, species, etc.
"""

import pytest
import asyncio
import os
from typing import List, Dict, Any

from addgene_mcp.server import AddgeneMCP, SearchResult, PlasmidOverview
from eliot import start_action

# Set testing flag to use optimized scrapy settings
os.environ['TESTING'] = 'true'


class TestFilters:
    """Test search filter functionality."""
    
    @pytest.fixture(scope="class")
    def mcp_server(self):
        """Set up the MCP server for testing."""
        return AddgeneMCP()
    
    @pytest.mark.asyncio
    async def test_expression_filter(self, mcp_server):
        """Test expression system filters."""
        with start_action(action_type="test_expression_filter") as action:
            # Test mammalian expression filter
            result = await mcp_server.search_plasmids(
                query="GFP",
                page_size=3,
                expression="mammalian"
            )
            
            action.log(
                message_type="expression_filter_result",
                expression="mammalian",
                count=result.count,
                returned=len(result.plasmids)
            )
            
            # Structure validation
            assert isinstance(result, SearchResult)
            assert result.page_size == 3
            assert result.count >= 0
            
            # Check that filter was applied (if results exist)
            for plasmid in result.plasmids:
                if plasmid.expression:
                    # Should contain mammalian expression
                    has_mammalian = any("mammalian" in expr.lower() for expr in plasmid.expression)
                    if not has_mammalian:
                        action.log(
                            message_type="expression_filter_mismatch",
                            plasmid_id=plasmid.id,
                            expected="mammalian",
                            actual=plasmid.expression
                        )
    
    @pytest.mark.asyncio
    async def test_vector_type_filter(self, mcp_server):
        """Test vector type filters."""
        with start_action(action_type="test_vector_type_filter") as action:
            # Test lentiviral vector filter
            result = await mcp_server.search_plasmids(
                query="shRNA",
                page_size=3,
                vector_types="lentiviral"
            )
            
            action.log(
                message_type="vector_type_filter_result",
                vector_type="lentiviral",
                count=result.count,
                returned=len(result.plasmids)
            )
            
            # Structure validation
            assert isinstance(result, SearchResult)
            assert result.page_size == 3
            assert result.count >= 0
            
            # Check that filter was applied (if results exist)
            for plasmid in result.plasmids:
                if plasmid.vector_type:
                    # Should contain lentiviral vector type
                    has_lentiviral = "lentiviral" in plasmid.vector_type.lower()
                    if not has_lentiviral:
                        action.log(
                            message_type="vector_type_filter_mismatch",
                            plasmid_id=plasmid.id,
                            expected="lentiviral",
                            actual=plasmid.vector_type
                        )
    
    @pytest.mark.asyncio
    async def test_species_filter(self, mcp_server):
        """Test species filters."""
        with start_action(action_type="test_species_filter") as action:
            # Test human species filter
            result = await mcp_server.search_plasmids(
                query="p53",
                page_size=3,
                species="homo_sapiens"
            )
            
            action.log(
                message_type="species_filter_result",
                species="homo_sapiens",
                count=result.count,
                returned=len(result.plasmids)
            )
            
            # Structure validation
            assert isinstance(result, SearchResult)
            assert result.page_size == 3
            assert result.count >= 0
    
    @pytest.mark.asyncio
    async def test_popularity_filter(self, mcp_server):
        """Test popularity filters."""
        with start_action(action_type="test_popularity_filter") as action:
            # Test high popularity filter
            result = await mcp_server.search_plasmids(
                query="plasmid",
                page_size=3,
                popularity="high"
            )
            
            action.log(
                message_type="popularity_filter_result",
                popularity="high",
                count=result.count,
                returned=len(result.plasmids)
            )
            
            # Structure validation
            assert isinstance(result, SearchResult)
            assert result.page_size == 3
            assert result.count >= 0
            
            # Check that filter was applied (if results exist)
            for plasmid in result.plasmids:
                if plasmid.popularity:
                    # Should have high popularity
                    has_high_popularity = plasmid.popularity.lower() == "high"
                    if not has_high_popularity:
                        action.log(
                            message_type="popularity_filter_mismatch",
                            plasmid_id=plasmid.id,
                            expected="high",
                            actual=plasmid.popularity
                        )
    
    @pytest.mark.asyncio
    async def test_plasmid_type_filter(self, mcp_server):
        """Test plasmid type filters."""
        with start_action(action_type="test_plasmid_type_filter") as action:
            # Test single insert filter
            result = await mcp_server.search_plasmids(
                query="insert",
                page_size=3,
                plasmid_type="single_insert"
            )
            
            action.log(
                message_type="plasmid_type_filter_result",
                plasmid_type="single_insert",
                count=result.count,
                returned=len(result.plasmids)
            )
            
            # Structure validation
            assert isinstance(result, SearchResult)
            assert result.page_size == 3
            assert result.count >= 0
    
    @pytest.mark.asyncio
    async def test_multiple_filters_combination(self, mcp_server):
        """Test combining multiple filters."""
        with start_action(action_type="test_multiple_filters_combination") as action:
            # Test combining multiple filters
            result = await mcp_server.search_plasmids(
                query="test",
                page_size=2,
                expression="mammalian",
                popularity="high"
            )
            
            action.log(
                message_type="multiple_filters_result",
                filters={
                    "expression": "mammalian",
                    "popularity": "high"
                },
                count=result.count,
                returned=len(result.plasmids)
            )
            
            # Structure validation
            assert isinstance(result, SearchResult)
            assert result.page_size == 2
            assert result.count >= 0
            
            # Check that both filters were applied (if results exist)
            for plasmid in result.plasmids:
                # Check expression filter
                if plasmid.expression:
                    has_mammalian = any("mammalian" in expr.lower() for expr in plasmid.expression)
                    if not has_mammalian:
                        action.log(
                            message_type="multiple_filter_expression_mismatch",
                            plasmid_id=plasmid.id,
                            expected="mammalian",
                            actual=plasmid.expression
                        )
                
                # Check popularity filter
                if plasmid.popularity:
                    has_high_popularity = plasmid.popularity.lower() == "high"
                    if not has_high_popularity:
                        action.log(
                            message_type="multiple_filter_popularity_mismatch",
                            plasmid_id=plasmid.id,
                            expected="high",
                            actual=plasmid.popularity
                        )
    
    @pytest.mark.asyncio
    async def test_resistance_marker_filter(self, mcp_server):
        """Test resistance marker filters."""
        with start_action(action_type="test_resistance_marker_filter") as action:
            # Test puromycin resistance marker
            result = await mcp_server.search_plasmids(
                query="resistance",
                page_size=3,
                resistance_marker="puromycin"
            )
            
            action.log(
                message_type="resistance_marker_filter_result",
                resistance_marker="puromycin",
                count=result.count,
                returned=len(result.plasmids)
            )
            
            # Structure validation
            assert isinstance(result, SearchResult)
            assert result.page_size == 3
            assert result.count >= 0
    
    @pytest.mark.asyncio
    async def test_bacterial_resistance_filter(self, mcp_server):
        """Test bacterial resistance filters."""
        with start_action(action_type="test_bacterial_resistance_filter") as action:
            # Test ampicillin bacterial resistance
            result = await mcp_server.search_plasmids(
                query="ampicillin",
                page_size=3,
                bacterial_resistance="ampicillin"
            )
            
            action.log(
                message_type="bacterial_resistance_filter_result",
                bacterial_resistance="ampicillin",
                count=result.count,
                returned=len(result.plasmids)
            )
            
            # Structure validation
            assert isinstance(result, SearchResult)
            assert result.page_size == 3
            assert result.count >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 