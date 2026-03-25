"""
Autonomous web application explorer for AI WebTester.

Crawls an authenticated web application, maps all pages/forms/inputs,
uses AI to generate tests, and executes them automatically.
"""

import asyncio
import hashlib
import json
import logging
import time
import yaml
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from urllib.parse import urlparse, urljoin, urlunparse, parse_qs, urlencode

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


async def _wait_for_page_ready(page, timeout: int = 5000):
    """Wait for page to be interactive: domcontentloaded + best-effort networkidle."""
    await page.wait_for_load_state("domcontentloaded")
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass  # Timeout is acceptable — page is interactive after domcontentloaded


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class DiscoveredPage:
    url: str
    normalized_url: str
    title: str
    page_type: str
    dom_hash: str
    forms: List[Dict[str, Any]] = field(default_factory=list)
    inputs: List[Dict[str, Any]] = field(default_factory=list)
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    buttons: List[Dict[str, Any]] = field(default_factory=list)
    screenshot_path: str = ""
    console_errors: List[Dict[str, Any]] = field(default_factory=list)
    network_errors: List[Dict[str, Any]] = field(default_factory=list)
    discovery_method: str = "link"
    parent_url: Optional[str] = None
    depth: int = 0
    module_hint: str = ""


@dataclass
class AppMap:
    base_url: str
    pages: Dict[str, DiscoveredPage] = field(default_factory=dict)
    adjacency: Dict[str, List[str]] = field(default_factory=dict)
    total_forms: int = 0
    total_inputs: int = 0
    total_links: int = 0
    modules: Dict[str, List[str]] = field(default_factory=dict)
    errors_summary: Dict[str, int] = field(default_factory=dict)


@dataclass
class ExplorationResult:
    run_id: str
    app_map: AppMap
    test_plans: List[Dict[str, Any]] = field(default_factory=list)
    test_results: List[Dict[str, Any]] = field(default_factory=list)
    console_errors: List[Dict[str, Any]] = field(default_factory=list)
    network_errors: List[Dict[str, Any]] = field(default_factory=list)
    duration_seconds: float = 0.0
    pages_discovered: int = 0
    tests_executed: int = 0
    tests_passed: int = 0
    tests_failed: int = 0


# ── Configuration ─────────────────────────────────────────────────────────────

def _load_explorer_config() -> Dict[str, Any]:
    config_path = Path(__file__).parent.parent / "configs" / "explorer.yaml"
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f).get("explorer", {})
    except Exception as e:
        logger.warning(f"Could not load explorer config: {e}, using defaults")
        return {}


# ── Authenticator ─────────────────────────────────────────────────────────────

class Authenticator:
    """Handles login via credentials or session cookie injection."""

    def __init__(self, page, context, config: Dict[str, Any]):
        self.page = page
        self.context = context
        self.config = config
        self.login_cfg = config.get("login", {})

    async def login_with_credentials(
        self, login_url: str, username: str, password: str
    ) -> bool:
        logger.info(f"Logging in at {login_url}")
        await self.page.goto(login_url)
        await _wait_for_page_ready(self.page)

        # Auto-detect username field
        user_sel = await self._find_first_selector(
            self.login_cfg.get("username_selectors", ["input[type='email']"])
        )
        if not user_sel:
            logger.error("Could not find username/email field on login page")
            return False

        # Auto-detect password field
        pass_sel = await self._find_first_selector(
            self.login_cfg.get("password_selectors", ["input[type='password']"])
        )
        if not pass_sel:
            logger.error("Could not find password field on login page")
            return False

        # Auto-detect submit button
        submit_sel = await self._find_first_selector(
            self.login_cfg.get("submit_selectors", ["button[type='submit']"])
        )
        if not submit_sel:
            logger.error("Could not find submit button on login page")
            return False

        # Fill and submit
        await self.page.fill(user_sel, username)
        await self.page.fill(pass_sel, password)
        await self.page.click(submit_sel)

        try:
            await _wait_for_page_ready(self.page, timeout=10000)
        except Exception:
            pass  # Some SPAs don't trigger full load

        return await self.verify_authenticated()

    async def login_with_cookie(
        self, base_url: str, cookie_name: str, cookie_value: str
    ) -> bool:
        logger.info(f"Injecting session cookie '{cookie_name}'")
        parsed = urlparse(base_url)
        await self.context.add_cookies([{
            "name": cookie_name,
            "value": cookie_value,
            "domain": parsed.hostname,
            "path": "/",
        }])
        await self.page.goto(base_url)
        await _wait_for_page_ready(self.page)
        return await self.verify_authenticated()

    async def verify_authenticated(self) -> bool:
        """Heuristic check: page is not a login page."""
        html = await self.page.content()
        soup = BeautifulSoup(html, "html.parser")
        page_text = soup.get_text().lower()
        title = (soup.title.string or "").lower() if soup.title else ""

        # If we still see a login form, auth failed
        login_indicators = ["sign in", "log in", "login", "authenticate"]
        has_password_field = soup.find("input", {"type": "password"})

        if has_password_field and any(ind in page_text[:500] or ind in title for ind in login_indicators):
            logger.warning("Authentication appears to have failed — login page still visible")
            return False

        logger.info("Authentication verified — no login page detected")
        return True

    async def _find_first_selector(self, selectors: List[str]) -> Optional[str]:
        for sel in selectors:
            try:
                el = await self.page.query_selector(sel)
                if el and await el.is_visible():
                    return sel
            except Exception:
                continue
        return None


