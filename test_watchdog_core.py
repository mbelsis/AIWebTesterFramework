#!/usr/bin/env python3
"""
Core test to verify critical watchdog fixes work without browser dependencies.

This tests that:
1. WatchdogState definitions are compatible between files
2. Network tracking works correctly
3. State comparison logic works as expected
"""

import time
import logging
from utils.watchdog import Watchdog, WatchdogState, StateIndicator
from browser.context import WatchdogState as FallbackWatchdogState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_watchdog_state_compatibility():
    """Test that WatchdogState definitions are compatible."""
    logger.info("Testing WatchdogState compatibility...")
    
    # Test that both states have the same fields
    real_state = WatchdogState(timestamp=time.time())
    fallback_state = FallbackWatchdogState(timestamp=time.time())
    
    # Check that both have required fields
    required_fields = ['timestamp', 'dom_hash', 'request_count', 'pixel_signature', 'url', 'title']
    
    real_fields = set(dir(real_state))
    fallback_fields = set(dir(fallback_state))
    
    missing_from_fallback = [field for field in required_fields if not hasattr(fallback_state, field)]
    
    compatible = len(missing_from_fallback) == 0
    
    logger.info(f"Compatibility check: {'PASS' if compatible else 'FAIL'}")
    if not compatible:
        logger.error(f"Missing fields in fallback: {missing_from_fallback}")
    
    return compatible

def test_network_tracking():
    """Test that network tracking works correctly."""
    logger.info("Testing network tracking...")
    
    watchdog = Watchdog()
    initial_count = watchdog._request_count
    
    # Track some network requests
    watchdog.track_network_request("request")
    watchdog.track_network_request("response")
    watchdog.track_network_request("request")
    
    final_count = watchdog._request_count
    tracked_count = final_count - initial_count
    
    expected_count = 3
    tracking_works = tracked_count == expected_count
    
    logger.info(f"Tracked {tracked_count} requests (expected {expected_count}): {'PASS' if tracking_works else 'FAIL'}")
    
    return tracking_works

def test_state_comparison():
    """Test that state comparison logic works correctly."""
    logger.info("Testing state comparison logic...")
    
    # Create two identical states
    timestamp = time.time()
    state1 = WatchdogState(
        timestamp=timestamp,
        dom_hash="test_hash_123",
        request_count=5,
        pixel_signature="pixel_sig_456",
        url="http://example.com",
        title="Test Page"
    )
    
    state2 = WatchdogState(
        timestamp=timestamp + 1,  # Different timestamp
        dom_hash="test_hash_123",  # Same DOM
        request_count=5,           # Same request count
        pixel_signature="pixel_sig_456",  # Same pixel signature
        url="http://example.com",  # Same URL
        title="Test Page"          # Same title
    )
    
    # Check changes
    changes = state1.has_changed(state2, ignore_timestamp=True)
    
    # Should have no changes (ignoring timestamp)
    relevant_changes = {
        'dom_hash': changes.get('dom_hash', False),
        'request_count': changes.get('request_count', False), 
        'pixel_signature': changes.get('pixel_signature', False)
    }
    
    no_changes = not any(relevant_changes.values())
    
    logger.info(f"Identical states comparison: {'PASS' if no_changes else 'FAIL'}")
    logger.info(f"Changes detected: {relevant_changes}")
    
    # Test with actual changes
    state3 = WatchdogState(
        timestamp=timestamp,
        dom_hash="different_hash_789",  # Changed DOM
        request_count=7,                # Changed request count
        pixel_signature="pixel_sig_456", # Same pixel signature
        url="http://example.com",
        title="Test Page"
    )
    
    changes2 = state1.has_changed(state3, ignore_timestamp=True)
    expected_changes = {
        'dom_hash': True,      # Should detect DOM change
        'request_count': True, # Should detect request count change
        'pixel_signature': False  # Should detect no pixel change
    }
    
    actual_changes = {
        'dom_hash': changes2.get('dom_hash', False),
        'request_count': changes2.get('request_count', False),
        'pixel_signature': changes2.get('pixel_signature', False)
    }
    
    changes_correct = actual_changes == expected_changes
    
    logger.info(f"Different states comparison: {'PASS' if changes_correct else 'FAIL'}")
    logger.info(f"Expected changes: {expected_changes}")
    logger.info(f"Actual changes: {actual_changes}")
    
    return no_changes and changes_correct

def test_config_loading():
    """Test that watchdog config loads correctly."""
    logger.info("Testing watchdog config loading...")
    
    try:
        watchdog = Watchdog()
        config = watchdog.config
        
        # Check that config loaded
        config_loaded = config is not None
        
        # Check that pixel signature is disabled by default (our fix)
        pixel_disabled = StateIndicator.PIXEL_SIGNATURE not in config.state_indicators
        
        # Check that DOM hash and request count are enabled
        dom_enabled = StateIndicator.DOM_HASH in config.state_indicators
        request_enabled = StateIndicator.REQUEST_COUNT in config.state_indicators
        
        config_correct = config_loaded and pixel_disabled and dom_enabled and request_enabled
        
        logger.info(f"Config loaded: {'PASS' if config_loaded else 'FAIL'}")
        logger.info(f"Pixel signature disabled: {'PASS' if pixel_disabled else 'FAIL'}")
        logger.info(f"DOM hash enabled: {'PASS' if dom_enabled else 'FAIL'}")
        logger.info(f"Request count enabled: {'PASS' if request_enabled else 'FAIL'}")
        logger.info(f"State indicators: {[ind.value for ind in config.state_indicators]}")
        
        return config_correct
        
    except Exception as e:
        logger.error(f"Config loading failed: {e}")
        return False

def main():
    """Run all core watchdog tests."""
    logger.info("Starting core watchdog functionality tests...")
    
    try:
        # Test 1: Type compatibility
        compatibility_result = test_watchdog_state_compatibility()
        
        # Test 2: Network tracking
        network_result = test_network_tracking()
        
        # Test 3: State comparison
        comparison_result = test_state_comparison()
        
        # Test 4: Config loading
        config_result = test_config_loading()
        
        # Summary
        logger.info("\n" + "="*50)
        logger.info("CORE WATCHDOG TEST RESULTS")
        logger.info("="*50)
        
        logger.info(f"✓ WatchdogState compatibility: {'PASS' if compatibility_result else 'FAIL'}")
        logger.info(f"✓ Network tracking: {'PASS' if network_result else 'FAIL'}")
        logger.info(f"✓ State comparison: {'PASS' if comparison_result else 'FAIL'}")
        logger.info(f"✓ Config loading: {'PASS' if config_result else 'FAIL'}")
        
        # Overall result
        all_pass = compatibility_result and network_result and comparison_result and config_result
        
        logger.info(f"\nOverall result: {'ALL CORE TESTS PASS' if all_pass else 'SOME TESTS FAILED'}")
        
        if not all_pass:
            logger.error("Critical watchdog functionality issues remain!")
            return False
        else:
            logger.info("Core watchdog fixes working correctly!")
            return True
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)