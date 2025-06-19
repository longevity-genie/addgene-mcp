#!/usr/bin/env python3
"""
Test script to validate that our Scrapy selectors work correctly on real HTML.
"""

from scrapy import Selector
from urllib.parse import urljoin

def test_selectors():
    """Test our selectors on the actual HTML we fetched."""
    
    print("🧪 Testing Scrapy Selectors on Real HTML")
    print("="*60)
    
    # Read the HTML file
    with open('debug_addgene_response.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Create Scrapy selector
    selector = Selector(text=html_content)
    base_url = "https://www.addgene.org/search/catalog/plasmids/"
    
    print("1️⃣ Testing main search result selector...")
    plasmid_entries = selector.css('div.search-result-item')
    print(f"   Found {len(plasmid_entries)} plasmid entries")
    
    if len(plasmid_entries) == 0:
        print("❌ No plasmid entries found!")
        return False
    
    print(f"\n2️⃣ Testing selectors on first entry...")
    first_entry = plasmid_entries[0]
    
    # Test ID extraction
    entry_id = first_entry.css('::attr(id)').get()
    print(f"   ID: {entry_id}")
    
    # Test title extraction  
    title_link = first_entry.css('h3.search-result-title span a')
    if title_link:
        name = title_link.css('::text').get()
        href = title_link.css('::attr(href)').get()
        print(f"   Name: {name}")
        print(f"   URL: {href}")
        if href:
            full_url = urljoin(base_url, href)
            print(f"   Full URL: {full_url}")
    else:
        print("   ❌ No title link found")
    
    # Test details section
    details = first_entry.css('div.search-result-details')
    print(f"   Details sections: {len(details)}")
    
    if details:
        # Test field labels
        field_labels = details.css('span.field-label')
        print(f"   Field labels: {len(field_labels)}")
        
        for i, label_elem in enumerate(field_labels[:5]):  # First 5
            label_text = label_elem.css('::text').get()
            print(f"      {i+1}. Label: '{label_text}'")
            
            # Test value extraction using XPath
            parent_row = label_elem.xpath('../..')  # Go up to the row
            value_column = parent_row.css('.col-xs-10')
            if value_column:
                field_value = value_column.css('::text').get()
                print(f"         Value: '{field_value}'")
                
                # Check for links
                link = value_column.css('a::attr(href)').get()
                if link:
                    print(f"         Link: {link}")
    
    # Test popularity extraction
    flame_icon = first_entry.css('span.addgene-flame')
    if flame_icon:
        flame_classes = flame_icon.css('::attr(class)').get()
        print(f"   Flame classes: {flame_classes}")
        
        if flame_classes:
            classes = flame_classes.split()
            popularity = None
            for cls in classes:
                if cls == "addgene-flame-high":
                    popularity = "high"
                elif cls == "addgene-flame-medium":
                    popularity = "medium"
                elif cls == "addgene-flame-low":
                    popularity = "low"
            print(f"   Popularity: {popularity}")
    
    print(f"\n3️⃣ Testing all entries...")
    successful_extractions = 0
    
    for i, entry in enumerate(plasmid_entries):
        try:
            # Extract basic info
            entry_id = entry.css('::attr(id)').get()
            title_link = entry.css('h3.search-result-title span a')
            
            if title_link:
                name = title_link.css('::text').get()
                href = title_link.css('::attr(href)').get()
                
                if name and href:
                    successful_extractions += 1
                    print(f"   ✅ Entry {i+1}: ID={entry_id}, Name='{name}', URL={href}")
                else:
                    print(f"   ❌ Entry {i+1}: Missing name or URL")
            else:
                print(f"   ❌ Entry {i+1}: No title link found")
                
        except Exception as e:
            print(f"   ❌ Entry {i+1}: Error - {e}")
    
    print(f"\n🎯 SUMMARY:")
    print(f"✅ Found {len(plasmid_entries)} total entries")
    print(f"✅ Successfully extracted {successful_extractions} entries")
    print(f"✅ Success rate: {successful_extractions/len(plasmid_entries)*100:.1f}%")
    
    if successful_extractions == len(plasmid_entries):
        print("🎉 All selectors work perfectly!")
        return True
    else:
        print("⚠️  Some selectors may need adjustment")
        return False

if __name__ == "__main__":
    success = test_selectors()
    exit(0 if success else 1) 