"""
Utility functions for integrating seeded data generation with the AI WebTester framework.
"""

import copy
from typing import Dict, Any, Optional
from data_gen.faker_util import get_run_specific_faker


def inject_seeded_data_into_env(env_config: Dict[str, Any], run_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Inject seeded test data into environment configuration at runtime.
    
    This function can be used by executors to replace template variables
    in environment configs with actual seeded data during test execution.
    
    Args:
        env_config: Environment configuration dictionary
        run_id: Run ID for seeding, uses env config run_id if not provided
        
    Returns:
        Environment config with seeded data injected
    """
    if run_id is None:
        run_id = env_config.get('run_id', 'default_run')
    
    # Ensure run_id is a string
    if run_id is None:
        run_id = 'default_run'
    
    faker = get_run_specific_faker(run_id)
    updated_config = copy.deepcopy(env_config)
    
    # Replace template variables in credentials
    if 'credentials' in updated_config:
        creds = updated_config['credentials']
        if isinstance(creds.get('email'), str) and '{{' in creds['email']:
            user_profile = faker.user_profile()
            creds['email'] = user_profile['email']
        if isinstance(creds.get('username'), str) and '{{' in creds['username']:
            user_profile = faker.user_profile()
            creds['username'] = user_profile['username']
    
    # Replace template variables in test data
    if 'test_data' in updated_config:
        test_data = updated_config['test_data']
        
        # Handle user data templates
        if 'user_data' in test_data:
            user_data = test_data['user_data']
            if any('{{' in str(v) for v in user_data.values()):
                seeded_user = faker.user_profile()
                for key, value in user_data.items():
                    if isinstance(value, str) and '{{' in value:
                        if key in seeded_user:
                            user_data[key] = seeded_user[key]
        
        # Handle payment info templates
        if 'payment_info' in test_data:
            payment_info = test_data['payment_info']
            if any('{{' in str(v) for v in payment_info.values()):
                seeded_payment = faker.payment_data()
                for key, value in payment_info.items():
                    if isinstance(value, str) and '{{' in value:
                        if key in seeded_payment:
                            payment_info[key] = seeded_payment[key]
        
        # Handle address templates
        for address_key in ['billing_address', 'shipping_address', 'address']:
            if address_key in test_data:
                address_data = test_data[address_key]
                if any('{{' in str(v) for v in address_data.values()):
                    seeded_address = faker.address_data()
                    for key, value in address_data.items():
                        if isinstance(value, str) and '{{' in value:
                            if key in seeded_address:
                                address_data[key] = seeded_address[key]
    
    return updated_config


def get_form_fill_data(field_names: list, run_id: str) -> Dict[str, str]:
    """
    Get seeded form data for filling web forms during test execution.
    
    Args:
        field_names: List of form field names
        run_id: Run ID for seeding
        
    Returns:
        Dictionary mapping field names to seeded values
    """
    faker = get_run_specific_faker(run_id)
    return faker.form_data(field_names)


def get_test_user_profile(run_id: str) -> Dict[str, str]:
    """
    Get a complete seeded user profile for testing.
    
    Args:
        run_id: Run ID for seeding
        
    Returns:
        Dictionary with user profile data
    """
    faker = get_run_specific_faker(run_id)
    return faker.user_profile()


def get_unique_email(run_id: str, prefix: str = "qa", domain: str = "example.com") -> str:
    """
    Get a unique email address for testing.
    
    Args:
        run_id: Run ID for seeding
        prefix: Email prefix
        domain: Email domain
        
    Returns:
        Unique email address with run ID suffix
    """
    faker = get_run_specific_faker(run_id)
    return faker.email(domain=domain, prefix=prefix)