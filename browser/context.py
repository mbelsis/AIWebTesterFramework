from playwright.async_api import async_playwright
from pathlib import Path
import logging
import time
import hashlib
import asyncio
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict

# Import redaction utilities for secure evidence collection
try:
    from utils.redaction import get_redactor, redact_text, ContentType
    REDACTION_AVAILABLE = True
except ImportError:
    from enum import Enum
    REDACTION_AVAILABLE = False
    
    class ContentType(Enum):
        TEXT = "text"
    
    def get_redactor():
        return None

# Import watchdog utilities for state tracking integration
try:
    from utils.watchdog import WatchdogState
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    
    @dataclass 
    class WatchdogState:
        timestamp: float
        dom_hash: Optional[str] = None
        request_count: int = 0
        pixel_signature: Optional[str] = None
        url: Optional[str] = None
        title: Optional[str] = None

logger = logging.getLogger(__name__)


@dataclass
class NetworkActivity:
    """Tracks network activity for watchdog monitoring."""
    request_count: int = 0
    response_count: int = 0
    last_request_time: float = 0.0
    last_response_time: float = 0.0
    request_urls: List[str] = None
    
    def __post_init__(self):
        if self.request_urls is None:
            self.request_urls = []
    
    def track_request(self, url: str):
        """Track a network request."""
        self.request_count += 1
        self.last_request_time = time.time()
        # Keep only the last 10 URLs for memory efficiency
        self.request_urls.append(url)
        if len(self.request_urls) > 10:
            self.request_urls.pop(0)
    
    def track_response(self):
        """Track a network response."""
        self.response_count += 1
        self.last_response_time = time.time()
    
    def get_activity_summary(self) -> Dict[str, Any]:
        """Get summary of network activity."""
        return {
            "request_count": self.request_count,
            "response_count": self.response_count,
            "last_request_time": self.last_request_time,
            "last_response_time": self.last_response_time,
            "recent_urls": self.request_urls[-3:] if self.request_urls else []
        }


class StateCapture:
    """Helper class for capturing browser state for watchdog monitoring."""
    
    def __init__(self, redactor=None):
        """Initialize state capture with optional redaction."""
        self.redactor = redactor
    
    async def capture_dom_hash(self, page, depth: int = 3) -> str:
        """
        Capture DOM hash for structural change detection.
        
        Args:
            page: Playwright page object
            depth: Depth of DOM traversal for hash generation
            
        Returns:
            MD5 hash of DOM structure
        """
        try:
            # Get simplified DOM structure
            dom_content = await page.evaluate(f"""
                function getDOMContent(element, depth) {{
                    if (depth <= 0 || !element) return '';
                    
                    let content = element.tagName || '';
                    if (element.id) content += '#' + element.id;
                    if (element.className) content += '.' + element.className.split(' ').join('.');
                    
                    // Include text content for leaf nodes
                    if (element.children.length === 0 && element.textContent) {{
                        content += '|' + element.textContent.trim().substring(0, 50);
                    }}
                    
                    // Recursively process children
                    for (let child of element.children) {{
                        content += getDOMContent(child, depth - 1);
                    }}
                    
                    return content;
                }}
                
                getDOMContent(document.body, {depth});
            """)
            
            # Apply redaction if available
            if self.redactor and self.redactor.is_enabled():
                dom_content = self.redactor.redact_text(dom_content, ContentType.TEXT)
            
            return hashlib.md5(dom_content.encode('utf-8')).hexdigest()
            
        except Exception as e:
            logger.warning(f"Failed to capture DOM hash: {e}")
            return f"error_{int(time.time())}"
    
    async def capture_pixel_signature(self, page, regions: int = 9) -> str:
        """
        Capture pixel signature for visual change detection.
        
        Args:
            page: Playwright page object
            regions: Number of regions to sample for signature
            
        Returns:
            Hash representing visual page signature
        """
        try:
            # Take a lightweight screenshot
            screenshot = await page.screenshot(type='png', full_page=False)
            
            # Generate signature based on content properties (stable, no time)
            # Use screenshot size and basic hash for change detection
            screenshot_hash = hashlib.md5(screenshot).hexdigest()[:8]
            signature_data = f"size_{len(screenshot)}_regions_{regions}_hash_{screenshot_hash}"
            
            return hashlib.md5(signature_data.encode('utf-8')).hexdigest()[:16]
            
        except Exception as e:
            logger.warning(f"Failed to capture pixel signature: {e}")
            return "error_capture_failed"
    
    async def capture_page_state(self, page, dom_depth: int = 3, pixel_regions: int = 9) -> WatchdogState:
        """
        Capture comprehensive page state for watchdog monitoring.
        
        Args:
            page: Playwright page object
            dom_depth: Depth for DOM hash generation
            pixel_regions: Number of regions for pixel signature
            
        Returns:
            WatchdogState with captured state data
        """
        current_time = time.time()
        
        try:
            # Capture URL and title
            url = page.url
            title = await page.title()
            
            # Apply redaction to URL if available
            if self.redactor and self.redactor.is_enabled():
                url = self.redactor.redact_url(url)
            
            # Capture DOM hash
            dom_hash = await self.capture_dom_hash(page, dom_depth)
            
            # Capture pixel signature
            pixel_signature = await self.capture_pixel_signature(page, pixel_regions)
            
            return WatchdogState(
                timestamp=current_time,
                dom_hash=dom_hash,
                pixel_signature=pixel_signature,
                url=url,
                title=title
            )
            
        except Exception as e:
            logger.error(f"Error capturing page state: {e}")
            return WatchdogState(timestamp=current_time)


