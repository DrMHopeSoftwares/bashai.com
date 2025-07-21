"""
Unified Phone Provider Integration
Handles phone number operations across multiple providers (Plivo, Twilio, Telnyx)
"""

import os
from typing import Dict, List, Optional
from plivo_integration import PlivoAPI
from twilio_integration import TwilioAPI
from telnyx_integration import TelnyxAPI


class PhoneProviderManager:
    """Unified manager for multiple phone number providers"""
    
    def __init__(self):
        self.providers = {
            'plivo': PlivoAPI(),
            'twilio': TwilioAPI(),
            'telnyx': TelnyxAPI(),
        }
        
        # Provider availability based on credentials
        self.available_providers = {}
        for name, provider in self.providers.items():
            self.available_providers[name] = not getattr(provider, 'use_mock', True)
    
    def get_provider(self, provider_name: str):
        """Get provider instance by name"""
        provider = self.providers.get(provider_name.lower())
        if not provider:
            raise ValueError(f"Unsupported provider: {provider_name}. Supported: plivo, twilio, telnyx")
        return provider
    
    def search_phone_numbers(self, 
                           provider_name: str,
                           country_code: str = 'US',
                           pattern: str = None,
                           region: str = None,
                           limit: int = 20) -> Dict:
        """
        Search for available phone numbers using specified provider
        
        Args:
            provider_name: Provider to use ('plivo', 'twilio')
            country_code: Country code (e.g., 'US', 'GB', 'CA')
            pattern: Number pattern to search for
            region: Region/state code
            limit: Maximum number of results
        
        Returns:
            Dict with available phone numbers
        """
        try:
            provider = self.get_provider(provider_name)
            
            if provider_name.lower() == 'plivo':
                return provider.search_phone_numbers(
                    country_iso=country_code,
                    pattern=pattern,
                    region=region,
                    limit=limit
                )
            elif provider_name.lower() == 'twilio':
                # For Twilio, extract area code from pattern if it's numeric
                area_code = None
                contains = pattern
                
                if pattern and pattern.isdigit() and len(pattern) == 3:
                    area_code = pattern
                    contains = None
                
                return provider.search_phone_numbers(
                    country_code=country_code,
                    area_code=area_code,
                    contains=contains,
                    in_region=region,
                    limit=limit
                )
            elif provider_name.lower() == 'telnyx':
                # For Telnyx, use national_destination_code for area code
                national_destination_code = None
                if pattern and pattern.isdigit() and len(pattern) == 3:
                    national_destination_code = pattern
                
                return provider.search_phone_numbers(
                    country_code=country_code,
                    phone_number_type='local',
                    region=region,
                    national_destination_code=national_destination_code,
                    features=['voice', 'sms'],
                    limit=limit
                )
            else:
                return {
                    'success': False,
                    'error': f'Provider {provider_name} not implemented',
                    'available_numbers': []
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error searching numbers with {provider_name}: {str(e)}',
                'available_numbers': []
            }
    
    def purchase_phone_number(self, 
                            provider_name: str,
                            phone_number: str,
                            **kwargs) -> Dict:
        """
        Purchase a phone number using specified provider
        
        Args:
            provider_name: Provider to use ('plivo', 'twilio')
            phone_number: The phone number to purchase
            **kwargs: Provider-specific options
        
        Returns:
            Dict with purchase result
        """
        try:
            provider = self.get_provider(provider_name)
            
            if provider_name.lower() == 'plivo':
                application_id = kwargs.get('application_id')
                return provider.purchase_phone_number(phone_number, application_id)
            elif provider_name.lower() == 'twilio':
                friendly_name = kwargs.get('friendly_name')
                voice_url = kwargs.get('voice_url')
                sms_url = kwargs.get('sms_url')
                return provider.purchase_phone_number(
                    phone_number, friendly_name, voice_url, sms_url
                )
            elif provider_name.lower() == 'telnyx':
                connection_id = kwargs.get('connection_id')
                customer_reference = kwargs.get('customer_reference', 'DrM Hope Purchase')
                billing_group_id = kwargs.get('billing_group_id')
                return provider.purchase_phone_number(
                    phone_number, connection_id, customer_reference, billing_group_id
                )
            else:
                return {
                    'success': False,
                    'error': f'Provider {provider_name} not implemented'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error purchasing number with {provider_name}: {str(e)}'
            }
    
    def release_phone_number(self, 
                           provider_name: str,
                           phone_number_id: str) -> Dict:
        """
        Release a phone number using specified provider
        
        Args:
            provider_name: Provider to use ('plivo', 'twilio')
            phone_number_id: Provider-specific phone number identifier
        
        Returns:
            Dict with release result
        """
        try:
            provider = self.get_provider(provider_name)
            
            if provider_name.lower() == 'plivo':
                return provider.release_phone_number(phone_number_id)
            elif provider_name.lower() == 'twilio':
                return provider.release_phone_number(phone_number_id)
            elif provider_name.lower() == 'telnyx':
                return provider.release_phone_number(phone_number_id)
            else:
                return {
                    'success': False,
                    'error': f'Provider {provider_name} not implemented'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error releasing number with {provider_name}: {str(e)}'
            }
    
    def get_phone_number_details(self, 
                               provider_name: str,
                               phone_number_id: str) -> Dict:
        """
        Get phone number details using specified provider
        
        Args:
            provider_name: Provider to use ('plivo', 'twilio')
            phone_number_id: Provider-specific phone number identifier
        
        Returns:
            Dict with phone number details
        """
        try:
            provider = self.get_provider(provider_name)
            
            if provider_name.lower() == 'plivo':
                return provider.get_phone_number_details(phone_number_id)
            elif provider_name.lower() == 'twilio':
                return provider.get_phone_number_details(phone_number_id)
            elif provider_name.lower() == 'telnyx':
                return provider.get_phone_number_details(phone_number_id)
            else:
                return {
                    'success': False,
                    'error': f'Provider {provider_name} not implemented'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error getting number details with {provider_name}: {str(e)}'
            }
    
    def list_purchased_numbers(self, provider_name: str) -> Dict:
        """
        List purchased phone numbers using specified provider
        
        Args:
            provider_name: Provider to use ('plivo', 'twilio')
        
        Returns:
            Dict with list of purchased numbers
        """
        try:
            provider = self.get_provider(provider_name)
            
            if provider_name.lower() == 'plivo':
                return provider.list_purchased_numbers()
            elif provider_name.lower() == 'twilio':
                return provider.list_purchased_numbers()
            elif provider_name.lower() == 'telnyx':
                return provider.list_purchased_numbers()
            else:
                return {
                    'success': False,
                    'error': f'Provider {provider_name} not implemented',
                    'phone_numbers': []
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error listing numbers with {provider_name}: {str(e)}',
                'phone_numbers': []
            }
    
    def get_provider_status(self) -> Dict:
        """
        Get status of all providers (whether they have valid credentials)
        
        Returns:
            Dict with provider status information
        """
        status = {}
        for name, available in self.available_providers.items():
            status[name] = {
                'available': available,
                'has_credentials': available,
                'mock_mode': not available
            }
        return status
    
    def get_supported_countries(self, provider_name: str) -> List[str]:
        """
        Get list of supported countries for a provider
        
        Args:
            provider_name: Provider name
        
        Returns:
            List of supported country codes
        """
        # Default supported countries based on provider documentation
        provider_countries = {
            'plivo': ['US', 'UK', 'CA', 'AU', 'IN', 'DE', 'FR', 'ES', 'IT', 'NL', 'BE', 'SE', 'NO', 'DK', 'FI'],
            'twilio': ['US', 'UK', 'CA', 'AU', 'IN', 'DE', 'FR', 'ES', 'IT', 'NL', 'BE', 'SE', 'NO', 'DK', 'FI', 'JP', 'SG', 'HK'],
            'telnyx': ['US', 'UK', 'CA', 'AU', 'IN', 'DE', 'FR', 'ES', 'IT', 'NL', 'BE', 'SE', 'NO', 'DK', 'FI']
        }
        
        return provider_countries.get(provider_name.lower(), [])


# Global instance
phone_provider_manager = PhoneProviderManager()


# Example usage and testing
if __name__ == "__main__":
    import json
    
    manager = PhoneProviderManager()
    
    # Test provider status
    print("Provider Status:")
    print(json.dumps(manager.get_provider_status(), indent=2))
    
    # Test search with Plivo
    print("\nTesting Plivo search...")
    plivo_result = manager.search_phone_numbers('plivo', 'US', '555', limit=3)
    print(json.dumps(plivo_result, indent=2))
    
    # Test search with Twilio
    print("\nTesting Twilio search...")
    twilio_result = manager.search_phone_numbers('twilio', 'US', '555', limit=3)
    print(json.dumps(twilio_result, indent=2))
    
    # Test purchase (mock)
    if plivo_result['success'] and plivo_result['available_numbers']:
        first_number = plivo_result['available_numbers'][0]['phone_number']
        print(f"\nTesting purchase with Plivo for {first_number}...")
        purchase_result = manager.purchase_phone_number('plivo', first_number)
        print(json.dumps(purchase_result, indent=2))