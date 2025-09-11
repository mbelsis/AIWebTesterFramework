"""
Seeded Faker utility for consistent test data generation across AI WebTester framework.

This module provides deterministic data generation that ensures:
- Same run ID produces identical data every time
- Different run IDs produce different but consistent data sets
- Email uniqueness with run-specific suffixes
- Realistic test data using Faker providers
"""

import hashlib
from typing import Dict, Any, Optional, List, Union
from faker import Faker
from faker.providers import internet, person, company, phone_number, address


class SeededFaker:
    """Seeded Faker utility for consistent test data generation."""
    
    def __init__(self, run_id: str, locale: str = 'en_US'):
        """
        Initialize SeededFaker with consistent seeding per test run.
        
        Args:
            run_id: Unique run identifier for seeding
            locale: Faker locale (default: 'en_US')
        """
        self.run_id = run_id
        self.locale = locale
        self.faker = Faker(locale)
        
        # Generate consistent seed from run_id
        self.seed = self._generate_seed(run_id)
        self.faker.seed_instance(self.seed)
        
        # Cache for consistent data within a run
        self._cache: Dict[str, Any] = {}
        
    def _generate_seed(self, run_id: str) -> int:
        """
        Generate consistent seed from run_id.
        
        Args:
            run_id: Run identifier
            
        Returns:
            Integer seed for Faker
        """
        try:
            # Try to extract hex-like portion from run_id
            if len(run_id) >= 6:
                hex_part = run_id[-6:]
                return int(hex_part, 16) % (2**31 - 1)  # Ensure positive 32-bit int
        except ValueError:
            pass
        
        # Fall back to hash-based seed
        hash_obj = hashlib.md5(run_id.encode('utf-8'))
        return int(hash_obj.hexdigest()[:8], 16) % (2**31 - 1)
    
    def get_run_id_suffix(self, length: int = 6) -> str:
        """Get consistent run ID suffix for uniqueness."""
        return self.run_id[:length]
    
    def email(self, domain: str = "example.com", prefix: str = "qa") -> str:
        """
        Generate run-specific unique email.
        
        Args:
            domain: Email domain
            prefix: Email prefix
            
        Returns:
            Unique email with run ID suffix
        """
        suffix = self.get_run_id_suffix()
        base_name = self.faker.user_name()
        return f"{prefix}+{base_name}+{suffix}@{domain}"
    
    def user_profile(self, consistent_names: bool = True) -> Dict[str, str]:
        """
        Generate consistent user profile data.
        
        Args:
            consistent_names: Whether first/last names should match logically
            
        Returns:
            Dictionary with user profile data
        """
        cache_key = "user_profile"
        if cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        if consistent_names:
            # Generate matching first/last name pair
            first_name = self.faker.first_name()
            last_name = self.faker.last_name()
        else:
            first_name = self.faker.first_name()
            last_name = self.faker.last_name()
        
        profile = {
            'first_name': first_name,
            'last_name': last_name,
            'full_name': f"{first_name} {last_name}",
            'username': self.faker.user_name(),
            'email': self.email(),
            'phone': self.faker.phone_number(),
            'date_of_birth': self.faker.date_of_birth().isoformat(),
            'job_title': self.faker.job(),
            'company': self.faker.company()
        }
        
        self._cache[cache_key] = profile.copy()
        return profile
    
    def address_data(self) -> Dict[str, str]:
        """Generate consistent address data."""
        cache_key = "address"
        if cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        address = {
            'street_address': self.faker.street_address(),
            'city': self.faker.city(),
            'state': self.faker.state(),
            'state_abbr': self.faker.state_abbr(),
            'postal_code': self.faker.postcode(),
            'country': self.faker.country(),
            'country_code': self.faker.country_code()
        }
        
        self._cache[cache_key] = address.copy()
        return address
    
    def payment_data(self) -> Dict[str, str]:
        """Generate test-safe payment data."""
        cache_key = "payment"
        if cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        # Use test credit card numbers that won't process
        test_cards = [
            ("4111111111111111", "Visa"),        # Visa test card
            ("5555555555554444", "Mastercard"),  # Mastercard test card
            ("378282246310005", "AMEX"),         # American Express test card
        ]
        
        card_number, card_type = self.faker.random.choice(test_cards)
        
        payment = {
            'card_number': card_number,
            'card_type': card_type,
            'expiry_month': f"{self.faker.random_int(min=1, max=12):02d}",
            'expiry_year': str(self.faker.random_int(min=2024, max=2030)),
            'cvv': f"{self.faker.random_int(min=100, max=999)}",
            'cardholder_name': f"{self.faker.first_name()} {self.faker.last_name()}"
        }
        
        self._cache[cache_key] = payment.copy()
        return payment
    
    def business_data(self) -> Dict[str, str]:
        """Generate consistent business data."""
        cache_key = "business"
        if cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        business = {
            'company_name': self.faker.company(),
            'company_suffix': self.faker.company_suffix(),
            'business_email': self.email(domain="business.com", prefix="biz"),
            'phone': self.faker.phone_number(),
            'website': self.faker.url(),
            'industry': self.faker.job(),
            'description': self.faker.catch_phrase()
        }
        
        self._cache[cache_key] = business.copy()
        return business
    
    def form_data(self, fields: List[str]) -> Dict[str, str]:
        """
        Generate form data for specific fields.
        
        Args:
            fields: List of field names to generate data for
            
        Returns:
            Dictionary mapping field names to generated values
        """
        cache_key = f"form_data:{':'.join(sorted(fields))}"
        if cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        user_profile = self.user_profile()
        address = self.address_data()
        payment = self.payment_data()
        
        # Field mapping for common form fields
        field_mapping = {
            # Personal info
            'first_name': user_profile['first_name'],
            'firstName': user_profile['first_name'],
            'last_name': user_profile['last_name'],
            'lastName': user_profile['last_name'],
            'full_name': user_profile['full_name'],
            'fullName': user_profile['full_name'],
            'name': user_profile['full_name'],
            'username': user_profile['username'],
            'email': user_profile['email'],
            'phone': user_profile['phone'],
            'phoneNumber': user_profile['phone'],
            'date_of_birth': user_profile['date_of_birth'],
            'dateOfBirth': user_profile['date_of_birth'],
            
            # Address info
            'address': address['street_address'],
            'street_address': address['street_address'],
            'streetAddress': address['street_address'],
            'city': address['city'],
            'state': address['state'],
            'zip': address['postal_code'],
            'postal_code': address['postal_code'],
            'postalCode': address['postal_code'],
            'country': address['country'],
            
            # Payment info
            'card_number': payment['card_number'],
            'cardNumber': payment['card_number'],
            'expiry': f"{payment['expiry_month']}/{payment['expiry_year'][-2:]}",
            'expiry_date': f"{payment['expiry_month']}/{payment['expiry_year'][-2:]}",
            'expiryDate': f"{payment['expiry_month']}/{payment['expiry_year'][-2:]}",
            'cvv': payment['cvv'],
            'cardholder_name': payment['cardholder_name'],
            'cardholderName': payment['cardholder_name'],
            
            # Credentials
            'password': 'TestPass123!',
            'confirm_password': 'TestPass123!',
            'confirmPassword': 'TestPass123!',
            
            # Generic fallbacks
            'text': self.faker.sentence(),
            'description': self.faker.text(),
            'comment': self.faker.text(),
            'message': self.faker.paragraph(),
            'title': self.faker.sentence(nb_words=4),
            'url': self.faker.url(),
            'website': self.faker.url(),
        }
        
        form_data = {}
        for field in fields:
            if field in field_mapping:
                form_data[field] = field_mapping[field]
            else:
                # Generate generic data based on field name patterns
                field_lower = field.lower()
                if 'email' in field_lower:
                    form_data[field] = self.email()
                elif 'name' in field_lower:
                    form_data[field] = user_profile['full_name']
                elif 'phone' in field_lower:
                    form_data[field] = user_profile['phone']
                elif 'address' in field_lower:
                    form_data[field] = address['street_address']
                elif 'password' in field_lower:
                    form_data[field] = 'TestPass123!'
                else:
                    form_data[field] = self.faker.sentence()
        
        self._cache[cache_key] = form_data.copy()
        return form_data
    
    def reset_cache(self):
        """Reset the data cache while keeping the same seed."""
        self._cache.clear()


# Global cache for SeededFaker instances
_faker_instances: Dict[str, SeededFaker] = {}


def get_run_specific_faker(run_id: str, locale: str = 'en_US') -> SeededFaker:
    """
    Get or create a SeededFaker instance for a specific run.
    
    Args:
        run_id: Unique run identifier
        locale: Faker locale
        
    Returns:
        SeededFaker instance for the run
    """
    cache_key = f"{run_id}:{locale}"
    if cache_key not in _faker_instances:
        _faker_instances[cache_key] = SeededFaker(run_id, locale)
    return _faker_instances[cache_key]


def clear_faker_cache():
    """Clear all cached SeededFaker instances."""
    global _faker_instances
    _faker_instances.clear()