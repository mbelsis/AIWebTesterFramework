from playwright.async_api import async_playwright
from pathlib import Path

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
    
    return p, browser, context, page