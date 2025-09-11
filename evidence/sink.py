import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

class EvidenceSink:
    def __init__(self, artifacts_dir: str):
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.logs: List[Dict[str, Any]] = []

    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Log an event with timestamp"""
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
        """Save all collected logs to file"""
        logs_file = self.artifacts_dir / "events.json"
        with open(logs_file, "w") as f:
            json.dump(self.logs, f, indent=2)

    def get_artifact_files(self) -> List[str]:
        """Get list of all artifact files"""
        return [f.name for f in self.artifacts_dir.iterdir() if f.is_file()]