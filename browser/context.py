from playwright.async_api import async_playwright
from pathlib import Path
import logging

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

logger = logging.getLogger(__name__)

async def create_context(headful: bool, artifacts_dir: str, env_config: dict | None = None):
    """Create browser context with video recording and tracing"""
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
    
    # Setup redaction for network and console logging if available
    if REDACTION_AVAILABLE:
        redactor = get_redactor()
        if redactor.is_enabled():
            logger.info("Security redaction enabled for browser evidence collection")
            
            # Add request/response interceptors for redaction
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
    
    return p, browser, context, page