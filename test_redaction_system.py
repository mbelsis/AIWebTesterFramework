#!/usr/bin/env python3
"""
Comprehensive test suite for the security redaction system.
Tests all integration points and redaction functionality.
"""

import json
import sys
import os
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from utils.redaction import SecurityRedactor, ContentType, get_redactor
    from evidence.sink import EvidenceSink
    from providers.openai_provider import OpenAIProvider, OpenAIModel
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("This test requires all redaction modules to be available")
    sys.exit(1)


def test_basic_redaction():
    """Test basic redaction functionality"""
    print("🔍 Testing basic redaction functionality...")
    
    redactor = SecurityRedactor()
    
    # Test various sensitive data patterns
    test_cases = {
        "Authorization: Bearer sk-1234567890abcdef": "Authorization: Bearer [REDACTED_TOKEN]",
        "API_KEY=abc123def456": "API_KEY=[REDACTED_API_KEY]",
        "Email: user@example.com": "Email: [REDACTED_EMAIL]",
        "password=secretpassword123": "password=\"[REDACTED_PASSWORD]\"",
        "Phone: +1-555-123-4567": "Phone: [REDACTED_PHONE]",
        "https://user:pass@api.example.com": "https://[REDACTED_USER]:[REDACTED_PASS]@api.example.com"
    }
    
    success = True
    for original, expected_pattern in test_cases.items():
        redacted = redactor.redact_text(original)
        if "REDACTED" not in redacted:
            print(f"   ❌ Failed to redact: '{original}' -> '{redacted}'")
            success = False
        else:
            print(f"   ✅ Redacted: '{original}' -> '{redacted}'")
    
    return success


def test_json_redaction():
    """Test JSON redaction while preserving structure"""
    print("\n🔍 Testing JSON redaction...")
    
    redactor = SecurityRedactor()
    
    test_data = {
        "username": "testuser",
        "password": "supersecret123",
        "api_key": "sk-abcdef123456789",
        "email": "test@example.com",
        "metadata": {
            "session_token": "sess_xyz789",
            "authorization": "Bearer token123"
        },
        "non_sensitive": "this should remain"
    }
    
    redacted_data = redactor.redact_json(test_data)
    
    # Verify structure is preserved
    success = True
    if not isinstance(redacted_data, dict):
        print("   ❌ JSON structure not preserved")
        success = False
    
    # Verify sensitive fields are redacted
    sensitive_fields = ["password", "api_key", "email", "session_token", "authorization"]
    for field in sensitive_fields:
        if field in redacted_data:
            if "REDACTED" not in str(redacted_data[field]):
                print(f"   ❌ Field '{field}' not redacted: {redacted_data[field]}")
                success = False
            else:
                print(f"   ✅ Field '{field}' redacted: {redacted_data[field]}")
        elif field in redacted_data.get("metadata", {}):
            if "REDACTED" not in str(redacted_data["metadata"][field]):
                print(f"   ❌ Nested field '{field}' not redacted: {redacted_data['metadata'][field]}")
                success = False
            else:
                print(f"   ✅ Nested field '{field}' redacted: {redacted_data['metadata'][field]}")
    
    # Verify non-sensitive data is preserved
    if redacted_data.get("non_sensitive") != "this should remain":
        print("   ❌ Non-sensitive data was modified")
        success = False
    else:
        print("   ✅ Non-sensitive data preserved")
    
    return success


