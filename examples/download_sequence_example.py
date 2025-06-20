#!/usr/bin/env python3
"""
Example script demonstrating how to download plasmid sequences using Addgene MCP.

This example shows the complete workflow:
1. Search for plasmids
2. Get sequence information 
3. Download sequence files to local filesystem

Usage:
    python examples/download_sequence_example.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the path so we can import addgene_mcp
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from addgene_mcp.server import AddgeneMCP
from eliot import start_action


async def download_sequence_example():
    """Example of downloading plasmid sequences."""
    
    # Initialize the MCP server
    mcp = AddgeneMCP()
    
    print("🧬 Addgene MCP Sequence Download Example")
    print("=" * 50)
    
    # Example plasmid IDs for demonstration
    # NOTE: These are example IDs - in real usage you would get these from search results
    example_plasmids = [
        {"id": 12345, "name": "pUC19 (example)", "format": "snapgene"},
        {"id": 67890, "name": "pGFP (example)", "format": "genbank"},
    ]
    
    # Create downloads directory
    downloads_dir = Path("sequence_downloads")
    downloads_dir.mkdir(exist_ok=True)
    
    print(f"📁 Download directory: {downloads_dir.absolute()}")
    print()
    
    for plasmid in example_plasmids:
        plasmid_id = plasmid["id"]
        plasmid_name = plasmid["name"]
        format_type = plasmid["format"]
        
        print(f"🔍 Processing {plasmid_name} (ID: {plasmid_id})")
        
        try:
            # Step 1: Get sequence information
            print(f"   📋 Getting sequence info for format: {format_type}")
            sequence_info = await mcp.get_sequence_info(plasmid_id, format_type)
            
            if not sequence_info.available:
                print(f"   ❌ Sequence not available for {plasmid_name}")
                continue
            
            print(f"   ✅ Sequence available at: {sequence_info.download_url}")
            
            # Step 2: Download the sequence file
            print(f"   ⬇️  Downloading sequence...")
            download_result = await mcp.download_sequence(
                plasmid_id=plasmid_id,
                format=format_type,
                download_directory=str(downloads_dir)
            )
            
            if download_result.download_success:
                print(f"   ✅ Downloaded successfully!")
                print(f"   📄 File: {download_result.file_path}")
                print(f"   📏 Size: {download_result.file_size} bytes")
                
                # Show a preview of the file content
                if download_result.file_path and os.path.exists(download_result.file_path):
                    with open(download_result.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content_preview = f.read(200)  # First 200 characters
                        print(f"   👀 Preview: {content_preview.strip()[:100]}...")
            else:
                print(f"   ❌ Download failed: {download_result.error_message}")
                
        except Exception as e:
            print(f"   💥 Error processing {plasmid_name}: {e}")
        
        print()
    
    print("📊 Download Summary")
    print("-" * 30)
    
    # List all downloaded files
    downloaded_files = list(downloads_dir.glob("*.dna")) + list(downloads_dir.glob("*.gb"))
    
    if downloaded_files:
        print(f"✅ Successfully downloaded {len(downloaded_files)} files:")
        for file_path in downloaded_files:
            file_size = file_path.stat().st_size
            print(f"   📄 {file_path.name} ({file_size} bytes)")
    else:
        print("❌ No files were downloaded")
    
    print(f"\n📁 All files saved in: {downloads_dir.absolute()}")


async def search_and_download_example():
    """Example showing search -> download workflow."""
    
    print("\n" + "=" * 50)
    print("🔍 Search and Download Example")
    print("=" * 50)
    
    mcp = AddgeneMCP()
    
    # Search for plasmids
    print("🔍 Searching for GFP plasmids...")
    search_results = await mcp.search_plasmids(
        query="GFP",
        page_size=3,  # Small number for demo
        expression="mammalian"  # Focus on mammalian expression
    )
    
    print(f"📊 Found {search_results.count} total results, showing first {len(search_results.plasmids)}")
    
    downloads_dir = Path("search_downloads")
    downloads_dir.mkdir(exist_ok=True)
    
    for plasmid in search_results.plasmids[:2]:  # Download first 2 results
        print(f"\n🧬 {plasmid.name} (ID: {plasmid.id})")
        print(f"   👨‍🔬 Depositor: {plasmid.depositor}")
        
        # Try to download in SnapGene format
        try:
            download_result = await mcp.download_sequence(
                plasmid_id=plasmid.id,
                format="snapgene",
                download_directory=str(downloads_dir)
            )
            
            if download_result.download_success:
                print(f"   ✅ Downloaded: {Path(download_result.file_path).name}")
            else:
                print(f"   ❌ Download failed: {download_result.error_message}")
                
        except Exception as e:
            print(f"   💥 Error: {e}")


async def main():
    """Run all examples."""
    try:
        await download_sequence_example()
        await search_and_download_example()
        
        print("\n🎉 Example completed!")
        print("\nNote: This example uses mock data for demonstration.")
        print("In real usage, the downloads would fetch actual files from Addgene.")
        
    except Exception as e:
        print(f"💥 Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Note: This example will use mock data since we're not actually 
    # connecting to Addgene servers in the example environment
    print("Starting Addgene MCP sequence download example...")
    asyncio.run(main()) 