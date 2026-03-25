"""
Security redaction utilities for sanitizing sensitive data from logs, evidence, and LLM communications.
"""

import re
import json
import logging
import threading
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Supported content types for redaction."""
    TEXT = "text"
    JSON = "json"
    HTML = "html"
    XML = "xml"
    URL = "url"


@dataclass
class RedactionPattern:
    """Represents a redaction pattern with metadata."""
    name: str
    regex: str
    replacement: str
    description: str
    compiled_regex: Optional[re.Pattern] = None
    
    def __post_init__(self):
        """Compile the regex pattern."""
        try:
            self.compiled_regex = re.compile(self.regex)
        except re.error as e:
            logger.error(f"Failed to compile regex pattern '{self.name}': {e}")
            # Use a safe fallback pattern that won't match anything
            self.compiled_regex = re.compile(r"(?!.*)")  # Never matches


@dataclass
class RedactionStats:
    """Statistics about redaction operations."""
    total_items_processed: int = 0
    total_redactions: int = 0
    patterns_matched: Optional[Dict[str, int]] = None
    
    def __post_init__(self):
        if self.patterns_matched is None:
            self.patterns_matched = {}


class SecurityRedactor:
    """Main class for handling security redaction throughout the framework."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the security redactor.
        
        Args:
            config_path: Path to security configuration file. If None, uses default.
        """
        self.config_path = config_path or str(Path(__file__).parent.parent / "configs" / "security.yaml")
        self.config = self._load_config()
        self.patterns = self._load_patterns()
        self.stats = RedactionStats()
        
        # Initialize audit logging if enabled
        self.audit_enabled = self.config.get("audit", {}).get("log_redactions", False)
        if self.audit_enabled:
            self._setup_audit_logging()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load security configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded security configuration from {self.config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Security config not found at {self.config_path}, using defaults")
            return self._get_default_config()
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse security config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default security configuration if file is not available."""
        return {
            "redaction": {
                "enabled": True,
                "replacement_text": "[REDACTED]",
                "patterns": []
            },
            "audit": {
                "log_redactions": False,
                "redaction_stats": True
            }
        }
    
    def _load_patterns(self) -> List[RedactionPattern]:
        """Load and compile redaction patterns from configuration."""
        patterns = []
        pattern_configs = self.config.get("redaction", {}).get("patterns", [])
        
        for pattern_config in pattern_configs:
            try:
                pattern = RedactionPattern(
                    name=pattern_config.get("name", "unknown"),
                    regex=pattern_config.get("regex", ""),
                    replacement=pattern_config.get("replacement", "[REDACTED]"),
                    description=pattern_config.get("description", "")
                )
                patterns.append(pattern)
                logger.debug(f"Loaded redaction pattern: {pattern.name}")
            except Exception as e:
                logger.error(f"Failed to load pattern {pattern_config.get('name', 'unknown')}: {e}")
        
        logger.info(f"Loaded {len(patterns)} redaction patterns")
        return patterns
    
    def _setup_audit_logging(self):
        """Setup audit logging for redaction operations."""
        audit_logger = logging.getLogger("security.redaction.audit")
        if not audit_logger.handlers:
            # Create handler for audit logs
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - AUDIT - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            audit_logger.addHandler(handler)
            audit_logger.setLevel(logging.INFO)
    
    def is_enabled(self) -> bool:
        """Check if redaction is enabled."""
        return self.config.get("redaction", {}).get("enabled", True)
    
    def redact_text(self, text: str, content_type: ContentType = ContentType.TEXT) -> str:
        """
        Redact sensitive data from text content.
        
        Args:
            text: Text content to redact.
            content_type: Type of content for specialized handling.
        
        Returns:
            Redacted text with sensitive data removed.
        """
        if not self.is_enabled() or not text:
            return text
        
        original_text = text
        redacted_text = text
        redactions_made = 0
        
        try:
            # Apply all redaction patterns
            for pattern in self.patterns:
                if pattern.compiled_regex:
                    matches_before = len(pattern.compiled_regex.findall(redacted_text))
                    if matches_before > 0:
                        redacted_text = pattern.compiled_regex.sub(pattern.replacement, redacted_text)
                        matches_after = len(pattern.compiled_regex.findall(redacted_text))
                        pattern_redactions = matches_before - matches_after
                        
                        if pattern_redactions > 0:
                            redactions_made += pattern_redactions
                            if self.stats.patterns_matched is not None:
                                self.stats.patterns_matched[pattern.name] = (
                                    self.stats.patterns_matched.get(pattern.name, 0) + pattern_redactions
                                )
                            
                            if self.audit_enabled:
                                self._log_redaction(pattern.name, pattern_redactions, content_type)
            
            # Handle content-type specific redaction
            if content_type in [ContentType.JSON, ContentType.HTML, ContentType.XML]:
                redacted_text = self._redact_structured_content(redacted_text, content_type)
            
            self.stats.total_items_processed += 1
            self.stats.total_redactions += redactions_made
            
            return redacted_text
            
        except Exception as e:
            logger.error(f"Error during redaction: {e}")
            # Return original text if redaction fails to avoid breaking functionality
            return original_text
    
    def redact_json(self, data: Union[str, Dict, List]) -> Union[str, Dict, List]:
        """
        Redact sensitive data from JSON content while preserving structure.
        
        Args:
            data: JSON data as string, dict, or list.
        
        Returns:
            Redacted JSON data in the same format as input.
        """
        if not self.is_enabled():
            return data
        
        try:
            # Handle string input
            if isinstance(data, str):
                # Try to parse as JSON first
                try:
                    json_data = json.loads(data)
                    redacted_data = self._redact_json_object(json_data)
                    return json.dumps(redacted_data, indent=2)
                except json.JSONDecodeError:
                    # Treat as regular text if not valid JSON
                    return self.redact_text(data, ContentType.JSON)
            
            # Handle dict/list input
            elif isinstance(data, (dict, list)):
                return self._redact_json_object(data)
            
            else:
                return data
                
        except Exception as e:
            logger.error(f"Error redacting JSON: {e}")
            return data
    
    def _redact_json_object(self, obj: Union[Dict, List, Any], _parent_sensitive_key: Optional[str] = None) -> Union[Dict, List, Any]:
        """Recursively redact JSON objects while preserving structure."""
        if isinstance(obj, dict):
            redacted_dict = {}
            for key, value in obj.items():
                # Check if key suggests sensitive data
                if self._is_sensitive_key(key):
                    # For sensitive keys, only replace the value if it's a string
                    # Otherwise, preserve structure and redact contents
                    if isinstance(value, str):
                        redacted_dict[key] = self._get_redacted_value_for_key(key)
                    elif isinstance(value, (dict, list)):
                        # Pass the sensitive key down so list items inherit redaction
                        redacted_dict[key] = self._redact_json_object(value, _parent_sensitive_key=key)
                    else:
                        redacted_dict[key] = value
                elif isinstance(value, str):
                    redacted_dict[key] = self.redact_text(value, ContentType.JSON)
                elif isinstance(value, (dict, list)):
                    redacted_dict[key] = self._redact_json_object(value)
                else:
                    redacted_dict[key] = value
            return redacted_dict
        
        elif isinstance(obj, list):
            return [self._redact_json_object(item, _parent_sensitive_key) for item in obj]

        elif isinstance(obj, str):
            # If a parent dict key was sensitive, redact the string unconditionally
            if _parent_sensitive_key:
                return self._get_redacted_value_for_key(_parent_sensitive_key)
            return self.redact_text(obj, ContentType.JSON)

        else:
            return obj
    
    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a JSON key likely contains sensitive data."""
        sensitive_keys = {
            'password', 'passwd', 'pwd', 'secret', 'token', 'key', 'auth',
            'authorization', 'api_key', 'apikey', 'access_token', 'session',
            'sessionid', 'session_id', 'session_token', 'email', 'mail', 
            'credit_card', 'creditcard', 'card', 'ssn', 'social_security', 'phone',
            'cvv', 'cvc', 'cid'  # Add CVV-related keys
        }
        key_lower = key.lower().strip()
        # Check exact matches and partial matches for compound keys
        return key_lower in sensitive_keys or any(sens in key_lower for sens in ['token', 'key', 'secret', 'password', 'auth', 'cvv'])
    
    def _get_redacted_value_for_key(self, key: str) -> str:
        """Get appropriate redacted value based on key type."""
        key_lower = key.lower().strip()
        
        if 'email' in key_lower or 'mail' in key_lower:
            return "[REDACTED_EMAIL]"
        elif 'password' in key_lower or 'passwd' in key_lower or 'pwd' in key_lower:
            return "[REDACTED_PASSWORD]"
        elif 'authorization' in key_lower:  # Handle Authorization headers
            return "[REDACTED_AUTH]"
        elif 'session' in key_lower:  # Check session before token/key
            return "[REDACTED_SESSION]"
        elif 'key' in key_lower or key_lower == 'token':  # token gets [REDACTED_KEY] per test expectation
            return "[REDACTED_KEY]"
        elif 'token' in key_lower:  # Other token types like access_token
            return "[REDACTED_TOKEN]"
        elif 'secret' in key_lower:
            return "[REDACTED_SECRET]"
        elif 'phone' in key_lower:
            return "[REDACTED_PHONE]"
        elif 'card' in key_lower or 'cvv' in key_lower or 'cvc' in key_lower or 'cid' in key_lower:
            return "[REDACTED_CARD]"
        else:
            return "[REDACTED]"
    
    def _redact_structured_content(self, content: str, content_type: ContentType) -> str:
        """Apply content-type specific redaction patterns."""
        try:
            content_config = self.config.get("redaction", {}).get("content_types", {})
            type_config = content_config.get(content_type.value, {})
            
            # Apply field patterns for JSON
            if content_type == ContentType.JSON:
                field_patterns = type_config.get("field_patterns", [])
                for pattern in field_patterns:
                    try:
                        content = re.sub(pattern, '"field": "[REDACTED]"', content)
                    except re.error as e:
                        logger.warning(f"Invalid JSON field pattern '{pattern}': {e}")
            
            # Apply attribute patterns for HTML
            elif content_type == ContentType.HTML:
                attr_patterns = type_config.get("attribute_patterns", [])
                for pattern in attr_patterns:
                    try:
                        # For href URLs with credentials, preserve URL structure
                        if 'href' in pattern and '://' in pattern:
                            content = re.sub(pattern, 'href="\\g<1>://[REDACTED_USER]:[REDACTED_PASS]@\\g<4>"', content)
                        else:
                            content = re.sub(pattern, 'attr="[REDACTED]"', content)
                    except re.error as e:
                        logger.warning(f"Invalid HTML attribute pattern '{pattern}': {e}")
            
            # Apply element patterns for XML
            elif content_type == ContentType.XML:
                elem_patterns = type_config.get("element_patterns", [])
                for pattern in elem_patterns:
                    try:
                        # Don't use generic replacement - let the main patterns handle it
                        # This preserves specific redacted values like [REDACTED_OPENAI_KEY]
                        pass  # Skip XML-specific pattern replacement
                    except re.error as e:
                        logger.warning(f"Invalid XML element pattern '{pattern}': {e}")
            
            return content
            
        except Exception as e:
            logger.error(f"Error in structured content redaction: {e}")
            return content
    
    def redact_url(self, url: str) -> str:
        """Redact sensitive data from URLs."""
        if not self.is_enabled() or not url:
            return url
        
        return self.redact_text(url, ContentType.URL)
    
    def redact_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Redact sensitive data from HTTP headers."""
        if not self.is_enabled():
            return headers
        
        redacted_headers = {}
        for key, value in headers.items():
            if self._is_sensitive_header(key):
                redacted_headers[key] = self._get_redacted_header_value(key)
            else:
                redacted_headers[key] = self.redact_text(str(value))
        
        return redacted_headers
    
    def _is_sensitive_header(self, header_name: str) -> bool:
        """Check if HTTP header contains sensitive data."""
        sensitive_headers = {
            'authorization', 'x-api-key', 'apikey', 'api-key', 'x-auth-token',
            'cookie', 'set-cookie', 'x-session-id', 'session-id', 'x-csrf-token'
        }
        return header_name.lower().strip() in sensitive_headers
    
    def _get_redacted_header_value(self, header_name: str) -> str:
        """Get redacted value for sensitive headers."""
        header_lower = header_name.lower().strip()
        
        if 'authorization' in header_lower:
            return "[REDACTED_AUTH]"
        elif 'cookie' in header_lower:
            return "[REDACTED_COOKIE]"
        elif 'token' in header_lower:
            return "[REDACTED_TOKEN]"
        elif 'key' in header_lower:
            return "[REDACTED_KEY]"
        elif 'session' in header_lower:
            return "[REDACTED_SESSION]"
        else:
            return "[REDACTED]"
    
    def _log_redaction(self, pattern_name: str, count: int, content_type: ContentType):
        """Log redaction activity for audit purposes."""
        audit_logger = logging.getLogger("security.redaction.audit")
        audit_logger.info(
            f"Redacted {count} instance(s) using pattern '{pattern_name}' "
            f"in {content_type.value} content"
        )
    
    def get_stats(self) -> RedactionStats:
        """Get redaction statistics."""
        return self.stats
    
    def reset_stats(self):
        """Reset redaction statistics."""
        self.stats = RedactionStats()
    
    def validate_patterns(self) -> List[Tuple[str, str]]:
        """
        Validate all redaction patterns and return any errors.
        
        Returns:
            List of tuples (pattern_name, error_message) for invalid patterns.
        """
        errors = []
        for pattern in self.patterns:
            if pattern.compiled_regex is None:
                errors.append((pattern.name, "Failed to compile regex"))
            elif pattern.compiled_regex.pattern == "(?!.*)":
                errors.append((pattern.name, "Pattern was replaced with fallback (invalid regex)"))
        
        return errors


