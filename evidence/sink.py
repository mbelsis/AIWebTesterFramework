import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import redaction utilities for secure artifact storage
try:
    from utils.redaction import get_redactor, redact_text, redact_json, ContentType
    REDACTION_AVAILABLE = True
except ImportError:
    from enum import Enum
    REDACTION_AVAILABLE = False
    
    class ContentType(Enum):
        HTML = "html"
    
    def get_redactor():
        return None

logger = logging.getLogger(__name__)

class EvidenceSink:
    def __init__(self, artifacts_dir: str):
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.logs: List[Dict[str, Any]] = []
        
        # Initialize redaction if available
        self.redactor = None
        if REDACTION_AVAILABLE:
            try:
                self.redactor = get_redactor()
                if self.redactor.is_enabled():
                    logger.info("Security redaction enabled for evidence collection")
            except Exception as e:
                logger.warning(f"Failed to initialize redactor: {e}")
                self.redactor = None

    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Log an event with timestamp, applying redaction to sensitive data"""
        try:
            # Apply redaction to event data if redactor is available
            redacted_data = data
            if self.redactor and self.redactor.is_enabled():
                redacted_data = self.redactor.redact_json(data)
            
            event = {
                "timestamp": time.time(),
                "type": event_type,
                "data": redacted_data
            }
            self.logs.append(event)
            
        except Exception as e:
            logger.error(f"Error logging event with redaction: {e}")
            # Fallback to original data if redaction fails
            event = {
                "timestamp": time.time(),
                "type": event_type,
                "data": data
            }
            self.logs.append(event)

    def save_screenshot(self, screenshot_data: bytes, filename: Optional[str] = None) -> str:
        """Save screenshot and return filename"""
        if not filename:
            filename = f"screenshot_{int(time.time())}.png"
        
        screenshot_path = self.artifacts_dir / filename
        with open(screenshot_path, "wb") as f:
            f.write(screenshot_data)
        
        return filename

    def save_logs(self):
        """Save all collected logs to file with additional redaction pass"""
        logs_file = self.artifacts_dir / "events.json"
        
        try:
            # Apply final redaction pass to the entire log structure
            logs_to_save = self.logs
            if self.redactor and self.redactor.is_enabled():
                # redact_json expects a single object, so we process the logs list appropriately
                logs_to_save = [self.redactor.redact_json(log) for log in self.logs]
            
            with open(logs_file, "w") as f:
                json.dump(logs_to_save, f, indent=2)
                
            logger.info(f"Saved {len(self.logs)} events to {logs_file}")
            
        except Exception as e:
            logger.error(f"Error saving logs with redaction: {e}")
            # Fallback to original logs
            with open(logs_file, "w") as f:
                json.dump(self.logs, f, indent=2)

    def get_artifact_files(self) -> List[str]:
        """Get list of all artifact files"""
        return [f.name for f in self.artifacts_dir.iterdir() if f.is_file()]
    
    def redact_html_content(self, html_content: str) -> str:
        """Redact sensitive data from HTML content (DOM snapshots)"""
        if not self.redactor or not self.redactor.is_enabled():
            return html_content
        
        try:
            return self.redactor.redact_text(html_content, ContentType.HTML)
        except Exception as e:
            logger.error(f"Error redacting HTML content: {e}")
            return html_content
    
    def save_redacted_html(self, html_content: str, filename: Optional[str] = None) -> str:
        """Save HTML content with redaction applied"""
        if not filename:
            filename = f"dom_snapshot_{int(time.time())}.html"
        
        try:
            # Apply redaction to HTML content
            redacted_html = self.redact_html_content(html_content)
            
            html_path = self.artifacts_dir / filename
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(redacted_html)
            
            logger.debug(f"Saved redacted HTML snapshot: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving redacted HTML: {e}")
            # Fallback to original content
            html_path = self.artifacts_dir / filename
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            return filename