class NetworkActivityTracker:
    """Enhanced network activity tracker for browser contexts."""
    
    def __init__(self, redactor=None, watchdog_callback: Optional[Callable] = None):
        """
        Initialize network activity tracker.
        
        Args:
            redactor: Optional redaction utility for secure logging
            watchdog_callback: Optional callback function for watchdog integration
        """
        self.redactor = redactor
        self.watchdog_callback = watchdog_callback
        self.activity = NetworkActivity()
        
    def setup_tracking(self, page):
        """Setup network tracking for a page."""
        # Setup request tracking
        def on_request(request):
            try:
                # Track with internal counter
                url = request.url
                if self.redactor and self.redactor.is_enabled():
                    url = self.redactor.redact_url(url)
                
                self.activity.track_request(url)
                
                # Notify watchdog if callback provided
                if self.watchdog_callback:
                    self.watchdog_callback("request")
                
                logger.debug(f"Request tracked: {request.method} {url}")
                
            except Exception as e:
                logger.error(f"Error tracking request: {e}")
        
        def on_response(response):
            try:
                # Track response
                self.activity.track_response()
                
                # Notify watchdog if callback provided
                if self.watchdog_callback:
                    self.watchdog_callback("response")
                
                logger.debug(f"Response tracked: {response.status}")
                
            except Exception as e:
                logger.error(f"Error tracking response: {e}")
        
        # Attach listeners
        page.on("request", on_request)
        page.on("response", on_response)
        
        logger.info("Network activity tracking setup completed")
    
    def get_activity_summary(self) -> Dict[str, Any]:
        """Get current activity summary."""
        return self.activity.get_activity_summary()
    
    def reset_counters(self):
        """Reset activity counters."""
        self.activity = NetworkActivity()
        logger.debug("Network activity counters reset")


