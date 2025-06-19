#!/usr/bin/env python3
"""
Debug script to test the Scrapy runner directly and isolate hanging issues.
"""

import asyncio
import signal
from typing import Any

from addgene_mcp.scrapy_addgene.runner import ScrapyManager
from eliot import start_action

async def test_runner_with_timeout() -> bool:
    """Test the runner with a timeout to prevent hanging."""
    
    print("🐛 Testing Scrapy Runner with Timeout")
    print("="*60)
    
    # Set up timeout
    timeout_seconds = 30
    
    try:
        # Create manager
        manager = ScrapyManager()
        print("✅ Runner created successfully")
        
        # Test with a timeout
        print(f"⏰ Running spider with {timeout_seconds}s timeout...")
        
        result = await asyncio.wait_for(
            manager.search_plasmids(
                query="pLKO.1",
                page_size=3,
                page_number=1
            ),
            timeout=timeout_seconds
        )
        
        print(f"✅ Spider completed successfully!")
        print(f"📊 Result type: {type(result)}")
        print(f"📋 Found {len(result)} plasmid results")
        
        for i, plasmid_dict in enumerate(result[:3]):
            print(f"   {i+1}. {plasmid_dict.get('name', 'Unknown')} (ID: {plasmid_dict.get('id', 'Unknown')})")
        
        return True
        
    except asyncio.TimeoutError:
        print(f"❌ Spider timed out after {timeout_seconds} seconds")
        print("💡 This confirms the hanging issue is in the runner/reactor")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def signal_handler(signum: int, frame: Any) -> None:
    """Handle Ctrl+C gracefully."""
    print("\n🛑 Interrupted by user")
    exit(1)

async def main() -> None:
    """Main debug function."""
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🚀 Starting Scrapy Runner Debug Test")
    print("Press Ctrl+C to interrupt if it hangs")
    print("="*60)
    
    success = await test_runner_with_timeout()
    
    if success:
        print("\n🎉 SUCCESS: Runner works correctly!")
    else:
        print("\n❌ FAILURE: Runner has hanging issues")
        print("\n💡 DIAGNOSIS:")
        print("   - Selectors work perfectly (confirmed by test_selectors.py)")
        print("   - HTML fetching works (confirmed by debug_html_fetch.py)")
        print("   - Issue is in Twisted reactor or runner logic")
        print("   - Likely causes:")
        print("     1. Twisted reactor not properly stopping")
        print("     2. Spider not yielding results correctly")
        print("     3. Pipeline hanging on processing")
        print("     4. Event loop conflicts")

if __name__ == "__main__":
    asyncio.run(main()) 