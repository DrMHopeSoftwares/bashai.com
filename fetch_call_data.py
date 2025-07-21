#!/usr/bin/env python3
"""
Fetch call data and recordings from Bolna API
"""

import os
import requests
import json
from bolna_integration import BolnaAPI

def fetch_call_data():
    """Fetch call data and recordings"""
    try:
        # Use admin settings
        admin_user_data = {
            'sender_phone': '+918085315398',
            'bolna_agent_id': '15554373-b8e1-4b00-8c25-c4742dc8e480'
        }

        print("🔍 Initializing Bolna API...")
        bolna_api = BolnaAPI(admin_user_data=admin_user_data)

        # Call execution IDs from server logs
        execution_ids = [
            'cedfecea-2b48-435f-8ece-99a98b81e0e6',  # Call 1 at 11:35:17
            'bb6a74d8-6361-40b2-8734-ab7272c5deab'   # Call 2 at 11:36:48
        ]

        print(f"📞 Fetching data for {len(execution_ids)} calls...")

        for i, execution_id in enumerate(execution_ids, 1):
            print(f"\n🔍 Call {i}: {execution_id}")
            print(f"🔗 Execution ID: {execution_id}")

            try:
                # Method 1: Get call status using correct endpoint
                print("📊 Fetching call status...")
                call_status = bolna_api.get_call_status(execution_id)
                print(f"✅ Status Response: {json.dumps(call_status, indent=2)}")

            except Exception as e:
                print(f"❌ Call status failed: {e}")

            try:
                # Method 2: Try different call endpoints
                endpoints_to_try = [
                    f'/call/{execution_id}',
                    f'/calls/{execution_id}',
                    f'/run/{execution_id}',
                    f'/runs/{execution_id}',
                    f'/execution/{execution_id}',
                    f'/executions/{execution_id}'
                ]

                for endpoint in endpoints_to_try:
                    try:
                        print(f"🔍 Trying endpoint: {endpoint}")
                        response = bolna_api._make_request('GET', endpoint)
                        print(f"✅ {endpoint} Response: {json.dumps(response, indent=2)}")
                        break
                    except Exception as e:
                        print(f"⚠️ {endpoint} failed: {e}")

            except Exception as e:
                print(f"❌ All call detail endpoints failed: {e}")

        # Try to list all calls with different endpoints
        print(f"\n📋 Fetching all recent calls...")
        list_endpoints = ['/calls', '/call', '/runs', '/run', '/executions', '/execution']

        for endpoint in list_endpoints:
            try:
                print(f"🔍 Trying list endpoint: {endpoint}")
                all_calls = bolna_api._make_request('GET', endpoint)
                print(f"✅ {endpoint} Response: {json.dumps(all_calls, indent=2)}")
                break
            except Exception as e:
                print(f"⚠️ {endpoint} failed: {e}")

    except Exception as e:
        print(f"❌ Fetch call data failed: {e}")

if __name__ == "__main__":
    fetch_call_data()
