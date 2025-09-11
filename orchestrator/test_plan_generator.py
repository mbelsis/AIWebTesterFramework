import asyncio
import yaml
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from orchestrator.page_analyzer import PageAnalyzer
from data_gen.faker_util import get_run_specific_faker

class TestPlanGenerator:
    def __init__(self, openai_api_key: Optional[str] = None, run_id: Optional[str] = None):
        self.analyzer = PageAnalyzer(openai_api_key)
        self.run_id = run_id or self._generate_run_id()

    async def generate_from_url(
        self, 
        url: str, 
        test_description: str = "",
        output_dir: str = "examples",
        headful: bool = False
    ) -> Dict[str, Any]:
        """Generate test plan and environment config from a URL"""
        
        print(f"🔍 Analyzing page: {url}")
        
        # Analyze the page
        page_analysis = await self.analyzer.analyze_page(url, headful=headful)
        
        print(f"📝 Found {len(page_analysis['elements'])} interactive elements")
        print(f"📄 Page type identified as: {page_analysis['structure']['page_type']}")
        
        # Generate test plan using AI
        print("🤖 Generating test plan with AI...")
        test_plan = await self.analyzer.generate_test_plan(page_analysis, test_description)
        
        # Generate environment config with seeded data
        env_config = self._generate_environment_config(url, page_analysis)
        
        # Save files
        plan_filename, env_filename = await self._save_files(
            test_plan, env_config, output_dir, page_analysis["title"]
        )
        
        return {
            "plan_file": plan_filename,
            "env_file": env_filename,
            "page_type": page_analysis.get("structure", {}).get("page_type", "unknown"),
            "elements_found": len(page_analysis.get('elements', []))
        }

    def _generate_environment_config(self, url: str, page_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate environment configuration with seeded Faker data"""
        
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Get seeded faker instance for consistent data generation
        faker = get_run_specific_faker(self.run_id)
        user_profile = faker.user_profile()
        
        env_config = {
            "name": f"Generated Environment for {page_analysis['title']}",
            "description": f"Auto-generated environment configuration for {page_analysis['structure']['page_type']} page",
            "run_id": self.run_id,
            "target": {
                "base_url": base_url,
                "timeout": 15000
            },
            "credentials": {
                "username": user_profile['username'],
                "password": "TestPass123!",
                "email": user_profile['email']
            },
            "settings": {
                "headful": True,
                "slow_mo": 500,
                "video": True,
                "screenshots": True
            }
        }
        
        # Add page-specific configurations with seeded data
        page_type = page_analysis["structure"]["page_type"]
        
        if page_type == "login":
            # Generate valid and invalid user profiles
            valid_user = faker.user_profile()
            env_config["test_data"] = {
                "valid_credentials": {
                    "username": valid_user['username'],
                    "password": "TestPass123!",
                    "email": valid_user['email']
                },
                "invalid_credentials": {
                    "username": f"invalid_{faker.get_run_id_suffix()}",
                    "password": "wrong_password",
                    "email": f"invalid+{faker.get_run_id_suffix()}@example.com"
                }
            }
        elif page_type == "registration":
            user_data = faker.user_profile()
            env_config["test_data"] = {
                "user_data": {
                    "first_name": user_data['first_name'],
                    "last_name": user_data['last_name'],
                    "full_name": user_data['full_name'],
                    "username": user_data['username'],
                    "email": user_data['email'],
                    "password": "TestPass123!",
                    "confirm_password": "TestPass123!",
                    "phone": user_data['phone'],
                    "date_of_birth": user_data['date_of_birth'],
                    "job_title": user_data['job_title'],
                    "company": user_data['company']
                }
            }
        elif page_type == "checkout":
            payment_data = faker.payment_data()
            address_data = faker.address_data()
            user_data = faker.user_profile()
            
            env_config["test_data"] = {
                "payment_info": {
                    "card_number": payment_data['card_number'],
                    "card_type": payment_data['card_type'],
                    "expiry": f"{payment_data['expiry_month']}/{payment_data['expiry_year'][-2:]}",
                    "expiry_month": payment_data['expiry_month'],
                    "expiry_year": payment_data['expiry_year'],
                    "cvv": payment_data['cvv'],
                    "cardholder_name": payment_data['cardholder_name']
                },
                "billing_address": {
                    "first_name": user_data['first_name'],
                    "last_name": user_data['last_name'],
                    "street_address": address_data['street_address'],
                    "city": address_data['city'],
                    "state": address_data['state'],
                    "state_abbr": address_data['state_abbr'],
                    "postal_code": address_data['postal_code'],
                    "country": address_data['country'],
                    "phone": user_data['phone']
                },
                "shipping_address": {
                    "first_name": user_data['first_name'],
                    "last_name": user_data['last_name'],
                    "street_address": address_data['street_address'],
                    "city": address_data['city'],
                    "state": address_data['state'],
                    "state_abbr": address_data['state_abbr'],
                    "postal_code": address_data['postal_code'],
                    "country": address_data['country'],
                    "phone": user_data['phone']
                }
            }
        elif page_type == "contact":
            contact_data = faker.user_profile()
            business_data = faker.business_data()
            
            env_config["test_data"] = {
                "contact_info": {
                    "name": contact_data['full_name'],
                    "email": contact_data['email'],
                    "phone": contact_data['phone'],
                    "company": business_data['company_name'],
                    "subject": "Test inquiry from automated testing",
                    "message": "This is a test message generated for automated testing purposes."
                }
            }
        
        # Add form data for generic form fields
        if page_analysis.get('structure', {}).get('forms'):
            form_fields = []
            for form in page_analysis['structure']['forms']:
                form_fields.extend([field['name'] for field in form.get('fields', [])])
            
            if form_fields:
                env_config["form_data"] = faker.form_data(form_fields)
        
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

    def _generate_run_id(self) -> str:
        """Generate a unique run ID for seeding purposes."""
        timestamp = int(time.time() * 1000)  # milliseconds
        # Create a hash from timestamp for better distribution
        hash_obj = hashlib.md5(str(timestamp).encode())
        return f"gen_{timestamp}_{hash_obj.hexdigest()[:8]}"

    async def interactive_generate(self, url: str) -> Dict[str, Any]:
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