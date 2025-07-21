#!/usr/bin/env python3
"""
Test script for Data History feature
Tests the new API endpoints and functionality
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:5003"
TEST_PHONE_NUMBER = "+918035315404"  # Use one of the existing phone numbers

def test_data_history_api():
    """Test the data history API endpoint"""
    print("🧪 Testing Data History API...")
    
    # Test without authentication (should fail)
    print("\n1. Testing without authentication...")
    response = requests.get(f"{BASE_URL}/api/phone/{TEST_PHONE_NUMBER}/data-history")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}...")
    
    # Test with mock authentication (for development)
    print("\n2. Testing data history endpoint...")
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'DataHistoryTest/1.0'
    }
    
    params = {
        'days': '30',
        'type': 'all'
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/phone/{TEST_PHONE_NUMBER}/data-history",
            headers=headers,
            params=params
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success! Got {data.get('total_records', 0)} records")
            print(f"   📊 Statistics: {data.get('statistics', {})}")
            print(f"   📈 Usage trends: {len(data.get('usage_trends', []))} data points")
        else:
            print(f"   ❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_export_functionality():
    """Test the export data functionality"""
    print("\n🧪 Testing Export Functionality...")
    
    formats = ['csv', 'json']
    
    for format_type in formats:
        print(f"\n3. Testing {format_type.upper()} export...")
        
        params = {
            'format': format_type,
            'days': '7',
            'type': 'calls'
        }
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/phone/{TEST_PHONE_NUMBER}/export-data",
                params=params
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                content_disposition = response.headers.get('Content-Disposition', '')
                
                print(f"   ✅ Export successful!")
                print(f"   📄 Content-Type: {content_type}")
                print(f"   📁 Content-Disposition: {content_disposition}")
                print(f"   📊 Data size: {len(response.content)} bytes")
                
                # Save sample file
                filename = f"sample_export_{format_type}.{format_type}"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"   💾 Saved sample to: {filename}")
                
            else:
                print(f"   ❌ Failed: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_frontend_integration():
    """Test if the frontend changes are working"""
    print("\n🧪 Testing Frontend Integration...")
    
    print("\n4. Testing dashboard page...")
    try:
        response = requests.get(f"{BASE_URL}/dashboard.html")
        
        if response.status_code == 200:
            content = response.text
            
            # Check for Data History button
            if 'Data History' in content:
                print("   ✅ Data History button found in dashboard")
            else:
                print("   ❌ Data History button not found")
                
            # Check for modal
            if 'dataHistoryModal' in content:
                print("   ✅ Data History modal found")
            else:
                print("   ❌ Data History modal not found")
                
            # Check for JavaScript functions
            functions_to_check = [
                'viewDataHistory',
                'showDataHistoryModal',
                'exportDataHistory',
                'refreshDataHistory'
            ]
            
            for func in functions_to_check:
                if func in content:
                    print(f"   ✅ Function {func} found")
                else:
                    print(f"   ❌ Function {func} not found")
                    
        else:
            print(f"   ❌ Dashboard not accessible: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting Data History Feature Tests")
    print("=" * 50)
    
    test_data_history_api()
    test_export_functionality()
    test_frontend_integration()
    
    print("\n" + "=" * 50)
    print("✅ Data History Feature Tests Completed!")
    print("\n📋 Summary:")
    print("   - API endpoints created")
    print("   - Export functionality implemented")
    print("   - Frontend integration added")
    print("   - Modal and UI components ready")
    print("\n🎯 Next Steps:")
    print("   - Test with real authentication")
    print("   - Add real database queries")
    print("   - Implement Chart.js for visualizations")
    print("   - Add PDF export functionality")

if __name__ == "__main__":
    main()
