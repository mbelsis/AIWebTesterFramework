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
            await page.wait_for_load_state("networkidle")
            
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

    async def _generate_selector(self, element) -> str:
        """Generate a reliable CSS selector for the element"""
        
        # Try different selector strategies
        selectors = []
        
        # Try ID first
        element_id = await element.evaluate("el => el.id")
        if element_id:
            selectors.append(f"#{element_id}")
        
        # Try name attribute
        name_attr = await element.evaluate("el => el.name")
        if name_attr:
            selectors.append(f"[name='{name_attr}']")
        
        # Try data attributes
        data_testid = await element.evaluate("el => el.getAttribute('data-testid')")
        if data_testid:
            selectors.append(f"[data-testid='{data_testid}']")
        
        # Try class-based selector (if classes are meaningful)
        class_name = await element.evaluate("el => el.className")
        if class_name and not any(word in class_name.lower() for word in ['random', 'generated', 'hash']):
            main_class = class_name.split()[0] if class_name.split() else ""
            if main_class:
                selectors.append(f".{main_class}")
        
        # Try text-based selector for buttons/links
        text_content = await element.evaluate("el => el.textContent?.trim()")
        tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
        if text_content and len(text_content) < 50 and tag_name in ['button', 'a', 'span']:
            selectors.append(f"{tag_name}:has-text('{text_content}')")
        
        # Return the first working selector or a generic one
        return selectors[0] if selectors else f"{tag_name}"

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
        title = soup.title.string.lower() if soup.title else ""
        
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
        """Generate a basic test plan without AI as fallback"""
        
        steps = []
        page_type = page_analysis.get("structure", {}).get("page_type", "unknown")
        
        # Add navigation step
        steps.append({
            "title": f"Navigate to {page_analysis.get('title', 'page')}",
            "action": "navigate",
            "target": page_analysis.get("url", "")
        })
        
        # Generate steps based on page type and elements
        for element in page_analysis.get("elements", []):
            if not element.get("visible", False) or not element.get("enabled", False):
                continue
                
            if element.get("type") == "inputs" and element.get("input_type") == "text":
                field_name = element.get("placeholder") or element.get("name") or "field"
                steps.append({
                    "title": f"Fill {field_name}",
                    "action": "fill",
                    "target": element.get("selector", ""),
                    "data": {"value": "test_value"}
                })
            elif element.get("type") == "buttons" and element.get("text"):
                steps.append({
                    "title": f"Click {element.get('text', '')}",
                    "action": "click", 
                    "target": element.get("selector", "")
                })
        
        return {
            "name": f"Generated Test for {page_analysis.get('title', 'Page')}",
            "description": f"Auto-generated test plan for {page_type} page",
            "steps": steps
        }