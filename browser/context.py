from playwright.async_api import async_playwright
from pathlib import Path

async def create_context(headful: bool, artifacts_dir: str):
    """Create browser context with video recording and tracing"""
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=not headful)
    
    # Create context with video recording
    context = await browser.new_context(
        record_video_dir=str(Path(artifacts_dir) / "video"),
        viewport={"width": 1280, "height": 720}
    )
    
    # Start tracing
    await context.tracing.start(screenshots=True, snapshots=True, sources=True)
    
    # Create page
    page = await context.new_page()
    
    return browser, context, page