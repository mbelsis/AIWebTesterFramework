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
            filename = f"screenshot_{time.time_ns()}.png"
        
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
        """Get list of all artifact files recursively, including videos in subdirectories"""
        try:
            artifact_files = []
            
            # Use recursive glob to find all files
            for file_path in self.artifacts_dir.rglob("*"):
                if file_path.is_file():
                    # Get relative path from artifacts_dir to maintain structure
                    relative_path = file_path.relative_to(self.artifacts_dir)
                    artifact_files.append(str(relative_path))
            
            logger.debug(f"Found {len(artifact_files)} artifact files recursively")
            return artifact_files
            
        except Exception as e:
            logger.error(f"Error listing artifact files recursively: {e}")
            return []
    
    def get_categorized_artifacts(self) -> Dict[str, List[str]]:
        """Get artifacts categorized by type."""
        try:
            all_files = self.get_artifact_files()
            
            categorized = {
                "videos": [],
                "traces": [],
                "screenshots": [],
                "logs": [],
                "html_snapshots": [],
                "watchdog_artifacts": [],
                "other": []
            }
            
            for file in all_files:
                if file.endswith(('.webm', '.mp4', '.avi')):
                    categorized["videos"].append(file)
                elif file.endswith('.zip') and 'trace' in file:
                    categorized["traces"].append(file)
                elif file.endswith('.png') or file.endswith('.jpg'):
                    categorized["screenshots"].append(file)
                elif file.endswith('.json'):
                    if any(pattern in file for pattern in ['watchdog', 'stuck_state']):
                        categorized["watchdog_artifacts"].append(file)
                    else:
                        categorized["logs"].append(file)
                elif file.endswith('.html'):
                    categorized["html_snapshots"].append(file)
                else:
                    categorized["other"].append(file)
            
            return categorized
        except Exception as e:
            logger.error(f"Error categorizing artifacts: {e}")
            return {"error": [str(e)]}
    
    def validate_video_artifacts(self) -> Dict[str, Any]:
        """Validate video artifacts for completeness and playability."""
        validation_result = {
            "valid_videos": [],
            "invalid_videos": [],
            "missing_videos": [],
            "total_video_size_bytes": 0,
            "validation_errors": []
        }
        
        try:
            video_dir = self.artifacts_dir / "video"
            
            if not video_dir.exists():
                validation_result["missing_videos"].append("Video directory does not exist")
                return validation_result
            
            # Find all video files
            video_files = list(video_dir.glob("*.webm")) + list(video_dir.glob("*.mp4"))
            
            if not video_files:
                validation_result["missing_videos"].append("No video files found in video directory")
                return validation_result
            
            for video_file in video_files:
                try:
                    if video_file.exists() and video_file.stat().st_size > 0:
                        file_size = video_file.stat().st_size
                        validation_result["valid_videos"].append({
                            "name": video_file.name,
                            "path": str(video_file),
                            "size_bytes": file_size,
                            "size_mb": round(file_size / (1024 * 1024), 2)
                        })
                        validation_result["total_video_size_bytes"] += file_size
                    else:
                        validation_result["invalid_videos"].append({
                            "name": video_file.name,
                            "issue": "File is empty or does not exist"
                        })
                except Exception as e:
                    validation_result["invalid_videos"].append({
                        "name": video_file.name,
                        "issue": f"Error accessing file: {str(e)}"
                    })
            
            return validation_result
            
        except Exception as e:
            error_msg = f"Critical error during video validation: {str(e)}"
            logger.error(error_msg)
            validation_result["validation_errors"].append(error_msg)
            return validation_result
    
    def generate_artifact_summary(self, finalization_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate comprehensive artifact summary including video validation."""
        try:
            summary = {
                "timestamp": time.time(),
                "artifacts_directory": str(self.artifacts_dir),
                "categorized_files": self.get_categorized_artifacts(),
                "video_validation": self.validate_video_artifacts(),
                "total_events_logged": len(self.logs)
            }
            
            # Include finalization results if provided
            if finalization_result:
                summary["finalization_status"] = finalization_result
                
            # Calculate total artifact size
            try:
                total_size = sum(f.stat().st_size for f in self.artifacts_dir.rglob('*') if f.is_file())
                summary["total_artifacts_size_bytes"] = total_size
                summary["total_artifacts_size_mb"] = round(total_size / (1024 * 1024), 2)
            except Exception as e:
                summary["size_calculation_error"] = str(e)
            
            # Get watchdog artifacts summary
            watchdog_artifacts = self.get_watchdog_artifacts()
            if watchdog_artifacts:
                summary["watchdog_artifacts_count"] = len(watchdog_artifacts)
            
            return summary
            
        except Exception as e:
            error_msg = f"Error generating artifact summary: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "timestamp": time.time()}
    
    def save_artifact_summary(self, finalization_result: Optional[Dict[str, Any]] = None, 
                             filename: str = "artifact_summary.json") -> str:
        """Generate and save comprehensive artifact summary."""
        try:
            summary = self.generate_artifact_summary(finalization_result)
            
            summary_path = self.artifacts_dir / filename
            with open(summary_path, "w") as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"Artifact summary saved to {summary_path}")
            
            # Log the summary generation
            self.log_event("artifact_summary_generated", {
                "summary_path": str(summary_path),
                "total_files": len(summary.get("categorized_files", {}).get("videos", [])) + 
                              len(summary.get("categorized_files", {}).get("traces", [])) + 
                              len(summary.get("categorized_files", {}).get("screenshots", [])),
                "valid_videos": len(summary.get("video_validation", {}).get("valid_videos", [])),
                "finalization_status": finalization_result.get("status") if finalization_result else None
            })
            
            return str(summary_path)
            
        except Exception as e:
            error_msg = f"Error saving artifact summary: {str(e)}"
            logger.error(error_msg)
            self.log_event("artifact_summary_error", {"error": error_msg})
            return ""
    
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
            filename = f"dom_snapshot_{time.time_ns()}.html"
        
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
        timestamp = time.time_ns()
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
        timestamp = time.time_ns()
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
        timestamp = time.time_ns()
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
        timestamp = time.time_ns()
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
            for f in self.artifacts_dir.rglob('*'):  # Use rglob to check subdirectories too
                if f.is_file() and any(pattern in f.name for pattern in [
                    'watchdog_state', 'watchdog_comparison', 'watchdog_metrics', 
                    'watchdog_screenshot', 'stuck_state'
                ]):
                    watchdog_files.append(str(f.relative_to(self.artifacts_dir)))
            
            return sorted(watchdog_files)
            
        except Exception as e:
            logger.error(f"Error getting watchdog artifacts: {e}")
            return []