#!/usr/bin/env python3
"""Test to verify Scrapy spider URL building with page_size parameter."""

from addgene_mcp.scrapy_addgene.spiders.plasmids import PlasmidsSpider


def test_spider_url_building():
    """Test that the spider builds URLs correctly with page_size."""
    
    # Test 1: Basic URL with default parameters
    spider1 = PlasmidsSpider(query="alzheimer", page_size=10, page_number=1)
    url1 = spider1.build_search_url()
    print(f"Test 1 - Default parameters:")
    print(f"URL: {url1}")
    assert "page_size=10" in url1
    assert "page_number=1" in url1
    assert "q=alzheimer" in url1
    print("Default parameters test passed\n")
    
    # Test 2: Maximum page size (50)
    spider2 = PlasmidsSpider(query="alzheimer", page_size=50, page_number=1)
    url2 = spider2.build_search_url()
    print(f"Test 2 - Maximum page size:")
    print(f"URL: {url2}")
    assert "page_size=50" in url2
    assert "page_number=1" in url2
    assert "q=alzheimer" in url2
    print("Maximum page size test passed\n")
    
    # Test 3: Verify start_urls is set correctly
    spider3 = PlasmidsSpider(query="alzheimer", page_size=50, page_number=1)
    print(f"Test 3 - Start URLs:")
    print(f"Start URLs: {spider3.start_urls}")
    assert len(spider3.start_urls) == 1
    assert "page_size=50" in spider3.start_urls[0]
    assert "q=alzheimer" in spider3.start_urls[0]
    print("Start URLs test passed\n")
    
    print("All URL building tests passed!")


if __name__ == "__main__":
    test_spider_url_building() 