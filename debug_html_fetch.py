#!/usr/bin/env python3
"""
Debug script to fetch HTML directly from Addgene and examine structure.
"""

import httpx
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urlencode

async def fetch_addgene_html():
    """Fetch HTML from Addgene search page."""
    
    # Build search URL similar to what the spider does
    base_url = "https://www.addgene.org/search/catalog/plasmids/"
    params = {
        'q': 'pLKO.1',
        'page_size': 3,
        'page_number': 1,
    }
    
    url = f"{base_url}?{urlencode(params)}"
    print(f"🌐 Fetching URL: {url}")
    
    async with httpx.AsyncClient(
        headers={
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en',
            'User-Agent': 'addgene-mcp/0.1.0 (+https://github.com/your-repo/addgene-mcp)',
        },
        timeout=30.0
    ) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            
            print(f"✅ Response status: {response.status_code}")
            print(f"📊 Content length: {len(response.text)} characters")
            
            return response.text
            
        except Exception as e:
            print(f"❌ Error fetching URL: {e}")
            return None

def analyze_html_structure(html_content):
    """Analyze the HTML structure and check our selectors."""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    print("\n" + "="*60)
    print("🔍 ANALYZING HTML STRUCTURE")
    print("="*60)
    
    # Check for search result items (what our spider looks for)
    print("\n1️⃣ Looking for search result items...")
    
    # Our spider looks for: 'div.search-result-item'
    search_results = soup.select('div.search-result-item')
    print(f"   Found {len(search_results)} items with 'div.search-result-item'")
    
    if len(search_results) == 0:
        # Try alternative selectors
        alternatives = [
            'div.search-result',
            'div.result-item', 
            'div.plasmid-item',
            'div[class*="result"]',
            'div[class*="item"]',
        ]
        
        for alt_selector in alternatives:
            alt_results = soup.select(alt_selector)
            print(f"   Alternative '{alt_selector}': {len(alt_results)} items")
    
    # If we found some results, analyze the first one
    if search_results:
        print(f"\n2️⃣ Analyzing first search result...")
        first_result = search_results[0]
        
        # Check ID extraction (spider looks for id attribute starting with 'Plasmids-')
        entry_id = first_result.get('id')
        print(f"   Entry ID: {entry_id}")
        
        # Check title extraction (spider looks for: h3.search-result-title span a)
        title_links = first_result.select('h3.search-result-title span a')
        print(f"   Title links found: {len(title_links)}")
        
        if title_links:
            name = title_links[0].get_text(strip=True)
            href = title_links[0].get('href')
            print(f"   Name: {name}")
            print(f"   URL: {href}")
        else:
            # Try alternative title selectors
            alt_title_selectors = [
                'h3 a',
                '.title a',
                'h3.search-result-title a',
                'a[href*="/plasmids/"]'
            ]
            for alt_sel in alt_title_selectors:
                alt_titles = first_result.select(alt_sel)
                print(f"   Alternative title '{alt_sel}': {len(alt_titles)} items")
        
        # Check for details section
        details = first_result.select('div.search-result-details')
        print(f"   Details sections found: {len(details)}")
        
        # Check for field labels
        if details:
            field_labels = details[0].select('span.field-label')
            print(f"   Field labels found: {len(field_labels)}")
            for label in field_labels[:3]:  # Show first 3
                label_text = label.get_text(strip=True)
                print(f"      - {label_text}")
        
        # Check for map column
        map_columns = first_result.select('div.map-column')
        print(f"   Map columns found: {len(map_columns)}")
        
        # Show the HTML structure of first result (truncated)
        print(f"\n3️⃣ First result HTML structure (first 500 chars):")
        result_html = str(first_result)[:500]
        print(f"   {result_html}...")
        
    else:
        print("\n❌ No search results found with expected selectors!")
        
        # Let's see what the page structure looks like
        print("\n🔍 General page structure:")
        
        # Look for any divs that might contain results
        all_divs = soup.find_all('div', limit=20)
        print(f"   Total divs on page: {len(soup.find_all('div'))}")
        print(f"   First 5 div classes:")
        for i, div in enumerate(all_divs[:5]):
            classes = div.get('class', [])
            div_id = div.get('id', '')
            print(f"      {i+1}. class={classes}, id='{div_id}'")
        
        # Look for any links that might be plasmid links
        plasmid_links = soup.find_all('a', href=lambda x: x and '/plasmids/' in x if x else False)
        print(f"   Found {len(plasmid_links)} links containing '/plasmids/'")
        for i, link in enumerate(plasmid_links[:3]):
            print(f"      {i+1}. {link.get('href')} - {link.get_text(strip=True)[:50]}")

async def main():
    """Main debug function."""
    print("🐛 Addgene HTML Debug Script")
    print("="*60)
    
    # Fetch HTML
    html_content = await fetch_addgene_html()
    
    if html_content:
        # Save HTML to file for inspection
        with open('debug_addgene_response.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("💾 HTML saved to: debug_addgene_response.html")
        
        # Analyze structure
        analyze_html_structure(html_content)
        
        print(f"\n🎯 SUMMARY:")
        print(f"✅ Successfully fetched HTML from Addgene")
        print(f"📄 Content saved to debug_addgene_response.html")
        print(f"🔍 Structure analysis completed")
        
    else:
        print("❌ Failed to fetch HTML")

if __name__ == "__main__":
    asyncio.run(main()) 