# ── Crawler ───────────────────────────────────────────────────────────────────

class Crawler:
    """BFS crawler that discovers pages, forms, inputs, and errors."""

    def __init__(
        self,
        page,
        context,
        sink,
        base_url: str,
        config: Dict[str, Any],
        module_filter: Optional[List[str]] = None,
    ):
        self.page = page
        self.context = context
        self.sink = sink
        self.base_url = base_url
        self.config = config
        self.module_filter = [m.lower() for m in module_filter] if module_filter else None

        parsed = urlparse(base_url)
        self.base_domain = parsed.hostname

        self.max_depth = config.get("max_depth", 5)
        self.max_pages = config.get("max_pages", 200)
        self.timeout_minutes = config.get("timeout_minutes", 30)
        self.delay = config.get("delay_between_pages", 500) / 1000.0
        self.exclude_patterns = config.get("exclude_patterns", [])
        self.nav_selectors = config.get("nav_selectors", ["nav a"])
        self.spa_cfg = config.get("spa", {})

        self.visited: Dict[str, DiscoveredPage] = {}
        self.console_errors: List[Dict[str, Any]] = []
        self.network_errors: List[Dict[str, Any]] = []

        self._setup_error_listeners()

    def _setup_error_listeners(self):
        self.page.on("console", self._on_console)
        self.page.on("response", self._on_response)
        self.page.on("requestfailed", self._on_request_failed)

    def _on_console(self, msg):
        if msg.type == "error":
            self.console_errors.append({
                "url": self.page.url,
                "type": msg.type,
                "text": msg.text,
                "timestamp": time.time(),
            })

    def _on_response(self, resp):
        if resp.status >= 400:
            self.network_errors.append({
                "url": resp.url,
                "status": resp.status,
                "page_url": self.page.url,
                "timestamp": time.time(),
            })

    def _on_request_failed(self, req):
        self.network_errors.append({
            "url": req.url,
            "failure": str(req.failure) if req.failure else "unknown",
            "page_url": self.page.url,
            "timestamp": time.time(),
        })

    # ── Main crawl loop ───────────────────────────────────────────────────

    async def crawl(self) -> AppMap:
        logger.info(f"Starting crawl from {self.base_url} (max_depth={self.max_depth})")
        start_time = time.time()
        deadline = start_time + self.timeout_minutes * 60

        queue: List[tuple] = [(self.page.url, 0, None)]  # (url, depth, parent_url)
        app_map = AppMap(base_url=self.base_url)

        while queue and len(self.visited) < self.max_pages and time.time() < deadline:
            url, depth, parent_url = queue.pop(0)

            if depth > self.max_depth:
                continue

            norm_url = self._normalize_url(url)
            if not self._is_same_domain(url):
                continue
            if self._is_excluded(url):
                continue

            # Navigate and analyze
            page_data = await self._visit_page(url, depth, parent_url)
            if page_data is None:
                continue

            page_key = f"{page_data.normalized_url}::{page_data.dom_hash}"
            if page_key in self.visited:
                continue

            self.visited[page_key] = page_data
            app_map.pages[page_key] = page_data
            app_map.total_forms += len(page_data.forms)
            app_map.total_inputs += len(page_data.inputs)
            app_map.total_links += len(page_data.links)

            # Track adjacency
            if parent_url:
                parent_norm = self._normalize_url(parent_url)
                app_map.adjacency.setdefault(parent_norm, []).append(page_data.normalized_url)

            # Track modules
            if page_data.module_hint:
                app_map.modules.setdefault(page_data.module_hint, []).append(page_key)

            # Enqueue discovered links
            for link in page_data.links:
                if depth + 1 <= self.max_depth:
                    queue.append((link, depth + 1, url))

            # SPA route discovery
            if self.spa_cfg.get("enabled", True) and depth + 1 <= self.max_depth:
                spa_links = await self._discover_spa_routes(url)
                for spa_url in spa_links:
                    queue.append((spa_url, depth + 1, url))

            await asyncio.sleep(self.delay)

        # Build error summary
        app_map.errors_summary = {
            "console_errors": len(self.console_errors),
            "network_errors": len(self.network_errors),
        }

        logger.info(
            f"Crawl complete: {len(self.visited)} pages in "
            f"{time.time() - start_time:.1f}s"
        )
        return app_map

    # ── Page visit ────────────────────────────────────────────────────────

    async def _visit_page(
        self, url: str, depth: int, parent_url: Optional[str]
    ) -> Optional[DiscoveredPage]:
        try:
            timeout = self.config.get("page_load_timeout", 15000)
            await self.page.goto(url, timeout=timeout)
            await _wait_for_page_ready(self.page, timeout=timeout)
        except Exception as e:
            logger.warning(f"Failed to load {url}: {e}")
            return None

        try:
            # Scroll to bottom to trigger lazy-loaded content
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(0.5)

            html = await self.page.content()
            title = await self.page.title()
            soup = BeautifulSoup(html, "html.parser")

            # DOM hash for dedup
            dom_hash = self._compute_dom_hash(html)
            norm_url = self._normalize_url(url)

            # Check if already visited (with this content)
            page_key = f"{norm_url}::{dom_hash}"
            if page_key in self.visited:
                return None

            # Extract page structure using PageAnalyzer helpers
            from orchestrator.page_analyzer import PageAnalyzer
            analyzer = PageAnalyzer.__new__(PageAnalyzer)

            elements = await self._extract_elements()
            structure = analyzer._analyze_html_structure(soup)
            page_type = analyzer._identify_page_type(soup)

            # Classify elements
            forms = structure.get("forms", [])
            inputs = [e for e in elements if e.get("type") == "inputs"]
            buttons = [e for e in elements if e.get("type") == "buttons"]
            outputs = self._extract_outputs(soup)
            links = self._extract_links(html, url)

            # Module detection
            module_hint = self._detect_module(soup, title)

            # Apply module filter
            if self.module_filter and not self._passes_module_filter(module_hint, title, soup):
                logger.debug(f"Skipping {url} — does not match module filter")
                # Still follow links one level to find module entry points
                if depth >= 1:
                    return None

            # Screenshot
            screenshot_name = ""
            try:
                idx = len(self.visited)
                safe_title = "".join(c if c.isalnum() else "_" for c in title[:30])
                screenshot_name = f"page_{idx}_{safe_title}.png"
                screenshot_data = await self.page.screenshot()
                self.sink.save_screenshot(screenshot_data, screenshot_name)
            except Exception as e:
                logger.warning(f"Failed to capture screenshot for {url}: {e}")

            # Collect current errors for this page
            page_console_errors = [e for e in self.console_errors if e["url"] == url]
            page_network_errors = [e for e in self.network_errors if e.get("page_url") == url]

            self.sink.log_event("page_discovered", {
                "url": url, "title": title, "page_type": page_type,
                "forms": len(forms), "inputs": len(inputs),
                "links": len(links), "depth": depth,
            })

            return DiscoveredPage(
                url=url,
                normalized_url=norm_url,
                title=title,
                page_type=page_type,
                dom_hash=dom_hash,
                forms=forms,
                inputs=inputs,
                outputs=outputs,
                links=links,
                buttons=buttons,
                screenshot_path=screenshot_name,
                console_errors=page_console_errors,
                network_errors=page_network_errors,
                discovery_method="link",
                parent_url=parent_url,
                depth=depth,
                module_hint=module_hint,
            )

        except Exception as e:
            logger.error(f"Error analyzing {url}: {e}")
            return None

    # ── Element extraction (on current page) ──────────────────────────────

    async def _extract_elements(self) -> List[Dict[str, Any]]:
        """Extract interactive elements from the current page."""
        elements = []
        selectors = {
            "inputs": "input, textarea, select",
            "buttons": "button, input[type='submit'], input[type='button']",
            "links": "a[href]",
        }
        for etype, selector in selectors.items():
            try:
                page_els = await self.page.query_selector_all(selector)
                for el in page_els[:50]:  # Cap per type to avoid huge pages
                    try:
                        info = {
                            "type": etype,
                            "tag": await el.evaluate("e => e.tagName.toLowerCase()"),
                            "id": await el.evaluate("e => e.id || ''"),
                            "name": await el.evaluate("e => e.name || ''"),
                            "text": (await el.evaluate("e => (e.textContent||'').trim()"))[:100],
                            "input_type": await el.evaluate("e => e.type || ''"),
                            "placeholder": await el.evaluate("e => e.placeholder || ''"),
                            "visible": await el.is_visible(),
                            "enabled": await el.is_enabled(),
                        }
                        elements.append(info)
                    except Exception:
                        continue
            except Exception:
                continue
        return elements

    def _extract_links(self, html: str, current_url: str) -> List[str]:
        """Extract and resolve all same-domain links from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        links = []
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or self._is_excluded(href):
                continue
            resolved = urljoin(current_url, href)
            if not self._is_same_domain(resolved):
                continue
            norm = self._normalize_url(resolved)
            if norm not in seen:
                seen.add(norm)
                links.append(resolved)
        return links

    def _extract_outputs(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Identify output/display areas: tables, alerts, result containers."""
        outputs = []
        for table in soup.find_all("table"):
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            outputs.append({"type": "table", "headers": headers[:20]})

        for alert in soup.find_all(class_=lambda c: c and any(
            kw in str(c).lower() for kw in ["alert", "message", "notification", "toast"]
        )):
            outputs.append({"type": "alert", "text": alert.get_text(strip=True)[:200]})

        return outputs

    # ── SPA route discovery ───────────────────────────────────────────────

    async def _discover_spa_routes(self, current_url: str) -> List[str]:
        """Click nav elements to discover SPA routes that don't change the URL."""
        discovered = []
        max_clicks = self.spa_cfg.get("max_clicks_per_page", 20)
        wait_ms = self.spa_cfg.get("click_wait_ms", 2000)

        current_html = await self.page.content()
        current_hash = self._compute_dom_hash(current_html)

        nav_elements = []
        for sel in self.nav_selectors:
            try:
                els = await self.page.query_selector_all(sel)
                nav_elements.extend(els)
            except Exception:
                continue

        clicked = 0
        for el in nav_elements[:max_clicks]:
            try:
                if not await el.is_visible():
                    continue
                text = await el.evaluate("e => (e.textContent||'').trim()")
                href = await el.evaluate("e => e.href || ''")

                # Skip if it's a regular link we'll already follow
                if href and self._is_same_domain(href):
                    continue

                await el.click()
                await asyncio.sleep(wait_ms / 1000.0)

                new_html = await self.page.content()
                new_hash = self._compute_dom_hash(new_html)
                new_url = self.page.url

                if new_hash != current_hash:
                    # New content discovered
                    spa_id = f"{new_url}#spa_{text[:20]}"
                    discovered.append(new_url)
                    logger.debug(f"SPA route discovered via click on '{text[:30]}'")

                # Navigate back to restore state
                await self.page.goto(current_url)
                await _wait_for_page_ready(self.page)
                clicked += 1

            except Exception as e:
                logger.debug(f"SPA click failed: {e}")
                try:
                    await self.page.goto(current_url)
                    await _wait_for_page_ready(self.page)
                except Exception:
                    pass

        return discovered

    # ── Helpers ────────────────────────────────────────────────────────────

    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        # Sort query params, strip fragment
        params = parse_qs(parsed.query)
        sorted_query = urlencode(sorted(params.items()), doseq=True)
        return urlunparse((
            parsed.scheme, parsed.netloc, parsed.path.rstrip("/"),
            parsed.params, sorted_query, "",
        ))

    def _is_same_domain(self, url: str) -> bool:
        try:
            return urlparse(url).hostname == self.base_domain
        except Exception:
            return False

    def _is_excluded(self, url: str) -> bool:
        url_lower = url.lower()
        return any(pat.lower() in url_lower for pat in self.exclude_patterns)

    def _compute_dom_hash(self, html: str) -> str:
        # Lightweight structural hash — strip whitespace-heavy text
        soup = BeautifulSoup(html, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        structure = []
        for tag in soup.find_all(True, recursive=True)[:200]:
            structure.append(f"{tag.name}#{tag.get('id', '')}:{','.join(tag.get('class', []))}")
        return hashlib.md5("|".join(structure).encode()).hexdigest()[:12]

    def _detect_module(self, soup: BeautifulSoup, title: str) -> str:
        """Try to identify which application module this page belongs to."""
        sources = []
        sources.append(title)
        for tag in ["h1", "h2"]:
            el = soup.find(tag)
            if el:
                sources.append(el.get_text(strip=True))
        for sel in [".breadcrumb", "nav[aria-label='breadcrumb']"]:
            el = soup.select_one(sel)
            if el:
                sources.append(el.get_text(strip=True))
        combined = " | ".join(sources).strip()
        return combined[:100] if combined else ""

    def _passes_module_filter(self, module_hint: str, title: str, soup: BeautifulSoup) -> bool:
        if not self.module_filter:
            return True
        searchable = f"{module_hint} {title}".lower()
        h1 = soup.find("h1")
        if h1:
            searchable += " " + h1.get_text(strip=True).lower()
        return any(mod in searchable for mod in self.module_filter)


# ── Report Generator ──────────────────────────────────────────────────────────

class ReportGenerator:
    """Produces exploration report artifacts."""

    def __init__(self, sink, artifacts_dir: str):
        self.sink = sink
        self.artifacts_dir = Path(artifacts_dir)

    def generate(self, result: ExplorationResult) -> str:
        # 1. app_map.json
        app_map_data = {
            "base_url": result.app_map.base_url,
            "pages_discovered": len(result.app_map.pages),
            "total_forms": result.app_map.total_forms,
            "total_inputs": result.app_map.total_inputs,
            "total_links": result.app_map.total_links,
            "modules": result.app_map.modules,
            "errors_summary": result.app_map.errors_summary,
            "pages": {
                key: {
                    "url": p.url,
                    "title": p.title,
                    "page_type": p.page_type,
                    "module": p.module_hint,
                    "forms": p.forms,
                    "inputs": [{"name": i.get("name"), "type": i.get("input_type"),
                                "placeholder": i.get("placeholder")} for i in p.inputs],
                    "outputs": p.outputs,
                    "buttons": [{"text": b.get("text", ""), "id": b.get("id", "")}
                                for b in p.buttons],
                    "links_count": len(p.links),
                    "console_errors": len(p.console_errors),
                    "network_errors": len(p.network_errors),
                    "screenshot": p.screenshot_path,
                    "depth": p.depth,
                }
                for key, p in result.app_map.pages.items()
            },
            "adjacency": result.app_map.adjacency,
        }
        self._write_json("app_map.json", app_map_data)

        # 2. exploration_report.json
        report_data = {
            "run_id": result.run_id,
            "summary": {
                "pages_discovered": result.pages_discovered,
                "tests_executed": result.tests_executed,
                "tests_passed": result.tests_passed,
                "tests_failed": result.tests_failed,
                "console_errors": len(result.console_errors),
                "network_errors": len(result.network_errors),
                "duration_seconds": round(result.duration_seconds, 2),
            },
            "test_results": result.test_results,
            "console_errors": result.console_errors[:500],
            "network_errors": result.network_errors[:500],
            "input_output_mapping": {
                p.url: {
                    "inputs": [{"name": i.get("name"), "type": i.get("input_type"),
                                "placeholder": i.get("placeholder")} for i in p.inputs],
                    "outputs": p.outputs,
                    "forms": p.forms,
                }
                for p in result.app_map.pages.values()
                if p.inputs or p.forms or p.outputs
            },
        }
        self._write_json("exploration_report.json", report_data)

        # 3. run.json (consistent with existing convention)
        # Determine status: failed if any tests failed OR if no tests ran
        # (e.g. auth failure, crawl crash) OR if errors were found during crawl
        if result.tests_failed > 0:
            status = "failed"
        elif result.tests_executed > 0 and result.tests_failed == 0:
            status = "passed"
        elif result.pages_discovered == 0:
            status = "failed"  # Nothing was discovered — something went wrong
        else:
            status = "incomplete"  # Pages found but no tests ran (crawl-only or error)

        self._write_json("run.json", {
            "run_id": result.run_id,
            "status": status,
            "pages_discovered": result.pages_discovered,
            "tests_executed": result.tests_executed,
            "tests_passed": result.tests_passed,
            "tests_failed": result.tests_failed,
            "console_errors": len(result.console_errors),
            "network_errors": len(result.network_errors),
            "duration_seconds": round(result.duration_seconds, 2),
        })

        # 4. Save test plans (sanitize names for filesystem safety)
        plans_dir = self.artifacts_dir / "test_plans"
        plans_dir.mkdir(exist_ok=True)
        for i, plan in enumerate(result.test_plans):
            raw_name = plan.get("name", "unnamed")
            safe_name = self._sanitize_filename(raw_name)
            self._write_json(f"test_plans/plan_{i}_{safe_name}.json", plan)

        logger.info(f"Reports saved to {self.artifacts_dir}")
        return str(self.artifacts_dir / "exploration_report.json")

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Remove characters unsafe for Windows/Linux filenames."""
        import re
        safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name)
        safe = re.sub(r'[\s_]+', '_', safe).strip('_. ')
        return safe[:40] if safe else "unnamed"

    def _write_json(self, filename: str, data: Any):
        path = self.artifacts_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)


# ── Exploration Orchestrator ──────────────────────────────────────────────────

class ExplorationOrchestrator:
    """Top-level coordinator: authenticate → crawl → generate tests → execute → report."""

    def __init__(self, artifacts_dir: str, headful: bool, run_id: str,
                 control_room=None):
        self.artifacts_dir = artifacts_dir
        self.headful = headful
        self.run_id = run_id
        self.cr = control_room
        self.config = _load_explorer_config()

    async def explore(
        self,
        base_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        cookie_name: Optional[str] = None,
        cookie_value: Optional[str] = None,
        login_url: Optional[str] = None,
        max_depth: int = 5,
        module_filter: Optional[List[str]] = None,
        generate_tests: bool = True,
        execute_tests: bool = True,
    ) -> ExplorationResult:

        started_at = time.time()
        self.config["max_depth"] = max_depth

        # ── Phase 1: Setup ────────────────────────────────────────────────
        from browser.context import create_context, finalize_video_and_trace
        from evidence.sink import EvidenceSink

        playwright_instance, browser, context, page, _, _ = await create_context(
            headful=self.headful,
            artifacts_dir=self.artifacts_dir,
        )
        sink = EvidenceSink(self.artifacts_dir)
        sink.log_event("exploration_started", {
            "base_url": base_url, "max_depth": max_depth,
            "module_filter": module_filter,
        })

        result = ExplorationResult(run_id=self.run_id, app_map=AppMap(base_url=base_url))

        try:
            # ── Phase 2: Authentication ───────────────────────────────────
            auth = Authenticator(page, context, self.config)

            if username and password:
                target = login_url or base_url
                success = await auth.login_with_credentials(target, username, password)
                if not success:
                    sink.log_event("auth_failed", {"method": "credentials"})
                    raise RuntimeError("Login failed — check credentials and login URL")

            elif cookie_name and cookie_value:
                success = await auth.login_with_cookie(base_url, cookie_name, cookie_value)
                if not success:
                    sink.log_event("auth_failed", {"method": "cookie"})
                    raise RuntimeError("Cookie authentication failed — session may be expired")
            else:
                # No auth — just navigate to the URL
                await page.goto(base_url)
                await _wait_for_page_ready(page)

            sink.log_event("auth_success", {"url": page.url})
            if self.cr:
                await self.cr.send_status(self.run_id, "running", "Authentication successful, starting crawl")

            # ── Phase 3: Crawl ────────────────────────────────────────────
            crawler = Crawler(
                page=page, context=context, sink=sink,
                base_url=base_url, config=self.config,
                module_filter=module_filter,
            )
            app_map = await crawler.crawl()
            result.app_map = app_map
            result.pages_discovered = len(app_map.pages)
            result.console_errors = crawler.console_errors
            result.network_errors = crawler.network_errors

            sink.log_event("crawl_complete", {
                "pages": len(app_map.pages),
                "forms": app_map.total_forms,
                "errors": len(crawler.console_errors) + len(crawler.network_errors),
            })

            if self.cr:
                await self.cr.send_status(
                    self.run_id, "running",
                    f"Crawl complete: {len(app_map.pages)} pages discovered"
                )

            # ── Phase 4: AI Test Generation ───────────────────────────────
            if generate_tests and app_map.pages:
                result.test_plans = await self._generate_tests(app_map, sink)
                sink.log_event("tests_generated", {"count": len(result.test_plans)})

            # ── Phase 5: Test Execution ───────────────────────────────────
            if execute_tests and result.test_plans:
                from orchestrator.executor import Executor
                executor = Executor(page, context, sink, self.cr, self.run_id)

                for plan in result.test_plans:
                    plan_result = await self._execute_plan(executor, plan, base_url, sink)
                    result.test_results.append(plan_result)
                    if plan_result.get("status") == "passed":
                        result.tests_passed += 1
                    else:
                        result.tests_failed += 1
                    result.tests_executed += 1

                if self.cr:
                    await self.cr.send_status(
                        self.run_id, "running",
                        f"Tests complete: {result.tests_passed}/{result.tests_executed} passed"
                    )

            # ── Phase 6: Report ───────────────────────────────────────────
            result.duration_seconds = time.time() - started_at
            report = ReportGenerator(sink, self.artifacts_dir)
            report.generate(result)

            sink.log_event("exploration_complete", {
                "pages": result.pages_discovered,
                "tests_passed": result.tests_passed,
                "tests_failed": result.tests_failed,
            })
            sink.save_logs()

            if self.cr:
                status = "passed" if result.tests_failed == 0 else "failed"
                await self.cr.send_status(self.run_id, status, "Exploration complete")

            return result

        except Exception as e:
            logger.error(f"Exploration failed: {e}")
            sink.log_event("exploration_failed", {"error": str(e)})
            sink.save_logs()
            result.duration_seconds = time.time() - started_at
            # Still generate partial report
            try:
                report = ReportGenerator(sink, self.artifacts_dir)
                report.generate(result)
            except Exception:
                pass
            raise

        finally:
            try:
                if context:
                    await finalize_video_and_trace(context, self.artifacts_dir)
                if browser:
                    await browser.close()
                if playwright_instance:
                    await playwright_instance.stop()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    # ── AI test generation ────────────────────────────────────────────────

    async def _generate_tests(
        self, app_map: AppMap, sink
    ) -> List[Dict[str, Any]]:
        from providers.openai_provider import OpenAIProvider

        provider = OpenAIProvider()
        if not provider.is_available():
            logger.warning("OpenAI not available — skipping AI test generation")
            return self._generate_fallback_tests(app_map)

        plans = []
        for key, page in app_map.pages.items():
            if not page.forms and not page.inputs and not page.buttons:
                continue  # Skip pages with nothing to test

            try:
                plan = await self._generate_page_test(provider, page)
                if plan:
                    plans.append(plan)
            except Exception as e:
                logger.warning(f"Failed to generate test for {page.url}: {e}")

        return plans

    async def _generate_page_test(
        self, provider, page: DiscoveredPage
    ) -> Optional[Dict[str, Any]]:
        prompt = f"""Analyze this web application page and generate a practical test plan.

Page URL: {page.url}
Page Title: {page.title}
Page Type: {page.page_type}
Module: {page.module_hint}

Forms found: {json.dumps(page.forms[:5], indent=2)}

Input fields: {json.dumps([{{"name": i.get("name"), "type": i.get("input_type"), "placeholder": i.get("placeholder")}} for i in page.inputs[:15]], indent=2)}

Buttons: {json.dumps([{{"text": b.get("text"), "id": b.get("id")}} for b in page.buttons[:10]], indent=2)}

Generate a test plan with steps that:
1. Navigate to this page
2. Fill all form fields with realistic test data
3. Submit the form
4. Verify success (look for success messages, URL changes, new data appearing)
5. Test at least one invalid input scenario

Return JSON with this structure:
{{
  "name": "Test plan name",
  "description": "What this tests",
  "page_url": "{page.url}",
  "steps": [
    {{
      "title": "Step description",
      "action": "navigate|fill|click|submit|wait|verify",
      "target": "CSS selector or URL",
      "data": {{"value": "test data"}},
      "verification": {{"text": "expected text"}}
    }}
  ]
}}"""

        messages = [
            {"role": "system", "content": "You are a QA engineer. Generate practical, executable test steps. Return valid JSON."},
            {"role": "user", "content": prompt},
        ]

        response = await provider.generate_completion_async(
            messages=messages, json_mode=True, temperature=0.1
        )

        if response.success and response.json_data:
            return response.json_data
        return None

    def _generate_fallback_tests(self, app_map: AppMap) -> List[Dict[str, Any]]:
        """Basic test generation without AI — just navigate and verify."""
        plans = []
        for key, page in app_map.pages.items():
            steps = [
                {"title": f"Navigate to {page.title}", "action": "navigate", "target": page.url},
                {"title": f"Verify {page.title} loaded", "action": "verify",
                 "verification": {"text": page.title[:30]}},
            ]
            # Fill any forms found
            for form_input in page.inputs[:5]:
                if form_input.get("name") and form_input.get("visible"):
                    selector = f"[name='{form_input['name']}']"
                    steps.append({
                        "title": f"Fill {form_input['name']}",
                        "action": "fill",
                        "target": selector,
                        "data": {"value": "test_value"},
                    })

            plans.append({
                "name": f"Basic test for {page.title}",
                "description": f"Auto-generated navigation and form test for {page.url}",
                "page_url": page.url,
                "steps": steps,
            })
        return plans

    # ── Test execution ────────────────────────────────────────────────────

    async def _execute_plan(
        self, executor, plan: Dict[str, Any], base_url: str, sink
    ) -> Dict[str, Any]:
        plan_name = plan.get("name", "Unnamed")
        steps = plan.get("steps", [])
        step_results = []
        status = "passed"

        sink.log_event("test_plan_started", {"name": plan_name, "steps": len(steps)})

        for idx, step in enumerate(steps):
            try:
                await executor.run_step(idx, step, base_url)
                step_results.append({"step": idx, "title": step.get("title"), "status": "passed"})
            except Exception as e:
                step_results.append({
                    "step": idx, "title": step.get("title"),
                    "status": "failed", "error": str(e),
                })
                status = "failed"
                # Continue with remaining steps instead of aborting
                continue

        sink.log_event("test_plan_completed", {"name": plan_name, "status": status})

        return {
            "plan_name": plan_name,
            "page_url": plan.get("page_url", ""),
            "status": status,
            "steps": step_results,
            "total_steps": len(steps),
            "passed_steps": sum(1 for s in step_results if s["status"] == "passed"),
            "failed_steps": sum(1 for s in step_results if s["status"] == "failed"),
        }
