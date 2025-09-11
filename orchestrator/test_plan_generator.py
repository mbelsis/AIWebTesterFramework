import asyncio
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
from orchestrator.page_analyzer import PageAnalyzer

class TestPlanGenerator:
    def __init__(self, openai_api_key: Optional[str] = None):
        self.analyzer = PageAnalyzer(openai_api_key)

    async def generate_from_url(
        self, 
        url: str, 
        test_description: str = "",
        output_dir: str = "examples",
        headful: bool = False
    ) -> Dict[str, str]:
        """Generate test plan and environment config from a URL"""
        
        print(f"🔍 Analyzing page: {url}")
        
        # Analyze the page
        page_analysis = await self.analyzer.analyze_page(url, headful=headful)
        
        print(f"📝 Found {len(page_analysis['elements'])} interactive elements")
        print(f"📄 Page type identified as: {page_analysis['structure']['page_type']}")
        
        # Generate test plan using AI
        print("🤖 Generating test plan with AI...")
        test_plan = await self.analyzer.generate_test_plan(page_analysis, test_description)
        
        # Generate environment config
        env_config = self._generate_environment_config(url, page_analysis)
        
        # Save files
        plan_filename, env_filename = await self._save_files(
            test_plan, env_config, output_dir, page_analysis["title"]
        )
        
        return {
            "plan_file": plan_filename,
            "env_file": env_filename,
            "page_type": page_analysis["structure"]["page_type"],
            "elements_found": len(page_analysis['elements'])
        }

    def _generate_environment_config(self, url: str, page_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate environment configuration based on page analysis"""
        
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        env_config = {
            "name": f"Generated Environment for {page_analysis['title']}",
            "description": f"Auto-generated environment configuration for {page_analysis['structure']['page_type']} page",
            "target": {
                "base_url": base_url,
                "timeout": 15000
            },
            "credentials": {
                "username": "test_user",
                "password": "test_password",
                "email": "test@example.com"
            },
            "settings": {
                "headful": True,
                "slow_mo": 500,
                "video": True,
                "screenshots": True
            }
        }
        
        # Add page-specific configurations
        page_type = page_analysis["structure"]["page_type"]
        
        if page_type == "login":
            env_config["test_data"] = {
                "valid_credentials": {
                    "username": "valid_user",
                    "password": "valid_password"
                },
                "invalid_credentials": {
                    "username": "invalid_user",
                    "password": "wrong_password"
                }
            }
        elif page_type == "registration":
            env_config["test_data"] = {
                "user_data": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe.test@example.com",
                    "password": "SecurePass123!",
                    "phone": "555-0123"
                }
            }
        elif page_type == "checkout":
            env_config["test_data"] = {
                "payment_info": {
                    "card_number": "4111111111111111",
                    "expiry": "12/25",
                    "cvv": "123",
                    "name": "John Doe"
                },
                "shipping_address": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "zip": "12345"
                }
            }
        
        return env_config

    async def _save_files(
        self, 
        test_plan: Dict[str, Any], 
        env_config: Dict[str, Any], 
        output_dir: str,
        page_title: str
    ) -> tuple[str, str]:
        """Save test plan and environment configuration to files"""
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filenames
        safe_title = self._sanitize_filename(page_title)
        plan_filename = output_path / f"plan.generated_{safe_title}.yaml"
        env_filename = output_path / f"env.generated_{safe_title}.yaml"
        
        # Save test plan
        with open(plan_filename, 'w') as f:
            yaml.dump(test_plan, f, default_flow_style=False, allow_unicode=True)
        
        # Save environment config
        with open(env_filename, 'w') as f:
            yaml.dump(env_config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"💾 Saved test plan: {plan_filename}")
        print(f"💾 Saved environment: {env_filename}")
        
        return str(plan_filename), str(env_filename)

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem safety"""
        import re
        # Remove or replace problematic characters
        safe = re.sub(r'[^\w\s-]', '', filename)
        safe = re.sub(r'[\s_]+', '_', safe)
        return safe.lower()[:50]  # Limit length

    async def interactive_generate(self, url: str) -> Dict[str, str]:
        """Interactive test plan generation with user prompts"""
        
        print(f"\n🚀 AI WebTester - Intelligent Test Plan Generator")
        print(f"📍 Target URL: {url}")
        print(f"" + "="*60)
        
        # Get user requirements
        print("\n📋 Test Requirements:")
        test_description = input("Describe what you want to test (or press Enter for auto-detection): ").strip()
        
        print("\n⚙️  Generation Settings:")
        headful_input = input("Show browser during analysis? (y/N): ").strip().lower()
        headful = headful_input in ['y', 'yes']
        
        output_dir = input("Output directory (default: examples): ").strip() or "examples"
        
        # Generate test plan
        result = await self.generate_from_url(
            url=url,
            test_description=test_description,
            output_dir=output_dir,
            headful=headful
        )
        
        print(f"\n✅ Test Plan Generation Complete!")
        print(f"📊 Page Type: {result['page_type']}")
        print(f"🎯 Elements Analyzed: {result['elements_found']}")
        print(f"📄 Plan File: {result['plan_file']}")
        print(f"🔧 Environment File: {result['env_file']}")
        
        print(f"\n🏃 Ready to run your test:")
        print(f"python -m cli.main run --plan {result['plan_file']} --env {result['env_file']} --control-room")
        
        return result

    def show_page_analysis(self, page_analysis: Dict[str, Any]):
        """Display detailed page analysis for user review"""
        
        print(f"\n📄 Page Analysis Results:")
        print(f"Title: {page_analysis['title']}")
        print(f"URL: {page_analysis['url']}")
        print(f"Type: {page_analysis['structure']['page_type']}")
        
        print(f"\n🎯 Interactive Elements Found:")
        element_types = {}
        for element in page_analysis['elements']:
            if element['visible'] and element['enabled']:
                elem_type = element['type']
                element_types[elem_type] = element_types.get(elem_type, 0) + 1
        
        for elem_type, count in element_types.items():
            print(f"  - {elem_type}: {count}")
        
        print(f"\n📝 Forms Detected:")
        for i, form in enumerate(page_analysis['structure']['forms']):
            print(f"  Form {i+1}: {len(form['fields'])} fields, method: {form['method']}")
        
        return element_types