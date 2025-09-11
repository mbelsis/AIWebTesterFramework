import asyncio
import json
import re
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import os
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class PageAnalyzer:
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None

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
        
        if not self.openai_client:
            raise ValueError("OpenAI API key not provided. Cannot generate test plan.")
        
        # Prepare data for AI
        ai_prompt = self._create_ai_prompt(page_analysis, test_description)
        
        try:
            # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
            # do not change this unless explicitly requested by the user
            response = self.openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert QA engineer who creates comprehensive test plans. Generate detailed, practical test steps based on the provided web page analysis. Return valid YAML format."
                    },
                    {
                        "role": "user", 
                        "content": ai_prompt
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Error generating test plan with AI: {e}")
            # Fallback to rule-based generation
            return self._generate_fallback_test_plan(page_analysis)

    def _create_ai_prompt(self, page_analysis: Dict[str, Any], test_description: str) -> str:
        """Create a detailed prompt for AI test plan generation"""
        
        elements_summary = []
        for element in page_analysis["elements"]:
            if element["visible"] and element["enabled"]:
                elements_summary.append({
                    "type": element["type"],
                    "selector": element["selector"],
                    "text": element["text"],
                    "input_type": element.get("input_type", ""),
                    "placeholder": element.get("placeholder", "")
                })
        
        prompt = f"""
Analyze this web page and generate a comprehensive test plan:

URL: {page_analysis["url"]}
Page Title: {page_analysis["title"]}
Page Type: {page_analysis["structure"]["page_type"]}

Interactive Elements Found:
{json.dumps(elements_summary[:20], indent=2)}

Forms on Page:
{json.dumps(page_analysis["structure"]["forms"], indent=2)}

Test Description/Requirements: {test_description or "Create comprehensive tests covering all major functionality"}

Please generate a detailed test plan that:
1. Tests all critical user flows on this page
2. Validates form submissions and input validation
3. Tests navigation and interactive elements
4. Includes appropriate verification steps
5. Uses realistic test data

Return the response as JSON with this structure:
{{
  "name": "Test Plan Name",
  "description": "Test plan description",
  "steps": [
    {{
      "title": "Step description",
      "action": "navigate|fill|click|submit|wait|verify",
      "target": "CSS selector",
      "data": {{"value": "test data"}},
      "verification": {{"text": "expected text"}}
    }}
  ]
}}

Focus on practical, executable test steps that cover the main user journey.
"""
        
        return prompt

    def _generate_fallback_test_plan(self, page_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a basic test plan without AI as fallback"""
        
        steps = []
        page_type = page_analysis["structure"]["page_type"]
        
        # Add navigation step
        steps.append({
            "title": f"Navigate to {page_analysis['title']}",
            "action": "navigate",
            "target": page_analysis["url"]
        })
        
        # Generate steps based on page type and elements
        for element in page_analysis["elements"]:
            if not element["visible"] or not element["enabled"]:
                continue
                
            if element["type"] == "inputs" and element["input_type"] == "text":
                steps.append({
                    "title": f"Fill {element['placeholder'] or element['name'] or 'field'}",
                    "action": "fill",
                    "target": element["selector"],
                    "data": {"value": "test_value"}
                })
            elif element["type"] == "buttons" and element["text"]:
                steps.append({
                    "title": f"Click {element['text']}",
                    "action": "click", 
                    "target": element["selector"]
                })
        
        return {
            "name": f"Generated Test for {page_analysis['title']}",
            "description": f"Auto-generated test plan for {page_type} page",
            "steps": steps
        }