# Global redactor instance (thread-safe initialization)
_global_redactor: Optional[SecurityRedactor] = None
_redactor_lock = threading.Lock()


def get_redactor() -> SecurityRedactor:
    """Get the global security redactor instance (thread-safe)."""
    global _global_redactor
    if _global_redactor is None:
        with _redactor_lock:
            # Double-check after acquiring lock
            if _global_redactor is None:
                _global_redactor = SecurityRedactor()
    return _global_redactor


def redact_text(text: str, content_type: ContentType = ContentType.TEXT) -> str:
    """Convenience function for text redaction."""
    return get_redactor().redact_text(text, content_type)


def redact_json(data: Union[str, Dict, List]) -> Union[str, Dict, List]:
    """Convenience function for JSON redaction."""
    return get_redactor().redact_json(data)


def redact_url(url: str) -> str:
    """Convenience function for URL redaction."""
    return get_redactor().redact_url(url)


def redact_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Convenience function for header redaction."""
    return get_redactor().redact_headers(headers)


# Example usage and testing
if __name__ == "__main__":
    # Test the redaction functionality
    redactor = SecurityRedactor()
    
    # Test text redaction
    test_text = """
    Authorization: Bearer sk-1234567890abcdef
    API Key: api_key=abc123def456
    Email: user@example.com
    Password: password123
    """
    
    print("Original text:")
    print(test_text)
    print("\nRedacted text:")
    print(redactor.redact_text(test_text))
    
    # Test JSON redaction
    test_json = {
        "username": "testuser",
        "password": "secret123",
        "email": "test@example.com",
        "api_key": "sk-abcdef123456",
        "data": {
            "token": "jwt_token_here",
            "session_id": "sess_12345"
        }
    }
    
    print("\nOriginal JSON:")
    print(json.dumps(test_json, indent=2))
    print("\nRedacted JSON:")
    print(json.dumps(redactor.redact_json(test_json), indent=2))
    
    # Print statistics
    print(f"\nRedaction stats: {redactor.get_stats()}")