async def create_context(headful: bool, artifacts_dir: str, env_config: dict | None = None, 
                       enable_watchdog_helpers: bool = True):
    """
    Create browser context with video recording, tracing, and watchdog integration.
    
    Args:
        headful: Whether to run browser in headful mode
        artifacts_dir: Directory for video recordings and artifacts
        env_config: Optional environment configuration
        enable_watchdog_helpers: Whether to enable watchdog state capture helpers
        
    Returns:
        Tuple of (playwright, browser, context, page, network_tracker, state_capture)
    """
    p = await async_playwright().start()
    
    # Get settings from env config if provided
    settings = env_config.get("settings", {}) if env_config else {}
    slow_mo = settings.get("slow_mo", 0)
    
    browser = await p.chromium.launch(
        headless=not headful,
        slow_mo=slow_mo
    )
    
    # Create context with video recording
    context = await browser.new_context(
        record_video_dir=str(Path(artifacts_dir) / "video"),
        viewport={"width": 1280, "height": 720}
    )
    
    # Start tracing
    await context.tracing.start(screenshots=True, snapshots=True, sources=True)
    
    # Create page
    page = await context.new_page()
    
    # Initialize redaction if available
    redactor = None
    if REDACTION_AVAILABLE:
        redactor = get_redactor()
        if redactor.is_enabled():
            logger.info("Security redaction enabled for browser evidence collection")
    
    # Initialize watchdog helpers if enabled
    network_tracker = None
    state_capture = None
    
    if enable_watchdog_helpers:
        try:
            # Initialize state capture helper
            state_capture = StateCapture(redactor=redactor)
            
            # Initialize network activity tracker
            network_tracker = NetworkActivityTracker(redactor=redactor)
            network_tracker.setup_tracking(page)
            
            # Attach state capture helpers to page for easy access
            page.state_capture = state_capture
            page.network_tracker = network_tracker
            
            logger.info("Watchdog integration helpers initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to initialize watchdog helpers: {e}")
            network_tracker = None
            state_capture = None
    
    # Setup request/response interceptors for redaction if available
    if redactor and redactor.is_enabled():
        async def redact_request(route, request):
            """Redact sensitive data from requests before processing."""
            try:
                # Log redacted request info
                redacted_url = redactor.redact_url(request.url)
                logger.debug(f"Request intercepted: {request.method} {redacted_url}")
                
                # Continue with original request
                await route.continue_()
            except Exception as e:
                logger.error(f"Error in request redaction: {e}")
                await route.continue_()
        
        # Intercept all requests for redaction logging
        await page.route("**/*", redact_request)
    
    return p, browser, context, page, network_tracker, state_capture


async def create_context_with_watchdog_callback(headful: bool, artifacts_dir: str, 
                                               watchdog_callback: Optional[Callable] = None,
                                               env_config: dict | None = None):
    """
    Create browser context with integrated watchdog callback for network tracking.
    
    Args:
        headful: Whether to run browser in headful mode
        artifacts_dir: Directory for artifacts
        watchdog_callback: Optional callback function for watchdog integration
        env_config: Optional environment configuration
        
    Returns:
        Tuple of (playwright, browser, context, page, network_tracker, state_capture)
    """
    p, browser, context, page, network_tracker, state_capture = await create_context(
        headful, artifacts_dir, env_config, enable_watchdog_helpers=True
    )
    
    # Setup watchdog callback integration if provided
    if watchdog_callback and network_tracker:
        network_tracker.watchdog_callback = watchdog_callback
        logger.info("Watchdog callback integrated with network tracker")
    
    return p, browser, context, page, network_tracker, state_capture


# Convenience functions for state capture
async def capture_current_state(page, dom_depth: int = 3, pixel_regions: int = 9) -> Optional[WatchdogState]:
    """
    Convenience function to capture current page state.
    
    Args:
        page: Playwright page object
        dom_depth: Depth for DOM hash generation
        pixel_regions: Number of regions for pixel signature
        
    Returns:
        WatchdogState if capture successful, None otherwise
    """
    try:
        # Check if state capture helper is attached
        if hasattr(page, 'state_capture') and page.state_capture:
            return await page.state_capture.capture_page_state(page, dom_depth, pixel_regions)
        else:
            # Fallback: create temporary state capture instance
            redactor = get_redactor() if REDACTION_AVAILABLE else None
            state_capture = StateCapture(redactor=redactor)
            return await state_capture.capture_page_state(page, dom_depth, pixel_regions)
            
    except Exception as e:
        logger.error(f"Failed to capture current page state: {e}")
        return None


def get_network_activity_summary(page) -> Optional[Dict[str, Any]]:
    """
    Get network activity summary from page.
    
    Args:
        page: Playwright page object
        
    Returns:
        Network activity summary dict or None if not available
    """
    try:
        if hasattr(page, 'network_tracker') and page.network_tracker:
            return page.network_tracker.get_activity_summary()
        return None
    except Exception as e:
        logger.error(f"Failed to get network activity summary: {e}")
        return None


