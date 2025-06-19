#!/usr/bin/env python3
"""Test example to verify filter parameters work correctly."""

import asyncio
import pytest
from addgene_mcp.server import AddgeneMCP


@pytest.mark.asyncio
async def test_filter_example():
    """Test that filter parameters work correctly."""
    
    print("🔍 Testing filter functionality...")
    
    api = AddgeneMCP()
    
    # Test 1: Search with mammalian expression filter
    print("📄 Testing mammalian expression filter...")
    result = await api.search_plasmids(
        query="GFP",
        page_size=5,
        page_number=1,
        expression="mammalian"
    )
    
    print(f"✅ Found {len(result.plasmids)} results with mammalian expression filter")
    for i, plasmid in enumerate(result.plasmids[:3], 1):
        print(f"  {i}. {plasmid.name} (ID: {plasmid.id})")
    
    # Test 2: Search with species filter
    print("\n📄 Testing species filter (homo_sapiens)...")
    result2 = await api.search_plasmids(
        query="p53",
        page_size=5,
        page_number=1,
        species="homo_sapiens"
    )
    
    print(f"✅ Found {len(result2.plasmids)} results with homo_sapiens species filter")
    for i, plasmid in enumerate(result2.plasmids[:3], 1):
        print(f"  {i}. {plasmid.name} (ID: {plasmid.id})")
    
    # Test 3: Search with vector type filter
    print("\n📄 Testing vector type filter (crispr)...")
    result3 = await api.search_plasmids(
        query="cas9",
        page_size=5,
        page_number=1,
        vector_types="crispr"
    )
    
    print(f"✅ Found {len(result3.plasmids)} results with CRISPR vector type filter")
    for i, plasmid in enumerate(result3.plasmids[:3], 1):
        print(f"  {i}. {plasmid.name} (ID: {plasmid.id})")
    
    print("\n🎉 Filter tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_filter_example()) 