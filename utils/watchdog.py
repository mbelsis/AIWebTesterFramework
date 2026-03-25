"""
Stuck-screen watchdog system for detecting and handling frozen UI states during browser automation testing.

This module provides comprehensive state tracking and recovery mechanisms for browser automation,
detecting when pages become unresponsive or stuck and implementing intelligent recovery strategies.
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import yaml

# Import existing utilities
try:
    from utils.redaction import get_redactor, ContentType
    REDACTION_AVAILABLE = True
except ImportError:
    REDACTION_AVAILABLE = False
    
    class ContentType(Enum):
        TEXT = "text"
    
    def get_redactor():
        return None

logger = logging.getLogger(__name__)


class RecoveryStrategy(Enum):
    """Available recovery strategies when stuck state is detected."""
    BACK_NAVIGATION = "back_navigation"
    PAGE_RELOAD = "page_reload"
    STEP_REPLANNING = "step_replanning"
    GRACEFUL_CONTINUATION = "graceful_continuation"
    TIMEOUT_FAILURE = "timeout_failure"


class StateIndicator(Enum):
    """Types of UI state indicators to monitor."""
    DOM_HASH = "dom_hash"
    REQUEST_COUNT = "request_count"
    PIXEL_SIGNATURE = "pixel_signature"


@dataclass
class WatchdogState:
    """Represents the current UI state for comparison."""
    timestamp: float
    dom_hash: Optional[str] = None
    request_count: int = 0
    pixel_signature: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    
    def has_changed(self, other: "WatchdogState", ignore_timestamp: bool = True) -> Dict[str, bool]:
        """
        Compare this state with another to detect changes.
        
        Args:
            other: Another watchdog state to compare against
            ignore_timestamp: Whether to ignore timestamp in comparison
            
        Returns:
            Dictionary indicating which indicators have changed
        """
        changes = {}
        
        if not ignore_timestamp:
            changes["timestamp"] = self.timestamp != other.timestamp
            
        changes["dom_hash"] = self.dom_hash != other.dom_hash
        changes["request_count"] = self.request_count != other.request_count
        changes["pixel_signature"] = self.pixel_signature != other.pixel_signature
        changes["url"] = self.url != other.url
        changes["title"] = self.title != other.title
        
        return changes
    
    def any_changed(self, other: "WatchdogState", indicators: Optional[List[StateIndicator]] = None) -> bool:
        """
        Check if any of the specified indicators have changed.
        
        Args:
            other: Another watchdog state to compare against
            indicators: List of specific indicators to check, all if None
            
        Returns:
            True if any indicator has changed, False otherwise
        """
        changes = self.has_changed(other)
        
        if indicators is None:
            # Check all state indicators except timestamp and metadata
            return changes.get("dom_hash", False) or \
                   changes.get("request_count", False) or \
                   changes.get("pixel_signature", False)
        
        indicator_map = {
            StateIndicator.DOM_HASH: "dom_hash",
            StateIndicator.REQUEST_COUNT: "request_count", 
            StateIndicator.PIXEL_SIGNATURE: "pixel_signature"
        }
        
        return any(changes.get(indicator_map[ind], False) for ind in indicators)


@dataclass
class WatchdogConfig:
    """Configuration settings for the watchdog system."""
    enabled: bool = True
    timeout_seconds: float = 12.0
    recovery_strategies: List[RecoveryStrategy] = None
    max_recovery_attempts: int = 3
    state_indicators: List[StateIndicator] = None
    capture_screenshots: bool = True
    log_level: str = "INFO"
    check_interval: float = 2.0
    dom_hash_depth: int = 3
    pixel_sample_regions: int = 9
    
    def __post_init__(self):
        """Initialize default values for lists."""
        if self.recovery_strategies is None:
            self.recovery_strategies = [
                RecoveryStrategy.BACK_NAVIGATION,
                RecoveryStrategy.PAGE_RELOAD,
                RecoveryStrategy.GRACEFUL_CONTINUATION,
                RecoveryStrategy.TIMEOUT_FAILURE
            ]
        
        if self.state_indicators is None:
            self.state_indicators = [
                StateIndicator.DOM_HASH,
                StateIndicator.REQUEST_COUNT,
                StateIndicator.PIXEL_SIGNATURE
            ]


@dataclass
class WatchdogStats:
    """Statistics about watchdog operations."""
    total_checks: int = 0
    stuck_detections: int = 0
    recovery_attempts: int = 0
    successful_recoveries: int = 0
    failed_recoveries: int = 0
    recovery_strategy_stats: Optional[Dict[str, int]] = None
    
    def __post_init__(self):
        """Initialize recovery strategy statistics."""
        if self.recovery_strategy_stats is None:
            self.recovery_strategy_stats = {
                strategy.value: 0 for strategy in RecoveryStrategy
            }


class Watchdog:
    """
    Main watchdog class for detecting stuck UI states and implementing recovery strategies.
    
    This class monitors multiple UI state indicators and triggers recovery actions when
    the browser automation appears to be stuck or unresponsive.
    """
    
    def __init__(self, config_path: Optional[str] = None, sink = None):
        """
        Initialize the watchdog system.
        
        Args:
            config_path: Path to watchdog configuration file
            sink: Evidence sink for logging and artifact collection
        """
        self.config = self._load_config(config_path)
        self.sink = sink
        self.stats = WatchdogStats()
        self.current_state: Optional[WatchdogState] = None
        self.previous_state: Optional[WatchdogState] = None
        self.stuck_since: Optional[float] = None
        self.recovery_attempts: int = 0
        self._monitoring_active = False
        self._monitoring_task: Optional[asyncio.Task] = None
        self._request_count = 0
        
        # Initialize redaction if available
        self.redactor = None
        if REDACTION_AVAILABLE:
            try:
                self.redactor = get_redactor()
                if self.redactor and self.redactor.is_enabled():
                    logger.info("Security redaction enabled for watchdog operations")
            except Exception as e:
                logger.warning(f"Failed to initialize redactor in watchdog: {e}")
                self.redactor = None
        
        logger.info(f"Watchdog initialized with timeout: {self.config.timeout_seconds}s, "
                   f"strategies: {[s.value for s in self.config.recovery_strategies]}")
    
    def _load_config(self, config_path: Optional[str] = None) -> WatchdogConfig:
        """Load watchdog configuration from YAML file or use defaults."""
        if config_path is None:
            config_path = str(Path(__file__).parent.parent / "configs" / "watchdog.yaml")
        
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            watchdog_config = config_data.get("watchdog", {})
            
            # Parse recovery strategies
            strategies = []
            for strategy_name in watchdog_config.get("recovery_strategies", []):
                try:
                    strategies.append(RecoveryStrategy(strategy_name))
                except ValueError:
                    logger.warning(f"Unknown recovery strategy: {strategy_name}")
            
            # Parse state indicators
            indicators = []
            for indicator_name in watchdog_config.get("state_indicators", []):
                try:
                    indicators.append(StateIndicator(indicator_name))
                except ValueError:
                    logger.warning(f"Unknown state indicator: {indicator_name}")
            
            config = WatchdogConfig(
                enabled=watchdog_config.get("enabled", True),
                timeout_seconds=watchdog_config.get("timeout_seconds", 12.0),
                recovery_strategies=strategies if strategies else None,
                max_recovery_attempts=watchdog_config.get("max_recovery_attempts", 3),
                state_indicators=indicators if indicators else None,
                capture_screenshots=watchdog_config.get("capture_screenshots", True),
                log_level=watchdog_config.get("log_level", "INFO"),
                check_interval=watchdog_config.get("check_interval", 2.0),
                dom_hash_depth=watchdog_config.get("dom_hash_depth", 3),
                pixel_sample_regions=watchdog_config.get("pixel_sample_regions", 9)
            )
            
            logger.info(f"Loaded watchdog configuration from {config_path}")
            return config
            
        except FileNotFoundError:
            logger.info(f"Watchdog config not found at {config_path}, using defaults")
            return WatchdogConfig()
        except (yaml.YAMLError, Exception) as e:
            logger.error(f"Failed to parse watchdog config: {e}, using defaults")
            return WatchdogConfig()
    
    async def capture_state(self, page, context=None) -> WatchdogState:
        """
        Capture current UI state for comparison.
        
        Args:
            page: Playwright page object
            context: Optional browser context for additional metrics
            
        Returns:
            Current watchdog state
        """
        current_time = time.time()
        state = WatchdogState(timestamp=current_time)
        
        try:
            # Capture URL and title
            state.url = page.url
            state.title = await page.title()
            
            # Capture DOM hash if enabled
            if StateIndicator.DOM_HASH in self.config.state_indicators:
                state.dom_hash = await self._generate_dom_hash(page)
            
            # Request count is tracked separately via network monitoring
            if StateIndicator.REQUEST_COUNT in self.config.state_indicators:
                state.request_count = self._request_count
            
            # Capture pixel signature if enabled
            if StateIndicator.PIXEL_SIGNATURE in self.config.state_indicators:
                state.pixel_signature = await self._generate_pixel_signature(page)
                
        except Exception as e:
            logger.error(f"Error capturing watchdog state: {e}")
            
        return state
    
    async def _generate_dom_hash(self, page) -> str:
        """Generate hash of DOM structure for change detection."""
        try:
            # Get simplified DOM structure
            dom_content = await page.evaluate(f"""
                function getDOMContent(element, depth) {{
                    if (depth <= 0) return '';
                    
                    let content = element.tagName || '';
                    if (element.id) content += '#' + element.id;
                    if (element.className) content += '.' + element.className.split(' ').join('.');
                    
                    // Include text content for leaf nodes
                    if (element.children.length === 0 && element.textContent) {{
                        content += '|' + element.textContent.trim().substring(0, 100);
                    }}
                    
                    // Recursively process children
                    for (let child of element.children) {{
                        content += getDOMContent(child, depth - 1);
                    }}
                    
                    return content;
                }}
                
                getDOMContent(document.body, {self.config.dom_hash_depth});
            """)
            
            return hashlib.md5(dom_content.encode('utf-8')).hexdigest()
            
        except Exception as e:
            logger.warning(f"Failed to generate DOM hash: {e}")
            return f"error_{int(time.time())}"
    
    async def _generate_pixel_signature(self, page) -> str:
        """Generate pixel signature for visual change detection."""
        try:
            # Take a lightweight screenshot
            screenshot = await page.screenshot(type='png', full_page=False)
            
            # Generate signature based on content properties (stable, no time)
            # Use screenshot size and a simple hash of the bytes for basic change detection
            screenshot_hash = hashlib.md5(screenshot).hexdigest()[:8]
            signature_data = f"size_{len(screenshot)}_hash_{screenshot_hash}"
            
            return hashlib.md5(signature_data.encode('utf-8')).hexdigest()[:16]
            
        except Exception as e:
            logger.warning(f"Failed to generate pixel signature: {e}")
            return "error_capture_failed"
    
    def track_network_request(self, request_type: str = "request"):
        """Track network request for request count monitoring."""
        self._request_count += 1
        logger.debug(f"Network activity tracked: {request_type}, total requests: {self._request_count}")
    
    async def start_monitoring(self, page, context=None, run_id: Optional[str] = None):
        """
        Start watchdog monitoring for the given page.
        
        Args:
            page: Playwright page object to monitor
            context: Optional browser context
            run_id: Optional run ID for logging context
        """
        if not self.config.enabled:
            logger.info("Watchdog monitoring disabled in configuration")
            return
        
        if self._monitoring_active:
            logger.warning("Watchdog monitoring already active")
            return
        
        self._monitoring_active = True
        self.current_state = await self.capture_state(page, context)
        self.previous_state = None
        self.stuck_since = None
        self.recovery_attempts = 0
        
        # Setup network request tracking
        self._setup_network_tracking(page)
        
        # Start monitoring loop
        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop(page, context, run_id)
        )
        
        logger.info(f"Watchdog monitoring started for {page.url}")
        
        if self.sink:
            self.sink.log_event("watchdog_started", {
                "url": page.url, 
                "run_id": run_id, 
                "config": asdict(self.config)
            })
    
    def _setup_network_tracking(self, page):
        """Setup network request/response tracking for the page."""
        # Remove previous listeners if they exist (uses stable references)
        if hasattr(self, '_on_page_request'):
            try:
                page.remove_listener("request", self._on_page_request)
                page.remove_listener("response", self._on_page_response)
            except Exception:
                pass

        # Store as instance attributes so the same references can be removed later
        self._on_page_request = lambda request: self.track_network_request("request")
        self._on_page_response = lambda response: self.track_network_request("response")

        page.on("request", self._on_page_request)
        page.on("response", self._on_page_response)
    
    async def _monitoring_loop(self, page, context=None, run_id: Optional[str] = None):
        """Main monitoring loop that checks for stuck states."""
        logger.info("Watchdog monitoring loop started")
        
        while self._monitoring_active:
            try:
                await asyncio.sleep(self.config.check_interval)
                
                if not self._monitoring_active:
                    break
                
                await self._check_for_stuck_state(page, context, run_id)
                self.stats.total_checks += 1
                
            except asyncio.CancelledError:
                logger.info("Watchdog monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in watchdog monitoring loop: {e}")
                await asyncio.sleep(1)  # Brief pause before continuing
        
        logger.info("Watchdog monitoring loop ended")
    
    async def _check_for_stuck_state(self, page, context=None, run_id: Optional[str] = None):
        """Check if the UI is in a stuck state and trigger recovery if needed."""
        # Capture current state
        new_state = await self.capture_state(page, context)
        
        # Compare with previous state
        if self.previous_state is None:
            # First check, establish baseline
            self.previous_state = self.current_state
            self.current_state = new_state
            return
        
        # Check if anything has changed
        if new_state.any_changed(self.current_state, self.config.state_indicators):
            # State has changed, reset stuck timer
            if self.stuck_since is not None:
                logger.debug("UI state changed, clearing stuck detection")
                self.stuck_since = None
                self.recovery_attempts = 0
            
            self.previous_state = self.current_state
            self.current_state = new_state
            return
        
        # No change detected
        current_time = time.time()
        
        if self.stuck_since is None:
            # First time detecting potential stuck state
            self.stuck_since = current_time
            logger.debug(f"Potential stuck state detected, starting timeout timer")
            return
        
        # Check if we've exceeded timeout threshold
        stuck_duration = current_time - self.stuck_since
        
        if stuck_duration >= self.config.timeout_seconds:
            logger.warning(f"Stuck state detected! Duration: {stuck_duration:.1f}s, "
                          f"Timeout: {self.config.timeout_seconds}s")
            
            self.stats.stuck_detections += 1
            
            if self.sink:
                self.sink.log_event("stuck_state_detected", {
                    "duration": stuck_duration,
                    "url": page.url,
                    "run_id": run_id,
                    "state": asdict(new_state)
                })
            
            # Trigger recovery
            await self._trigger_recovery(page, context, run_id)
    
    async def _trigger_recovery(self, page, context=None, run_id: Optional[str] = None):
        """Trigger recovery strategies when stuck state is detected."""
        if self.recovery_attempts >= self.config.max_recovery_attempts:
            logger.error(f"Maximum recovery attempts ({self.config.max_recovery_attempts}) reached, giving up")
            
            if self.sink:
                self.sink.log_event("recovery_failed", {
                    "url": page.url,
                    "run_id": run_id,
                    "attempts": self.recovery_attempts,
                    "reason": "max_attempts_exceeded"
                })
            return False
        
        self.recovery_attempts += 1
        self.stats.recovery_attempts += 1
        
        # Try each recovery strategy in order
        for strategy in self.config.recovery_strategies:
            logger.info(f"Attempting recovery strategy: {strategy.value} (attempt {self.recovery_attempts})")
            
            try:
                success = await self._execute_recovery_strategy(strategy, page, context, run_id)
                self.stats.recovery_strategy_stats[strategy.value] += 1
                
                if success:
                    logger.info(f"Recovery successful using strategy: {strategy.value}")
                    self.stats.successful_recoveries += 1
                    
                    # Reset stuck state tracking
                    self.stuck_since = None
                    self._request_count = 0  # Reset request counter
                    
                    if self.sink:
                        self.sink.log_event("recovery_successful", {
                            "strategy": strategy.value,
                            "attempt": self.recovery_attempts,
                            "url": page.url,
                            "run_id": run_id
                        })
                    
                    return True
                    
            except Exception as e:
                logger.error(f"Error executing recovery strategy {strategy.value}: {e}")
                
                if self.sink:
                    self.sink.log_event("recovery_error", {
                        "strategy": strategy.value,
                        "error": str(e),
                        "url": page.url,
                        "run_id": run_id
                    })
        
        # All strategies failed
        logger.error("All recovery strategies failed")
        self.stats.failed_recoveries += 1
        
        if self.sink:
            self.sink.log_event("recovery_failed", {
                "url": page.url,
                "run_id": run_id,
                "attempts": self.recovery_attempts,
                "reason": "all_strategies_failed"
            })
        
        return False
    
    async def _execute_recovery_strategy(self, strategy: RecoveryStrategy, page, context=None, run_id: Optional[str] = None) -> bool:
        """
        Execute a specific recovery strategy.
        
        Args:
            strategy: Recovery strategy to execute
            page: Playwright page object
            context: Optional browser context
            run_id: Optional run ID for logging
            
        Returns:
            True if recovery was successful, False otherwise
        """
        try:
            if strategy == RecoveryStrategy.BACK_NAVIGATION:
                await page.go_back()
                await page.wait_for_load_state("domcontentloaded", timeout=5000)
                return True

            elif strategy == RecoveryStrategy.PAGE_RELOAD:
                await page.reload()
                await page.wait_for_load_state("domcontentloaded", timeout=10000)
                return True
                
            elif strategy == RecoveryStrategy.GRACEFUL_CONTINUATION:
                logger.warning("Using graceful continuation - logging stuck state and proceeding")
                
                # Capture screenshot if enabled
                if self.config.capture_screenshots and self.sink:
                    try:
                        screenshot = await page.screenshot()
                        filename = f"stuck_state_{run_id}_{time.time_ns()}.png"
                        self.sink.save_screenshot(screenshot, filename)
                    except Exception as e:
                        logger.error(f"Failed to capture stuck state screenshot: {e}")
                
                return True  # Always "succeeds" by continuing
                
            elif strategy == RecoveryStrategy.STEP_REPLANNING:
                logger.info("Step re-planning strategy triggered - requires executor integration")
                # This strategy requires integration with the executor's step planning
                # For now, return False to try other strategies
                return False
                
            elif strategy == RecoveryStrategy.TIMEOUT_FAILURE:
                logger.error("Timeout failure strategy - marking as failed")
                return False
                
        except asyncio.TimeoutError:
            logger.warning(f"Recovery strategy {strategy.value} timed out")
            return False
        except Exception as e:
            logger.error(f"Recovery strategy {strategy.value} failed: {e}")
            return False
        
        return False
    
    async def stop_monitoring(self):
        """Stop watchdog monitoring."""
        if not self._monitoring_active:
            return
        
        self._monitoring_active = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
        
        logger.info("Watchdog monitoring stopped")
        
        if self.sink:
            self.sink.log_event("watchdog_stopped", {"stats": asdict(self.stats)})
    
    def get_stats(self) -> WatchdogStats:
        """Get watchdog statistics."""
        return self.stats
    
    def reset_stats(self):
        """Reset watchdog statistics."""
        self.stats = WatchdogStats()
    
    def is_monitoring(self) -> bool:
        """Check if monitoring is currently active."""
        return self._monitoring_active
    
    def get_current_state(self) -> Optional[WatchdogState]:
        """Get the current watchdog state."""
        return self.current_state


# Convenience functions
def create_watchdog(config_path: Optional[str] = None, sink = None) -> Watchdog:
    """Create a watchdog instance with optional configuration."""
    return Watchdog(config_path=config_path, sink=sink)


async def monitor_page_with_watchdog(page, context=None, run_id: Optional[str] = None, 
                                   config_path: Optional[str] = None, sink = None) -> Watchdog:
    """
    Convenience function to start monitoring a page with watchdog.
    
    Args:
        page: Playwright page to monitor
        context: Optional browser context
        run_id: Optional run ID for logging
        config_path: Optional path to watchdog config
        sink: Optional evidence sink
        
    Returns:
        Watchdog instance that is actively monitoring
    """
    watchdog = create_watchdog(config_path, sink)
    await watchdog.start_monitoring(page, context, run_id)
    return watchdog


# Example usage and testing
if __name__ == "__main__":
    # Test configuration loading
    watchdog = Watchdog()
    print(f"Watchdog config: timeout={watchdog.config.timeout_seconds}s")
    print(f"Recovery strategies: {[s.value for s in watchdog.config.recovery_strategies]}")
    print(f"State indicators: {[i.value for i in watchdog.config.state_indicators]}")
    print(f"Stats: {asdict(watchdog.get_stats())}")