async def finalize_video_and_trace(context, artifacts_dir: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Properly finalize video recording and trace collection with durability guarantees.
    CRITICAL FIX: Proper sequence is stop tracing → close context → wait for videos → validate
    
    Args:
        context: Playwright browser context
        artifacts_dir: Directory where artifacts are stored
        timeout: Maximum time to wait for finalization in seconds
        
    Returns:
        Dict containing finalization status and artifact information
    """
    finalization_result = {
        "status": "pending",
        "video_finalized": False,
        "trace_finalized": False,
        "artifacts": {},
        "errors": []
    }
    
    artifacts_path = Path(artifacts_dir)
    
    try:
        logger.info("Starting video and trace finalization...")
        start_time = time.time()
        
        # Step 1: Stop tracing and save trace file
        trace_path = artifacts_path / "trace.zip"
        try:
            await context.tracing.stop(path=str(trace_path))
            
            # Wait for trace file to be written and validate
            for attempt in range(timeout):
                if trace_path.exists() and trace_path.stat().st_size > 0:
                    finalization_result["trace_finalized"] = True
                    finalization_result["artifacts"]["trace"] = {
                        "path": str(trace_path),
                        "size_bytes": trace_path.stat().st_size,
                        "finalized_at": time.time()
                    }
                    logger.info(f"Trace finalized successfully: {trace_path} ({trace_path.stat().st_size} bytes)")
                    break
                await asyncio.sleep(1)
            else:
                finalization_result["errors"].append("Trace file not created within timeout period")
                
        except Exception as e:
            error_msg = f"Error stopping trace: {str(e)}"
            logger.error(error_msg)
            finalization_result["errors"].append(error_msg)
        
        # Step 2: CRITICAL FIX - Close context first to flush videos
        try:
            logger.info("Closing browser context to flush video recordings...")
            await context.close()
            logger.info("Browser context closed successfully - video files should now be flushed")
        except Exception as e:
            error_msg = f"Error closing browser context: {str(e)}"
            logger.error(error_msg)
            finalization_result["errors"].append(error_msg)
        
        # Step 3: NOW wait for video files to appear after context close
        video_dir = artifacts_path / "video"
        try:
            # Give video files time to be written after context close
            await asyncio.sleep(2)
            
            if video_dir.exists():
                # Check for video files and validate them
                video_files = list(video_dir.glob("*.webm")) + list(video_dir.glob("*.mp4"))
                if video_files:
                    video_artifacts = {}
                    for video_file in video_files:
                        # Wait for video file to be stable (no size changes)
                        stable_size = None
                        for attempt in range(timeout):
                            current_size = video_file.stat().st_size if video_file.exists() else 0
                            if stable_size is not None and current_size == stable_size and current_size > 0:
                                # File size is stable, consider it finalized
                                video_artifacts[video_file.name] = {
                                    "path": str(video_file),
                                    "size_bytes": current_size,
                                    "finalized_at": time.time()
                                }
                                logger.info(f"Video finalized: {video_file.name} ({current_size} bytes)")
                                break
                            stable_size = current_size
                            await asyncio.sleep(1)
                        else:
                            finalization_result["errors"].append(f"Video file {video_file.name} did not stabilize within timeout")
                    
                    if video_artifacts:
                        finalization_result["video_finalized"] = True
                        finalization_result["artifacts"]["videos"] = video_artifacts
                        logger.info(f"Video finalization completed: {len(video_artifacts)} files")
                    else:
                        finalization_result["errors"].append("No stable video files found after context close")
                else:
                    # No video files found - this might be expected if recording wasn't active
                    logger.info("No video files found after context close - recording may not have been active")
                    finalization_result["video_finalized"] = True  # Consider it finalized if no files expected
            else:
                logger.info("No video directory found - video recording was not enabled")
                finalization_result["video_finalized"] = True
                
        except Exception as e:
            error_msg = f"Error during video finalization: {str(e)}"
            logger.error(error_msg)
            finalization_result["errors"].append(error_msg)
        
        # Determine overall status
        if finalization_result["video_finalized"] and finalization_result["trace_finalized"]:
            if not finalization_result["errors"]:
                finalization_result["status"] = "success"
            else:
                finalization_result["status"] = "success_with_warnings"
        else:
            finalization_result["status"] = "failed"
        
        elapsed_time = time.time() - start_time
        finalization_result["finalization_duration_seconds"] = elapsed_time
        
        logger.info(f"Finalization completed in {elapsed_time:.2f}s with status: {finalization_result['status']}")
        
        return finalization_result
        
    except Exception as e:
        error_msg = f"Critical error during finalization: {str(e)}"
        logger.error(error_msg)
        finalization_result["status"] = "critical_error"
        finalization_result["errors"].append(error_msg)
        return finalization_result