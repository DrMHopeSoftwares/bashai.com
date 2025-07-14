"""
Twilio API Integration for Phone Number Management
Handles phone number search, purchase, and management via Twilio APIs
"""

import os
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime, timezone
import base64


class TwilioAPI:
    """Twilio API integration class for phone number operations"""
    
    def __init__(self, account_sid: str = None, auth_token: str = None):
        self.account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.base_url = f'https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}'
        
        if not self.account_sid or not self.auth_token:
            print("Warning: Twilio credentials not found. Using mock data.")
            self.use_mock = True
        else:
            self.use_mock = False
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make authenticated request to Twilio API"""
        if self.use_mock:
            return self._get_mock_response(endpoint, data)
        
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        # Twilio uses HTTP Basic Auth
        credentials = f"{self.account_sid}:{self.auth_token}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers['Authorization'] = f'Basic {encoded_credentials}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data)
            elif method == 'POST':
                response = requests.post(url, headers=headers, data=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Twilio API error: {e}")
            return {'error': str(e), 'success': False}
    
    def _get_mock_response(self, endpoint: str, data: Dict = None) -> Dict:
        """Return mock responses for testing without real API calls"""
        if 'AvailablePhoneNumbers' in endpoint:
            # Mock phone number search
            country_code = 'US'
            if 'US' in endpoint:
                country_code = 'US'
            elif 'GB' in endpoint:
                country_code = 'GB'
            elif 'CA' in endpoint:
                country_code = 'CA'
            
            pattern = data.get('Contains', '') if data else ''
            area_code = data.get('AreaCode', '555') if data else '555'
            
            mock_numbers = [
                {
                    'phone_number': f'+1{area_code}{pattern}001',
                    'friendly_name': f'+1 ({area_code}) {pattern}-001',
                    'iso_country': country_code,
                    'capabilities': {
                        'voice': True,
                        'SMS': True,
                        'MMS': True,
                        'fax': False
                    },
                    'locality': 'San Francisco',
                    'region': 'CA',
                    'postal_code': '94102',
                    'address_requirements': 'none',
                    'beta': False
                },
                {
                    'phone_number': f'+1{area_code}{pattern}002',
                    'friendly_name': f'+1 ({area_code}) {pattern}-002',
                    'iso_country': country_code,
                    'capabilities': {
                        'voice': True,
                        'SMS': True,
                        'MMS': True,
                        'fax': False
                    },
                    'locality': 'San Francisco',
                    'region': 'CA',
                    'postal_code': '94102',
                    'address_requirements': 'none',
                    'beta': False
                },
                {
                    'phone_number': f'+1{area_code}{pattern}003',
                    'friendly_name': f'+1 ({area_code}) {pattern}-003',
                    'iso_country': country_code,
                    'capabilities': {
                        'voice': True,
                        'SMS': True,
                        'MMS': True,
                        'fax': False
                    },
                    'locality': 'San Francisco',
                    'region': 'CA',
                    'postal_code': '94102',
                    'address_requirements': 'none',
                    'beta': False
                }
            ]
            
            return {
                'available_phone_numbers': mock_numbers,
                'uri': f"/2010-04-01/Accounts/{self.account_sid}/AvailablePhoneNumbers/{country_code}/Local.json"
            }
        
        elif 'IncomingPhoneNumbers.json' in endpoint and data:
            # Mock phone number purchase
            return {
                'sid': 'mock-twilio-sid',
                'account_sid': self.account_sid or 'mock-account-sid',
                'phone_number': data.get('PhoneNumber', '+15551234567'),
                'friendly_name': data.get('FriendlyName', ''),
                'capabilities': {
                    'voice': True,
                    'SMS': True,
                    'MMS': True,
                    'fax': False
                },
                'status': 'in-use',
                'date_created': datetime.now(timezone.utc).isoformat(),
                'date_updated': datetime.now(timezone.utc).isoformat(),
                'uri': f"/2010-04-01/Accounts/{self.account_sid}/IncomingPhoneNumbers/mock-twilio-sid.json"
            }
        
        return {'error': 'Mock endpoint not implemented', 'success': False}
    
    def search_phone_numbers(self, 
                           country_code: str = 'US', 
                           area_code: str = None,
                           contains: str = None,
                           in_region: str = None,
                           in_locality: str = None,
                           number_type: str = 'Local',
                           limit: int = 20) -> Dict:
        """
        Search for available phone numbers
        
        Args:
            country_code: Country code (e.g., 'US', 'GB', 'CA')
            area_code: Area code to search in
            contains: Pattern the number should contain
            in_region: State/region to search in
            in_locality: City/locality to search in
            number_type: Type of number ('Local', 'TollFree', 'Mobile')
            limit: Maximum number of results
        
        Returns:
            Dict with available phone numbers
        """
        endpoint = f'AvailablePhoneNumbers/{country_code}/{number_type}.json'
        
        params = {'PageSize': limit}
        
        if area_code:
            params['AreaCode'] = area_code
        if contains:
            params['Contains'] = contains
        if in_region:
            params['InRegion'] = in_region
        if in_locality:
            params['InLocality'] = in_locality
        
        response = self._make_request('GET', endpoint, params)
        
        if 'available_phone_numbers' in response:
            # Transform Twilio response to standardized format
            numbers = []
            for num in response['available_phone_numbers']:
                # Estimate pricing (Twilio pricing varies by region)
                monthly_cost = self._estimate_monthly_cost(country_code, number_type)
                
                numbers.append({
                    'phone_number': num['phone_number'],
                    'country_code': country_code,
                    'country_name': self._get_country_name(country_code),
                    'monthly_cost': monthly_cost,
                    'setup_cost': 0.00,  # Twilio typically doesn't charge setup fees
                    'capabilities': {
                        'voice': num['capabilities'].get('voice', False),
                        'sms': num['capabilities'].get('SMS', False),
                        'mms': num['capabilities'].get('MMS', False)
                    },
                    'provider': 'twilio',
                    'provider_metadata': {
                        'friendly_name': num.get('friendly_name'),
                        'locality': num.get('locality'),
                        'region': num.get('region'),
                        'postal_code': num.get('postal_code'),
                        'address_requirements': num.get('address_requirements'),
                        'beta': num.get('beta', False)
                    }
                })
            
            return {
                'success': True,
                'available_numbers': numbers,
                'total_count': len(numbers)
            }
        
        return {
            'success': False,
            'error': response.get('error', 'Failed to search phone numbers'),
            'available_numbers': []
        }
    
    def purchase_phone_number(self, 
                            phone_number: str, 
                            friendly_name: str = None,
                            voice_url: str = None,
                            sms_url: str = None) -> Dict:
        """
        Purchase a phone number
        
        Args:
            phone_number: The phone number to purchase
            friendly_name: Optional friendly name for the number
            voice_url: Optional webhook URL for voice calls
            sms_url: Optional webhook URL for SMS
        
        Returns:
            Dict with purchase result
        """
        data = {'PhoneNumber': phone_number}
        
        if friendly_name:
            data['FriendlyName'] = friendly_name
        if voice_url:
            data['VoiceUrl'] = voice_url
        if sms_url:
            data['SmsUrl'] = sms_url
        
        response = self._make_request('POST', 'IncomingPhoneNumbers.json', data)
        
        if 'sid' in response:
            return {
                'success': True,
                'message': 'Phone number purchased successfully',
                'phone_number': response['phone_number'],
                'provider_phone_id': response['sid'],
                'monthly_cost': self._estimate_monthly_cost(response.get('iso_country', 'US')),
                'provider_metadata': response
            }
        
        return {
            'success': False,
            'error': response.get('error', 'Failed to purchase phone number')
        }
    
    def release_phone_number(self, phone_number_sid: str) -> Dict:
        """
        Release a phone number
        
        Args:
            phone_number_sid: The Twilio SID of the phone number to release
        
        Returns:
            Dict with release result
        """
        response = self._make_request('DELETE', f'IncomingPhoneNumbers/{phone_number_sid}.json')
        
        if not response.get('error'):
            return {
                'success': True,
                'message': 'Phone number released successfully'
            }
        
        return {
            'success': False,
            'error': response.get('error', 'Failed to release phone number')
        }
    
    def get_phone_number_details(self, phone_number_sid: str) -> Dict:
        """
        Get details of a purchased phone number
        
        Args:
            phone_number_sid: The Twilio SID of the phone number
        
        Returns:
            Dict with phone number details
        """
        response = self._make_request('GET', f'IncomingPhoneNumbers/{phone_number_sid}.json')
        
        if 'sid' in response:
            return {
                'success': True,
                'phone_number': response['phone_number'],
                'sid': response['sid'],
                'friendly_name': response.get('friendly_name'),
                'capabilities': response.get('capabilities', {}),
                'monthly_cost': self._estimate_monthly_cost(response.get('iso_country', 'US')),
                'provider_metadata': response
            }
        
        return {
            'success': False,
            'error': response.get('error', 'Failed to get phone number details')
        }
    
    def list_purchased_numbers(self, page_size: int = 50) -> Dict:
        """
        List all purchased phone numbers
        
        Args:
            page_size: Number of results per page
        
        Returns:
            Dict with list of purchased numbers
        """
        params = {'PageSize': page_size}
        response = self._make_request('GET', 'IncomingPhoneNumbers.json', params)
        
        if 'incoming_phone_numbers' in response:
            numbers = []
            for num in response['incoming_phone_numbers']:
                numbers.append({
                    'phone_number': num['phone_number'],
                    'sid': num['sid'],
                    'friendly_name': num.get('friendly_name'),
                    'capabilities': num.get('capabilities', {}),
                    'monthly_cost': self._estimate_monthly_cost(num.get('iso_country', 'US')),
                    'provider_metadata': num
                })
            
            return {
                'success': True,
                'phone_numbers': numbers
            }
        
        return {
            'success': False,
            'error': response.get('error', 'Failed to list phone numbers'),
            'phone_numbers': []
        }
    
    def _estimate_monthly_cost(self, country_code: str, number_type: str = 'Local') -> float:
        """Estimate monthly cost based on country and number type"""
        # Twilio pricing estimates (in USD)
        pricing = {
            'US': {'Local': 1.00, 'TollFree': 2.00, 'Mobile': 1.00},
            'GB': {'Local': 1.50, 'TollFree': 3.00, 'Mobile': 1.50},
            'CA': {'Local': 1.00, 'TollFree': 2.00, 'Mobile': 1.00},
            'AU': {'Local': 2.00, 'TollFree': 4.00, 'Mobile': 2.00},
            'IN': {'Local': 2.50, 'TollFree': 5.00, 'Mobile': 2.50},
            'DE': {'Local': 1.50, 'TollFree': 3.00, 'Mobile': 1.50},
            'FR': {'Local': 1.50, 'TollFree': 3.00, 'Mobile': 1.50},
            'ES': {'Local': 1.50, 'TollFree': 3.00, 'Mobile': 1.50},
            'IT': {'Local': 1.50, 'TollFree': 3.00, 'Mobile': 1.50},
            'NL': {'Local': 2.00, 'TollFree': 4.00, 'Mobile': 2.00},
            'BE': {'Local': 2.00, 'TollFree': 4.00, 'Mobile': 2.00},
            'SE': {'Local': 2.00, 'TollFree': 4.00, 'Mobile': 2.00},
            'NO': {'Local': 2.50, 'TollFree': 5.00, 'Mobile': 2.50},
            'DK': {'Local': 2.00, 'TollFree': 4.00, 'Mobile': 2.00},
            'FI': {'Local': 2.00, 'TollFree': 4.00, 'Mobile': 2.00},
            'JP': {'Local': 3.00, 'TollFree': 6.00, 'Mobile': 3.00},
            'SG': {'Local': 3.00, 'TollFree': 6.00, 'Mobile': 3.00},
            'HK': {'Local': 3.00, 'TollFree': 6.00, 'Mobile': 3.00}
        }
        
        country_pricing = pricing.get(country_code, pricing['US'])
        return country_pricing.get(number_type, country_pricing['Local'])
    
    def _get_country_name(self, country_code: str) -> str:
        """Get country name from ISO code"""
        country_map = {
            'US': 'United States',
            'GB': 'United Kingdom', 
            'CA': 'Canada',
            'AU': 'Australia',
            'IN': 'India',
            'DE': 'Germany',
            'FR': 'France',
            'ES': 'Spain',
            'IT': 'Italy',
            'NL': 'Netherlands',
            'BE': 'Belgium',
            'SE': 'Sweden',
            'NO': 'Norway',
            'DK': 'Denmark',
            'FI': 'Finland',
            'JP': 'Japan',
            'SG': 'Singapore',
            'HK': 'Hong Kong'
        }
        return country_map.get(country_code, country_code)


# Example usage and testing
if __name__ == "__main__":
    # Initialize Twilio API (will use mock data if credentials not found)
    twilio = TwilioAPI()
    
    # Test phone number search
    print("Testing phone number search...")
    search_result = twilio.search_phone_numbers(country_code='US', area_code='555', limit=3)
    print(f"Search result: {json.dumps(search_result, indent=2)}")
    
    # Test phone number purchase (mock)
    if search_result['success'] and search_result['available_numbers']:
        first_number = search_result['available_numbers'][0]['phone_number']
        print(f"\nTesting phone number purchase for {first_number}...")
        purchase_result = twilio.purchase_phone_number(first_number, friendly_name="Test Number")
        print(f"Purchase result: {json.dumps(purchase_result, indent=2)}")