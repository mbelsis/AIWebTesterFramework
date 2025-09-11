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
    
    def save_watchdog_state_snapshot(self, state_data: Dict[str, Any], run_id: Optional[str] = None) -> str:
        """
        Save watchdog state snapshot for debugging stuck-screen detection.
        
        Args:
            state_data: Watchdog state information including DOM hash, pixel signature, etc.
            run_id: Optional run ID for organization
            
        Returns:
            Filename of the saved state snapshot
        """
        timestamp = int(time.time())
        filename = f"watchdog_state_{run_id}_{timestamp}.json" if run_id else f"watchdog_state_{timestamp}.json"
        
        try:
            # Apply redaction to state data
            redacted_data = state_data
            if self.redactor and self.redactor.is_enabled():
                redacted_data = self.redactor.redact_json(state_data)
            
            # Add timestamp and metadata
            snapshot = {
                "timestamp": timestamp,
                "run_id": run_id,
                "state_data": redacted_data,
                "snapshot_type": "watchdog_state"
            }
            
            state_path = self.artifacts_dir / filename
            with open(state_path, "w") as f:
                json.dump(snapshot, f, indent=2)
            
            logger.debug(f"Saved watchdog state snapshot: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving watchdog state snapshot: {e}")
            return ""
    
    def save_watchdog_comparison(self, previous_state: Dict[str, Any], current_state: Dict[str, Any], 
                                changes: Dict[str, bool], run_id: Optional[str] = None) -> str:
        """
        Save state comparison data for watchdog debugging.
        
        Args:
            previous_state: Previous watchdog state
            current_state: Current watchdog state  
            changes: Dictionary indicating which indicators changed
            run_id: Optional run ID for organization
            
        Returns:
            Filename of the saved comparison data
        """
        timestamp = int(time.time())
        filename = f"watchdog_comparison_{run_id}_{timestamp}.json" if run_id else f"watchdog_comparison_{timestamp}.json"
        
        try:
            # Apply redaction to state data
            redacted_previous = previous_state
            redacted_current = current_state
            
            if self.redactor and self.redactor.is_enabled():
                redacted_previous = self.redactor.redact_json(previous_state)
                redacted_current = self.redactor.redact_json(current_state)
            
            comparison = {
                "timestamp": timestamp,
                "run_id": run_id,
                "previous_state": redacted_previous,
                "current_state": redacted_current,
                "changes_detected": changes,
                "stuck_detection": not any(changes.values()),
                "snapshot_type": "watchdog_comparison"
            }
            
            comparison_path = self.artifacts_dir / filename
            with open(comparison_path, "w") as f:
                json.dump(comparison, f, indent=2)
            
            logger.debug(f"Saved watchdog comparison: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving watchdog comparison: {e}")
            return ""
    
    def save_watchdog_health_metrics(self, stats: Dict[str, Any], run_id: Optional[str] = None) -> str:
        """
        Save watchdog health metrics and statistics.
        
        Args:
            stats: Watchdog statistics and health metrics
            run_id: Optional run ID for organization
            
        Returns:
            Filename of the saved metrics data
        """
        timestamp = int(time.time())
        filename = f"watchdog_metrics_{run_id}_{timestamp}.json" if run_id else f"watchdog_metrics_{timestamp}.json"
        
        try:
            # Apply redaction to metrics (minimal needed since it's mostly numbers)
            redacted_stats = stats
            if self.redactor and self.redactor.is_enabled():
                redacted_stats = self.redactor.redact_json(stats)
            
            metrics = {
                "timestamp": timestamp,
                "run_id": run_id,
                "watchdog_stats": redacted_stats,
                "snapshot_type": "watchdog_health_metrics"
            }
            
            metrics_path = self.artifacts_dir / filename
            with open(metrics_path, "w") as f:
                json.dump(metrics, f, indent=2)
            
            logger.debug(f"Saved watchdog health metrics: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving watchdog health metrics: {e}")
            return ""
    
    def save_enhanced_screenshot(self, screenshot_data: bytes, metadata: Dict[str, Any], 
                                filename: Optional[str] = None) -> str:
        """
        Save screenshot with enhanced metadata for watchdog debugging.
        
        Args:
            screenshot_data: Screenshot image data
            metadata: Enhanced metadata including state information
            filename: Optional filename, generates one if not provided
            
        Returns:
            Filename of the saved screenshot
        """
        timestamp = int(time.time())
        if not filename:
            filename = f"watchdog_screenshot_{timestamp}.png"
        
        metadata_filename = f"{filename.rsplit('.', 1)[0]}_metadata.json"
        
        try:
            # Save the screenshot
            screenshot_path = self.artifacts_dir / filename
            with open(screenshot_path, "wb") as f:
                f.write(screenshot_data)
            
            # Apply redaction to metadata
            redacted_metadata = metadata
            if self.redactor and self.redactor.is_enabled():
                redacted_metadata = self.redactor.redact_json(metadata)
            
            # Save enhanced metadata
            enhanced_metadata = {
                "timestamp": timestamp,
                "screenshot_file": filename,
                "metadata": redacted_metadata,
                "snapshot_type": "enhanced_screenshot"
            }
            
            metadata_path = self.artifacts_dir / metadata_filename
            with open(metadata_path, "w") as f:
                json.dump(enhanced_metadata, f, indent=2)
            
            logger.debug(f"Saved enhanced screenshot with metadata: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving enhanced screenshot: {e}")
            # Fallback to basic screenshot save
            return self.save_screenshot(screenshot_data, filename)
    
    def get_watchdog_artifacts(self) -> List[str]:
        """Get list of all watchdog-related artifact files."""
        try:
            watchdog_files = []
            for f in self.artifacts_dir.iterdir():
                if f.is_file() and any(pattern in f.name for pattern in [
                    'watchdog_state', 'watchdog_comparison', 'watchdog_metrics', 
                    'watchdog_screenshot', 'stuck_state'
                ]):
                    watchdog_files.append(f.name)
            
            return sorted(watchdog_files)
            
        except Exception as e:
            logger.error(f"Error getting watchdog artifacts: {e}")
            return []