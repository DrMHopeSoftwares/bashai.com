"""
Telnyx API Integration for Phone Number Management
Handles phone number search, purchase, and management via Telnyx APIs
"""

import os
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime, timezone


class TelnyxAPI:
    """Telnyx API integration class for phone number operations"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('TELNYX_API_KEY')
        self.base_url = 'https://api.telnyx.com/v2'
        
        if not self.api_key:
            print("Warning: Telnyx credentials not found. Using mock data.")
            self.use_mock = True
        else:
            self.use_mock = False
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make authenticated request to Telnyx API"""
        if self.use_mock:
            return self._get_mock_response(endpoint, data)
        
        url = f"{self.base_url}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Telnyx API error: {e}")
            return {'errors': [{'detail': str(e)}], 'success': False}
    
    def _get_mock_response(self, endpoint: str, data: Dict = None) -> Dict:
        """Return mock responses for testing without real API calls"""
        if 'available_phone_numbers' in endpoint:
            # Mock phone number search
            filter_country_code = data.get('filter[country_code]', 'US') if data else 'US'
            filter_phone_number_type = data.get('filter[phone_number_type]', 'local') if data else 'local'
            filter_features = data.get('filter[features]', []) if data else []
            
            mock_numbers = [
                {
                    'phone_number': '+12025551001',
                    'record_type': 'available_phone_number',
                    'phone_number_type': filter_phone_number_type,
                    'country_code': filter_country_code,
                    'region': 'DC' if filter_country_code == 'US' else 'Region',
                    'locality': 'Washington' if filter_country_code == 'US' else 'City',
                    'features': filter_features or ['voice', 'sms', 'mms'],
                    'cost_information': {
                        'monthly_cost': '2.00',
                        'upfront_cost': '0.00'
                    },
                    'reservable': True,
                    'quickship': True,
                    'best_effort': False
                },
                {
                    'phone_number': '+12025551002',
                    'record_type': 'available_phone_number',
                    'phone_number_type': filter_phone_number_type,
                    'country_code': filter_country_code,
                    'region': 'DC' if filter_country_code == 'US' else 'Region',
                    'locality': 'Washington' if filter_country_code == 'US' else 'City',
                    'features': filter_features or ['voice', 'sms', 'mms'],
                    'cost_information': {
                        'monthly_cost': '2.00',
                        'upfront_cost': '0.00'
                    },
                    'reservable': True,
                    'quickship': True,
                    'best_effort': False
                },
                {
                    'phone_number': '+12025551003',
                    'record_type': 'available_phone_number',
                    'phone_number_type': filter_phone_number_type,
                    'country_code': filter_country_code,
                    'region': 'DC' if filter_country_code == 'US' else 'Region',
                    'locality': 'Washington' if filter_country_code == 'US' else 'City',
                    'features': filter_features or ['voice', 'sms', 'mms'],
                    'cost_information': {
                        'monthly_cost': '2.00',
                        'upfront_cost': '0.00'
                    },
                    'reservable': True,
                    'quickship': True,
                    'best_effort': False
                }
            ]
            
            return {
                'data': mock_numbers,
                'meta': {
                    'total_results': len(mock_numbers),
                    'best_effort_results': 0
                }
            }
        
        elif 'phone_numbers' in endpoint and data:
            # Mock phone number purchase
            return {
                'data': {
                    'id': 'mock-telnyx-number-id',
                    'record_type': 'phone_number',
                    'phone_number': data.get('phone_number', '+12025551234'),
                    'phone_number_type': 'local',
                    'country_code': 'US',
                    'region': 'DC',
                    'locality': 'Washington',
                    'features': ['voice', 'sms', 'mms'],
                    'status': 'purchase_pending',
                    'cost_information': {
                        'monthly_cost': '2.00',
                        'upfront_cost': '0.00'
                    },
                    'connection_id': data.get('connection_id'),
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
            }
        
        return {'errors': [{'detail': 'Mock endpoint not implemented'}], 'success': False}
    
    def search_phone_numbers(self, 
                           country_code: str = 'US',
                           phone_number_type: str = 'local',
                           region: str = None,
                           locality: str = None,
                           national_destination_code: str = None,
                           features: List[str] = None,
                           limit: int = 20) -> Dict:
        """
        Search for available phone numbers
        
        Args:
            country_code: Country code (e.g., 'US', 'GB', 'CA')
            phone_number_type: Type of number ('local', 'toll_free', 'national', 'mobile', 'landline')
            region: State/region code
            locality: City/locality name
            national_destination_code: Area code or national destination code
            features: List of required features (['voice', 'sms', 'mms', 'fax'])
            limit: Maximum number of results
        
        Returns:
            Dict with available phone numbers
        """
        params = {
            'filter[country_code]': country_code,
            'filter[phone_number_type]': phone_number_type,
            'page[size]': limit
        }
        
        if region:
            params['filter[administrative_area]'] = region
        if locality:
            params['filter[locality]'] = locality
        if national_destination_code:
            params['filter[national_destination_code]'] = national_destination_code
        if features:
            params['filter[features]'] = features
        
        response = self._make_request('GET', 'available_phone_numbers', params)
        
        if 'data' in response:
            # Transform Telnyx response to standardized format
            numbers = []
            for num in response['data']:
                numbers.append({
                    'phone_number': num['phone_number'],
                    'country_code': country_code,
                    'country_name': self._get_country_name(country_code),
                    'monthly_cost': float(num['cost_information']['monthly_cost']),
                    'setup_cost': float(num['cost_information']['upfront_cost']),
                    'capabilities': {
                        'voice': any(f.get('name') == 'voice' for f in num.get('features', []) if isinstance(f, dict)),
                        'sms': any(f.get('name') == 'sms' for f in num.get('features', []) if isinstance(f, dict)),
                        'mms': any(f.get('name') == 'mms' for f in num.get('features', []) if isinstance(f, dict))
                    },
                    'provider': 'telnyx',
                    'provider_metadata': {
                        'phone_number_type': num.get('phone_number_type'),
                        'region': num.get('region'),
                        'locality': num.get('locality'),
                        'features': num.get('features', []),
                        'reservable': num.get('reservable', False),
                        'quickship': num.get('quickship', False),
                        'best_effort': num.get('best_effort', False)
                    }
                })
            
            return {
                'success': True,
                'available_numbers': numbers,
                'total_count': response.get('meta', {}).get('total_results', len(numbers))
            }
        
        return {
            'success': False,
            'error': response.get('errors', [{}])[0].get('detail', 'Failed to search phone numbers'),
            'available_numbers': []
        }
    
    def purchase_phone_number(self, 
                            phone_number: str,
                            connection_id: str = None,
                            customer_reference: str = None,
                            billing_group_id: str = None) -> Dict:
        """
        Purchase a phone number
        
        Args:
            phone_number: The phone number to purchase
            connection_id: Connection ID to associate with the number
            customer_reference: Customer reference for the number
            billing_group_id: Billing group ID
        
        Returns:
            Dict with purchase result
        """
        data = {'phone_number': phone_number}
        
        if connection_id:
            data['connection_id'] = connection_id
        if customer_reference:
            data['customer_reference'] = customer_reference
        if billing_group_id:
            data['billing_group_id'] = billing_group_id
        
        response = self._make_request('POST', 'phone_numbers', data)
        
        if 'data' in response:
            num_data = response['data']
            return {
                'success': True,
                'message': 'Phone number purchased successfully',
                'phone_number': num_data['phone_number'],
                'provider_phone_id': num_data['id'],
                'monthly_cost': float(num_data['cost_information']['monthly_cost']),
                'status': num_data.get('status', 'active'),
                'provider_metadata': num_data
            }
        
        return {
            'success': False,
            'error': response.get('errors', [{}])[0].get('detail', 'Failed to purchase phone number')
        }
    
    def release_phone_number(self, phone_number_id: str) -> Dict:
        """
        Release a phone number
        
        Args:
            phone_number_id: The Telnyx ID of the phone number to release
        
        Returns:
            Dict with release result
        """
        response = self._make_request('DELETE', f'phone_numbers/{phone_number_id}')
        
        if not response.get('errors'):
            return {
                'success': True,
                'message': 'Phone number released successfully'
            }
        
        return {
            'success': False,
            'error': response.get('errors', [{}])[0].get('detail', 'Failed to release phone number')
        }
    
    def get_phone_number_details(self, phone_number_id: str) -> Dict:
        """
        Get details of a purchased phone number
        
        Args:
            phone_number_id: The Telnyx ID of the phone number
        
        Returns:
            Dict with phone number details
        """
        response = self._make_request('GET', f'phone_numbers/{phone_number_id}')
        
        if 'data' in response:
            num_data = response['data']
            return {
                'success': True,
                'phone_number': num_data['phone_number'],
                'id': num_data['id'],
                'status': num_data.get('status'),
                'features': num_data.get('features', []),
                'monthly_cost': float(num_data['cost_information']['monthly_cost']),
                'provider_metadata': num_data
            }
        
        return {
            'success': False,
            'error': response.get('errors', [{}])[0].get('detail', 'Failed to get phone number details')
        }
    
    def list_purchased_numbers(self, page_size: int = 50) -> Dict:
        """
        List all purchased phone numbers
        
        Args:
            page_size: Number of results per page
        
        Returns:
            Dict with list of purchased numbers
        """
        params = {'page[size]': page_size}
        response = self._make_request('GET', 'phone_numbers', params)
        
        if 'data' in response:
            numbers = []
            for num in response['data']:
                numbers.append({
                    'phone_number': num['phone_number'],
                    'id': num['id'],
                    'status': num.get('status'),
                    'features': num.get('features', []),
                    'monthly_cost': float(num['cost_information']['monthly_cost']),
                    'provider_metadata': num
                })
            
            return {
                'success': True,
                'phone_numbers': numbers
            }
        
        return {
            'success': False,
            'error': response.get('errors', [{}])[0].get('detail', 'Failed to list phone numbers'),
            'phone_numbers': []
        }
    
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
    # Initialize Telnyx API (will use mock data if credentials not found)
    telnyx = TelnyxAPI()
    
    # Test phone number search
    print("Testing phone number search...")
    search_result = telnyx.search_phone_numbers(
        country_code='US', 
        phone_number_type='local',
        national_destination_code='202',
        limit=3
    )
    print(f"Search result: {json.dumps(search_result, indent=2)}")
    
    # Test phone number purchase (mock)
    if search_result['success'] and search_result['available_numbers']:
        first_number = search_result['available_numbers'][0]['phone_number']
        print(f"\nTesting phone number purchase for {first_number}...")
        purchase_result = telnyx.purchase_phone_number(
            first_number, 
            customer_reference="DrM Hope Test"
        )
        print(f"Purchase result: {json.dumps(purchase_result, indent=2)}")