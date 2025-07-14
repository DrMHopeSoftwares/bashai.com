#!/usr/bin/env python3
"""
Railway deployment status checker
"""

import requests
import time

def check_url(url, description):
    """Check if a URL is accessible"""
    print(f"\n🔍 Checking {description}: {url}")
    try:
        response = requests.get(url, timeout=10, verify=True)
        print(f"   ✅ Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ SSL: Valid")
            if 'json' in response.headers.get('content-type', ''):
                print(f"   📦 Response: {response.json()}")
        return True
    except requests.exceptions.SSLError as e:
        print(f"   ❌ SSL Error: {str(e)}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection Error: Cannot reach server")
        return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def main():
    print("🚂 Railway Deployment Status Check")
    print("=" * 60)
    
    # Check different endpoints
    domains = [
        ("https://bhashai.com/health", "Production Domain - Health"),
        ("https://www.bhashai.com/health", "WWW Domain - Health"),
        ("https://bhashai.com/", "Production Domain - Root"),
        ("https://bhashai.com/simple-admin.html", "Admin Page"),
    ]
    
    working_count = 0
    for url, desc in domains:
        if check_url(url, desc):
            working_count += 1
        time.sleep(1)  # Be nice to the server
    
    print("\n" + "=" * 60)
    print(f"📊 Summary: {working_count}/{len(domains)} endpoints working")
    
    if working_count == 0:
        print("\n⚠️  No endpoints working. Check:")
        print("   1. Railway dashboard → Settings → Networking")
        print("   2. Look for 'Setup Complete' status")
        print("   3. Try the Railway-generated URL (*.up.railway.app)")
    elif working_count < len(domains):
        print("\n⚠️  Some endpoints not working. SSL might be propagating.")
    else:
        print("\n✅ All endpoints working! Deployment successful!")

if __name__ == "__main__":
    main()