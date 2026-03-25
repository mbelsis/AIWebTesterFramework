import asyncio
import json
import re
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import os
from providers.openai_provider import OpenAIProvider

class PageAnalyzer:
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_provider = OpenAIProvider(api_key=openai_api_key)

    async def analyze_page(self, url: str, headful: bool = False) -> Dict[str, Any]:
        """Analyze a web page and extract interactive elements and structure"""
        
        # Launch browser and get page content
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=not headful)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await page.goto(url)
            await page.wait_for_load_state("domcontentloaded")
            try:
                await page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass  # Page is interactive; networkidle timeout is acceptable
            
            # Get page content
            html_content = await page.content()
            page_title = await page.title()
            current_url = page.url
            
            # Take screenshot for AI analysis
            screenshot = await page.screenshot()
            
            # Extract interactive elements
            elements = await self._extract_interactive_elements(page)
            
            # Parse HTML with BeautifulSoup for detailed analysis
            soup = BeautifulSoup(html_content, 'html.parser')
            page_structure = self._analyze_html_structure(soup)
            
            analysis_result = {
                "url": current_url,
                "title": page_title,
                "structure": page_structure,
                "elements": elements,
                "screenshot": screenshot,
                "html_content": html_content[:50000]  # Truncate for AI processing
            }
            
            return analysis_result
            
        finally:
            await context.close()
            await browser.close()
            await playwright.stop()

    async def _extract_interactive_elements(self, page) -> List[Dict[str, Any]]:
        """Extract all interactive elements from the page"""
        
        elements = []
        
        # Define selectors for different element types
        selectors = {
            "forms": "form",
            "inputs": "input, textarea, select",
            "buttons": "button, input[type='submit'], input[type='button']",
            "links": "a[href]",
            "clickable": "[onclick], [role='button'], .btn, .button"
        }
        
        for element_type, selector in selectors.items():
            try:
                page_elements = await page.query_selector_all(selector)
                
                for element in page_elements:
                    element_info = await self._get_element_info(element, element_type)
                    if element_info:
                        elements.append(element_info)
                        
            except Exception as e:
                print(f"Error extracting {element_type}: {e}")
                
        return elements

    async def _get_element_info(self, element, element_type: str) -> Optional[Dict[str, Any]]:
        """Extract detailed information about a single element"""
        
        try:
            # Get element attributes
            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
            element_id = await element.evaluate("el => el.id || ''")
            element_class = await element.evaluate("el => el.className || ''")
            element_text = await element.evaluate("el => el.textContent?.trim() || ''")
            element_value = await element.evaluate("el => el.value || ''")
            placeholder = await element.evaluate("el => el.placeholder || ''")
            element_type_attr = await element.evaluate("el => el.type || ''")
            name_attr = await element.evaluate("el => el.name || ''")
            href = await element.evaluate("el => el.href || ''")
            
            # Generate selector
            selector = await self._generate_selector(element)
            
            # Check if element is visible
            is_visible = await element.is_visible()
            is_enabled = await element.is_enabled()
            
            return {
                "type": element_type,
                "tag": tag_name,
                "selector": selector,
                "id": element_id,
                "class": element_class,
                "text": element_text[:200],  # Truncate long text
                "value": element_value,
                "placeholder": placeholder,
                "input_type": element_type_attr,
                "name": name_attr,
                "href": href,
                "visible": is_visible,
                "enabled": is_enabled
            }
            
        except Exception as e:
            print(f"Error getting element info: {e}")
            return None

    def _escape_css_attr(self, value: str) -> str:
        """Escape a value for use inside CSS attribute selectors like [name='...']."""
        # Replace backslashes first, then single quotes
        return value.replace("\\", "\\\\").replace("'", "\\'")

    def _is_valid_css_id(self, value: str) -> bool:
        """Check if a value is safe to use as a #id CSS selector."""
        if not value:
            return False
        # CSS IDs must not start with a digit and must not contain spaces or special chars
        return bool(re.match(r'^[A-Za-z_-][A-Za-z0-9_-]*$', value))

    def _is_valid_css_class(self, value: str) -> bool:
        """Check if a value is safe to use as a .class CSS selector."""
        return bool(re.match(r'^[A-Za-z_-][A-Za-z0-9_-]*$', value))

    async def _generate_selector(self, element) -> str:
        """Generate a reliable CSS selector for the element"""

        selectors = []
        tag_name = await element.evaluate("el => el.tagName.toLowerCase()")

        # Try ID first (only if it's a valid CSS identifier)
        element_id = await element.evaluate("el => el.id")
        if element_id and self._is_valid_css_id(element_id):
            selectors.append(f"#{element_id}")

        # Try name attribute (escaped for safety)
        name_attr = await element.evaluate("el => el.name")
        if name_attr:
            selectors.append(f"[name='{self._escape_css_attr(name_attr)}']")

        # Try data-testid (escaped for safety)
        data_testid = await element.evaluate("el => el.getAttribute('data-testid')")
        if data_testid:
            selectors.append(f"[data-testid='{self._escape_css_attr(data_testid)}']")

        # Try class-based selector (only if it's a clean, unique-looking class)
        class_name = await element.evaluate("el => el.className")
        if class_name and isinstance(class_name, str):
            if not any(word in class_name.lower() for word in ['random', 'generated', 'hash']):
                main_class = class_name.split()[0] if class_name.split() else ""
                if main_class and self._is_valid_css_class(main_class):
                    selectors.append(f".{main_class}")

        # Try text-based selector for buttons/links (escape quotes in text)
        text_content = await element.evaluate("el => el.textContent?.trim()")
        if text_content and len(text_content) < 50 and tag_name in ['button', 'a', 'span']:
            safe_text = text_content.replace("'", "\\'")
            selectors.append(f"{tag_name}:has-text('{safe_text}')")

        return selectors[0] if selectors else tag_name

    def _analyze_html_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze the overall structure of the HTML page"""
        
        structure = {
            "forms": [],
            "navigation": [],
            "content_sections": [],
            "page_type": "unknown"
        }
        
        # Analyze forms
        forms = soup.find_all('form')
        for form in forms:
            form_info = {
                "action": form.get('action', ''),
                "method": form.get('method', 'get'),
                "fields": []
            }
            
            # Find form fields
            fields = form.find_all(['input', 'textarea', 'select'])
            for field in fields:
                field_info = {
                    "tag": field.name,
                    "type": field.get('type', ''),
                    "name": field.get('name', ''),
                    "id": field.get('id', ''),
                    "placeholder": field.get('placeholder', ''),
                    "required": field.has_attr('required')
                }
                form_info["fields"].append(field_info)
            
            structure["forms"].append(form_info)
        
        # Identify page type based on content
        page_type = self._identify_page_type(soup)
        structure["page_type"] = page_type
        
        return structure

    def _identify_page_type(self, soup: BeautifulSoup) -> str:
        """Identify the type of page (login, registration, dashboard, etc.)"""
        
        page_text = soup.get_text().lower()
        title = soup.title.string.lower() if soup.title and soup.title.string else ""
        
        # Check for common page types
        if any(word in page_text or word in title for word in ['login', 'sign in', 'authenticate']):
            return "login"
        elif any(word in page_text or word in title for word in ['register', 'sign up', 'create account']):
            return "registration"
        elif any(word in page_text or word in title for word in ['dashboard', 'overview', 'home']):
            return "dashboard"
        elif any(word in page_text or word in title for word in ['checkout', 'payment', 'order']):
            return "checkout"
        elif any(word in page_text or word in title for word in ['cart', 'shopping']):
            return "shopping_cart"
        elif any(word in page_text or word in title for word in ['profile', 'account', 'settings']):
            return "profile"
        elif any(word in page_text or word in title for word in ['contact', 'contact us', 'get in touch']):
            return "contact"
        elif any(word in page_text or word in title for word in ['search', 'results']):
            return "search"
        else:
            return "content"

    async def generate_test_plan(self, page_analysis: Dict[str, Any], test_description: str = "") -> Dict[str, Any]:
        """Generate a test plan using OpenAI based on page analysis"""
        
        if not self.openai_provider.is_available():
            print("OpenAI API key not provided. Using fallback test generation.")
            return self._generate_fallback_test_plan(page_analysis)
        
        # Use the new provider's async method
        result = await self.openai_provider.generate_test_plan_async(page_analysis, test_description)
        
        # The provider handles fallback internally, so we just return the result
        return result


    def _generate_fallback_test_plan(self, page_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a basic test plan without AI as fallback.

        Handles all common input types: text, email, password, textarea, select,
        number, tel, url, search, date, checkbox, and radio.
        """
        steps = []
        page_type = page_analysis.get("structure", {}).get("page_type", "unknown")

        # Navigation step
        steps.append({
            "title": f"Navigate to {page_analysis.get('title', 'page')}",
            "action": "navigate",
            "target": page_analysis.get("url", "")
        })

        # Mapping of input types to sensible test values
        _fill_values = {
            "text":     "Test Value",
            "email":    "qa-test@example.com",
            "password": "TestPass123!",
            "textarea": "Automated test input",
            "number":   "42",
            "tel":      "555-123-4567",
            "url":      "https://example.com",
            "search":   "search query",
            "date":     "2026-01-15",
        }

        # Fillable input types (includes the tag names textarea/select)
        fillable_types = set(_fill_values.keys()) | {"textarea", "select"}
        submit_candidates = []

        for element in page_analysis.get("elements", []):
            if not element.get("visible", False) or not element.get("enabled", False):
                continue

            etype = element.get("type", "")
            input_type = element.get("input_type", "").lower()
            tag = element.get("tag", "").lower()
            selector = element.get("selector", "")
            field_name = element.get("placeholder") or element.get("name") or element.get("id") or "field"

            if etype == "inputs":
                if tag == "select":
                    # For selects, just click to open (actual option selection needs AI)
                    steps.append({
                        "title": f"Interact with {field_name}",
                        "action": "click",
                        "target": selector,
                    })
                elif input_type in ("checkbox", "radio"):
                    steps.append({
                        "title": f"Toggle {field_name}",
                        "action": "click",
                        "target": selector,
                    })
                elif input_type in fillable_types or tag == "textarea":
                    effective_type = "textarea" if tag == "textarea" else input_type
                    value = _fill_values.get(effective_type, "test_value")
                    steps.append({
                        "title": f"Fill {field_name}",
                        "action": "fill",
                        "target": selector,
                        "data": {"value": value}
                    })

            elif etype == "buttons":
                text = element.get("text", "").strip().lower()
                if text:
                    submit_candidates.append(element)

        # Add a submit step if we found a likely submit button
        for btn in submit_candidates:
            btn_text = btn.get("text", "").strip().lower()
            if any(kw in btn_text for kw in ["submit", "save", "create", "login", "sign in", "register", "send"]):
                steps.append({
                    "title": f"Click {btn.get('text', '').strip()}",
                    "action": "submit",
                    "target": btn.get("selector", ""),
                })
                break
        else:
            # No obvious submit button — click the first button found
            if submit_candidates:
                steps.append({
                    "title": f"Click {submit_candidates[0].get('text', '').strip()}",
                    "action": "click",
                    "target": submit_candidates[0].get("selector", ""),
                })

        return {
            "name": f"Generated Test for {page_analysis.get('title', 'Page')}",
            "description": f"Auto-generated test plan for {page_type} page",
            "steps": steps
        }