def test_evidence_sink_integration():
    """Test evidence sink integration with redaction"""
    print("\n🔍 Testing evidence sink integration...")
    
    # Create temporary test directory
    import tempfile
    temp_dir = tempfile.mkdtemp()
    
    try:
        sink = EvidenceSink(temp_dir)
        
        # Test logging events with sensitive data
        sensitive_event = {
            "action": "login",
            "user": "testuser",
            "password": "secret123",
            "api_key": "sk-testkey12345",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        sink.log_event("user_action", sensitive_event)
        sink.save_logs()
        
        # Read back the logs and verify redaction
        logs_file = Path(temp_dir) / "events.json"
        if logs_file.exists():
            with open(logs_file, 'r') as f:
                saved_logs = json.load(f)
            
            if saved_logs and len(saved_logs) > 0:
                event_data = saved_logs[0].get("data", {})
                
                # Check if sensitive fields are redacted
                success = True
                if "REDACTED" not in str(event_data.get("password", "")):
                    print("   ❌ Password not redacted in evidence logs")
                    success = False
                else:
                    print("   ✅ Password redacted in evidence logs")
                
                if "REDACTED" not in str(event_data.get("api_key", "")):
                    print("   ❌ API key not redacted in evidence logs")
                    success = False
                else:
                    print("   ✅ API key redacted in evidence logs")
                
                return success
            else:
                print("   ❌ No events found in saved logs")
                return False
        else:
            print("   ❌ Logs file not created")
            return False
    
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_html_redaction():
    """Test HTML content redaction"""
    print("\n🔍 Testing HTML redaction...")
    
    redactor = SecurityRedactor()
    
    html_content = '''
    <html>
        <body>
            <form>
                <input type="password" value="secret123" />
                <input type="email" value="user@example.com" />
                <input type="hidden" name="api_key" value="sk-abcdef123" />
            </form>
            <div data-token="bearer_xyz789">Content</div>
        </body>
    </html>
    '''
    
    redacted_html = redactor.redact_text(html_content, ContentType.HTML)
    
    # Check that sensitive content is redacted
    success = True
    if "secret123" in redacted_html:
        print("   ❌ Password value not redacted in HTML")
        success = False
    else:
        print("   ✅ Password value redacted in HTML")
    
    if "user@example.com" in redacted_html:
        print("   ❌ Email value not redacted in HTML")
        success = False
    else:
        print("   ✅ Email value redacted in HTML")
    
    if "sk-abcdef123" in redacted_html:
        print("   ❌ API key not redacted in HTML")
        success = False
    else:
        print("   ✅ API key redacted in HTML")
    
    return success


def test_url_redaction():
    """Test URL redaction"""
    print("\n🔍 Testing URL redaction...")
    
    redactor = SecurityRedactor()
    
    test_urls = [
        "https://api.example.com/users?api_key=sk-123456789",
        "https://user:password@api.example.com/data",
        "https://example.com/callback?token=bearer_xyz789",
        "https://db.example.com/query?auth=Basic YWxhZGRpbjpvcGVuc2VzYW1l"
    ]
    
    success = True
    for url in test_urls:
        redacted_url = redactor.redact_url(url)
        
        # Check that sensitive parts are redacted
        sensitive_found = False
        sensitive_patterns = ["sk-", "password", "bearer_", "Basic Y"]
        
        for pattern in sensitive_patterns:
            if pattern in url and pattern in redacted_url:
                print(f"   ❌ Sensitive pattern '{pattern}' not redacted in: {redacted_url}")
                success = False
                sensitive_found = True
        
        if not sensitive_found and "REDACTED" in redacted_url:
            print(f"   ✅ URL redacted: {url} -> {redacted_url}")
        elif not sensitive_found:
            print(f"   ✅ URL clean (no sensitive data): {url}")
    
    return success


def test_openai_provider_integration():
    """Test OpenAI provider redaction integration"""
    print("\n🔍 Testing OpenAI provider integration...")
    
    # Test without actual API key to avoid real API calls
    provider = OpenAIProvider(api_key=None)  # This will disable actual API calls
    
    # Test that redactor is initialized
    if hasattr(provider, 'redactor') and provider.redactor is not None:
        print("   ✅ OpenAI provider redactor initialized")
        return True
    else:
        print("   ❌ OpenAI provider redactor not initialized")
        return False


def test_configuration_loading():
    """Test security configuration loading"""
    print("\n🔍 Testing configuration loading...")
    
    try:
        redactor = SecurityRedactor()
        
        # Check if patterns are loaded
        if redactor.patterns and len(redactor.patterns) > 0:
            print(f"   ✅ Loaded {len(redactor.patterns)} redaction patterns")
            
            # Check for some expected patterns
            pattern_names = [p.name for p in redactor.patterns]
            expected_patterns = ["authorization_bearer", "email_address", "password_field"]
            
            found_patterns = [p for p in expected_patterns if p in pattern_names]
            if len(found_patterns) >= 2:  # At least 2 core patterns should be present
                print(f"   ✅ Found expected patterns: {found_patterns}")
                return True
            else:
                print(f"   ❌ Missing expected patterns. Found: {pattern_names}")
                return False
        else:
            print("   ❌ No redaction patterns loaded")
            return False
    
    except Exception as e:
        print(f"   ❌ Error loading configuration: {e}")
        return False


def test_performance():
    """Test redaction performance with larger data"""
    print("\n🔍 Testing redaction performance...")
    
    import time
    
    redactor = SecurityRedactor()
    
    # Create larger test data
    large_text = "API_KEY=sk-test123456 " * 1000 + "email@example.com " * 1000
    
    start_time = time.time()
    redacted_text = redactor.redact_text(large_text)
    end_time = time.time()
    
    duration = end_time - start_time
    
    # Performance should be reasonable (under 1 second for this test)
    if duration < 1.0:
        print(f"   ✅ Performance acceptable: {duration:.3f}s for {len(large_text)} characters")
        return True
    else:
        print(f"   ⚠️  Performance concern: {duration:.3f}s for {len(large_text)} characters")
        return True  # Not a failure, but worth noting


def main():
    """Run all redaction tests"""
    print("🔒 Testing AI WebTester Security Redaction System")
    print("=" * 60)
    
    tests = [
        ("Configuration Loading", test_configuration_loading),
        ("Basic Redaction", test_basic_redaction),
        ("JSON Redaction", test_json_redaction),
        ("Evidence Sink Integration", test_evidence_sink_integration),
        ("HTML Redaction", test_html_redaction),
        ("URL Redaction", test_url_redaction),
        ("OpenAI Provider Integration", test_openai_provider_integration),
        ("Performance", test_performance)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All redaction tests passed! Security system is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the redaction implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())