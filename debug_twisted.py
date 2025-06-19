#!/usr/bin/env python3
"""
Debug script to test Twisted reactor integration.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from twisted.internet import asyncioreactor
from twisted.internet import reactor
from twisted.internet.defer import Deferred

async def test_twisted_integration():
    """Test if Twisted reactor works with asyncio."""
    
    print("🔧 Testing Twisted Reactor Integration")
    print("="*60)
    
    try:
        # Install asyncio reactor
        print("1️⃣ Installing asyncio reactor...")
        if not hasattr(asyncioreactor, '_asynchronous'):
            asyncioreactor.install()
        print("   ✅ Reactor installed")
        
        # Check if reactor is running
        print("2️⃣ Checking reactor status...")
        print(f"   Reactor running: {reactor.running}")
        print(f"   Reactor type: {type(reactor)}")
        
        # Test simple deferred
        print("3️⃣ Testing simple deferred...")
        
        def create_test_deferred():
            d = Deferred()
            reactor.callLater(1, d.callback, "test_result")
            return d
        
        # Convert deferred to future
        future = asyncio.Future()
        
        def on_success(result):
            if not future.done():
                future.set_result(result)
        
        def on_error(failure):
            if not future.done():
                future.set_exception(failure.value)
        
        deferred = create_test_deferred()
        deferred.addCallback(on_success)
        deferred.addErrback(on_error)
        
        # Start reactor if not running
        if not reactor.running:
            print("   Starting reactor...")
            reactor.run(installSignalHandlers=False)
        
        # Wait for result
        result = await asyncio.wait_for(future, timeout=5)
        print(f"   ✅ Deferred result: {result}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_twisted_integration()) 