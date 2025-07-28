"""
Plivo API Integration for Phone Number Management
Handles phone number search, purchase, and management via Plivo APIs
"""

import os
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime, timezone


class PlivoAPI:
    """Plivo API integration class for phone number operations"""
    
    def __init__(self, auth_id: str = None, auth_token: str = None):
        self.auth_id = auth_id or os.getenv('PLIVO_AUTH_ID')
        self.auth_token = auth_token or os.getenv('PLIVO_AUTH_TOKEN')
        self.base_url = 'https://api.plivo.com/v1/Account/{}'.format(self.auth_id)
        
        if not self.auth_id or not self.auth_token:
            print("Warning: Plivo credentials not found. Using mock data.")
            self.use_mock = True
        else:
            self.use_mock = False
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make authenticated request to Plivo API"""
        if self.use_mock:
            return self._get_mock_response(endpoint, data)
        
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        auth = (self.auth_id, self.auth_token)
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, auth=auth, params=data)
            elif method == 'POST':
                response = requests.post(url, headers=headers, auth=auth, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, auth=auth)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Plivo API error: {e}")
            return {'error': str(e), 'success': False}
    
    def _get_mock_response(self, endpoint: str, data: Dict = None) -> Dict:
        """Return mock responses for testing without real API calls"""
        if 'PhoneNumber' in endpoint and 'GET' in str(data):
            # Mock phone number search
            pattern = data.get('pattern', '') if data else ''
            country_iso = data.get('country_iso', 'US') if data else 'US'
            
            mock_numbers = [
                {
                    'number': f'+1555{pattern}001',
                    'monthly_rental_rate': '5.00',
                    'setup_rate': '0.00',
                    'number_type': 'local',
                    'country': country_iso,
                    'region': 'US-CA' if country_iso == 'US' else country_iso,
                    'prefix': pattern or '555',
                    'city': 'San Francisco' if country_iso == 'US' else 'City',
                    'lata': '722' if country_iso == 'US' else None,
                    'rate_center': 'SNFC CNTRL' if country_iso == 'US' else None,
                    'capabilities': ['voice', 'sms']
                },
                {
                    'number': f'+1555{pattern}002',
                    'monthly_rental_rate': '5.00',
                    'setup_rate': '0.00',
                    'number_type': 'local',
                    'country': country_iso,
                    'region': 'US-CA' if country_iso == 'US' else country_iso,
                    'prefix': pattern or '555',
                    'city': 'San Francisco' if country_iso == 'US' else 'City',
                    'lata': '722' if country_iso == 'US' else None,
                    'rate_center': 'SNFC CNTRL' if country_iso == 'US' else None,
                    'capabilities': ['voice', 'sms']
                },
                {
                    'number': f'+1555{pattern}003',
                    'monthly_rental_rate': '5.00',
                    'setup_rate': '0.00',
                    'number_type': 'local',
                    'country': country_iso,
                    'region': 'US-CA' if country_iso == 'US' else country_iso,
                    'prefix': pattern or '555',
                    'city': 'San Francisco' if country_iso == 'US' else 'City',
                    'lata': '722' if country_iso == 'US' else None,
                    'rate_center': 'SNFC CNTRL' if country_iso == 'US' else None,
                    'capabilities': ['voice', 'sms']
                }
            ]
            
            return {
                'api_id': 'mock-api-id',
                'meta': {
                    'limit': 20,
                    'offset': 0,
                    'total_count': len(mock_numbers)
                },
                'objects': mock_numbers
            }
        
        elif 'PhoneNumber' in endpoint and 'POST' in str(data):
            # Mock phone number purchase
            return {
                'api_id': 'mock-purchase-id',
                'message': 'Phone number purchased successfully',
                'status': 'success',
                'number': data.get('number', '+15551234567'),
                'monthly_rental_rate': '5.00',
                'application_id': None
            }
        
        return {'error': 'Mock endpoint not implemented', 'success': False}
    
    def search_phone_numbers(self, 
                           country_iso: str = 'US', 
                           pattern: str = None, 
                           region: str = None,
                           number_type: str = 'local',
                           limit: int = 20) -> Dict:
        """
        Search for available phone numbers
        
        Args:
            country_iso: Country code (e.g., 'US', 'GB', 'CA')
            pattern: Number pattern to search for
            region: Region/state code
            number_type: Type of number ('local', 'tollfree')
            limit: Maximum number of results
        
        Returns:
            Dict with available phone numbers
        """
        params = {
            'country_iso': country_iso,
            'type': number_type,
            'limit': limit
        }
        
        if pattern:
            params['pattern'] = pattern
        if region:
            params['region'] = region
        
        response = self._make_request('GET', 'PhoneNumber/', params)
        
        if 'objects' in response:
            # Transform Plivo response to standardized format
            numbers = []
            for num in response['objects']:
                numbers.append({
                    'phone_number': num['number'],
                    'country_code': country_iso,
                    'country_name': self._get_country_name(country_iso),
                    'monthly_cost': float(num['monthly_rental_rate']),
                    'setup_cost': float(num['setup_rate']),
                    'capabilities': {
                        'voice': 'voice' in num.get('capabilities', []),
                        'sms': 'sms' in num.get('capabilities', [])
                    },
                    'provider': 'plivo',
                    'provider_metadata': {
                        'number_type': num.get('number_type'),
                        'region': num.get('region'),
                        'city': num.get('city'),
                        'lata': num.get('lata'),
                        'rate_center': num.get('rate_center')
                    }
                })
            
            return {
                'success': True,
                'available_numbers': numbers,
                'total_count': response.get('meta', {}).get('total_count', len(numbers))
            }
        
        return {
            'success': False,
            'error': response.get('error', 'Failed to search phone numbers'),
            'available_numbers': []
        }
    
    def purchase_phone_number(self, phone_number: str, application_id: str = None) -> Dict:
        """
        Purchase a phone number
        
        Args:
            phone_number: The phone number to purchase
            application_id: Optional Plivo application ID
        
        Returns:
            Dict with purchase result
        """
        data = {'number': phone_number}
        if application_id:
            data['application_id'] = application_id
        
        response = self._make_request('POST', f'PhoneNumber/{phone_number}/', data)
        
        if response.get('status') == 'success' or 'message' in response:
            return {
                'success': True,
                'message': response.get('message', 'Phone number purchased successfully'),
                'phone_number': phone_number,
                'provider_phone_id': response.get('api_id', 'mock-id'),
                'monthly_cost': float(response.get('monthly_rental_rate', '5.00')),
                'provider_metadata': response
            }
        
        return {
            'success': False,
            'error': response.get('error', 'Failed to purchase phone number')
        }
    
    def release_phone_number(self, phone_number: str) -> Dict:
        """
        Release/unrent a phone number
        
        Args:
            phone_number: The phone number to release
        
        Returns:
            Dict with release result
        """
        response = self._make_request('DELETE', f'PhoneNumber/{phone_number}/')
        
        if response.get('status') == 'success' or not response.get('error'):
            return {
                'success': True,
                'message': 'Phone number released successfully'
            }
        
        return {
            'success': False,
            'error': response.get('error', 'Failed to release phone number')
        }
    
    def get_phone_number_details(self, phone_number: str) -> Dict:
        """
        Get details of a purchased phone number
        
        Args:
            phone_number: The phone number to get details for
        
        Returns:
            Dict with phone number details
        """
        response = self._make_request('GET', f'PhoneNumber/{phone_number}/')
        
        if 'number' in response:
            return {
                'success': True,
                'phone_number': response['number'],
                'monthly_cost': float(response.get('monthly_rental_rate', '0.00')),
                'capabilities': response.get('capabilities', []),
                'provider_metadata': response
            }
        
        return {
            'success': False,
            'error': response.get('error', 'Failed to get phone number details')
        }
    
    def list_purchased_numbers(self) -> Dict:
        """
        List all purchased phone numbers
        
        Returns:
            Dict with list of purchased numbers
        """
        response = self._make_request('GET', 'PhoneNumber/')
        
        if 'objects' in response:
            numbers = []
            for num in response['objects']:
                numbers.append({
                    'phone_number': num['number'],
                    'monthly_cost': float(num.get('monthly_rental_rate', '0.00')),
                    'capabilities': num.get('capabilities', []),
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
    
    def _get_country_name(self, country_iso: str) -> str:
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
            'FI': 'Finland'
        }
        return country_map.get(country_iso, country_iso)


# Example usage and testing
if __name__ == "__main__":
    # Initialize Plivo API (will use mock data if credentials not found)
    plivo = PlivoAPI()
    
    # Test phone number search
    print("Testing phone number search...")
    search_result = plivo.search_phone_numbers(country_iso='US', pattern='555', limit=3)
    print(f"Search result: {json.dumps(search_result, indent=2)}")
    
    # Test phone number purchase (mock)
    if search_result['success'] and search_result['available_numbers']:
        first_number = search_result['available_numbers'][0]['phone_number']
        print(f"\nTesting phone number purchase for {first_number}...")
        purchase_result = plivo.purchase_phone_number(first_number)
        print(f"Purchase result: {json.dumps(purchase_result, indent=2)}")