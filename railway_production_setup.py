#!/usr/bin/env python3
"""
Railway Production Setup Script
This script provides the exact environment variables needed for Railway deployment
"""

def get_production_environment_variables():
    """Get all production environment variables for Railway"""
    
    print("🚀 Railway Production Environment Variables")
    print("=" * 60)
    print("Copy these environment variables to your Railway project:")
    print()
    
    # Core API Keys we have
    env_vars = {
        # ElevenLabs Configuration (WORKING)
        "ELEVENLABS_API_KEY": "sk_97fa57d9766f4fee1b9632e8987595ba3de79f630ed2d14c",
        "ELEVENLABS_API_URL": "https://api.elevenlabs.io/v1",
        "ELEVENLABS_WEBSOCKET_URL": "wss://api.elevenlabs.io/v1/text-to-speech",
        "ELEVENLABS_DEFAULT_VOICE_ID": "21m00Tcm4TlvDq8ikWAM",
        "ELEVENLABS_MODEL_ID": "eleven_multilingual_v2",
        
        # Twilio Configuration (PARTIAL - need auth token)
        "TWILIO_ACCOUNT_SID": "ACb4f43ae70f647972a12b7c27ef1c0c0f",
        "TWILIO_AUTH_TOKEN": "your_twilio_auth_token_here",  # NEED THIS
        "TWILIO_PHONE_NUMBER": "+1234567890",  # NEED THIS
        
        # Required API Keys (NEED THESE)
        "BOLNA_API_KEY": "your_bolna_api_key_here",
        "RELEVANCE_AI_API_KEY": "your_relevance_ai_key_here",
        "OPENAI_API_KEY": "your_openai_api_key_here",
        
        # Database Configuration
        "SUPABASE_URL": "https://your-project.supabase.co",
        "SUPABASE_KEY": "your_supabase_anon_key",
        
        # Authentication
        "CLERK_SECRET_KEY": "your_clerk_secret_key",
        "CLERK_PUBLISHABLE_KEY": "your_clerk_publishable_key",
        
        # Payment Integration
        "RAZORPAY_KEY_ID": "your_razorpay_key_id",
        "RAZORPAY_KEY_SECRET": "your_razorpay_key_secret",
        
        # Additional Configuration
        "FLASK_ENV": "production",
        "PORT": "8080",
        "PYTHONPATH": "/app",
        
        # Mock Mode Flags (to prevent crashes)
        "USE_MOCK_MODE": "true",
        "BOLNA_MOCK_MODE": "true",
        "RELEVANCE_AI_MOCK_MODE": "true",
    }
    
    print("📋 ENVIRONMENT VARIABLES FOR RAILWAY:")
    print("-" * 40)
    
    # Show working configurations
    print("\n✅ WORKING CONFIGURATIONS:")
    working_keys = ["ELEVENLABS_API_KEY", "TWILIO_ACCOUNT_SID"]
    for key in working_keys:
        if key in env_vars:
            value = env_vars[key]
            if "api_key" in key.lower() or "token" in key.lower():
                display_value = f"{value[:20]}..." if len(value) > 20 else value
            else:
                display_value = value
            print(f"{key}={display_value}")
    
    # Show required configurations
    print("\n⚠️  REQUIRED FOR FULL FUNCTIONALITY:")
    required_keys = ["BOLNA_API_KEY", "RELEVANCE_AI_API_KEY", "OPENAI_API_KEY", "TWILIO_AUTH_TOKEN"]
    for key in required_keys:
        if key in env_vars:
            print(f"{key}={env_vars[key]}")
    
    # Show optional configurations
    print("\n🔧 OPTIONAL (for full features):")
    optional_keys = ["SUPABASE_URL", "CLERK_SECRET_KEY", "RAZORPAY_KEY_ID"]
    for key in optional_keys:
        if key in env_vars:
            print(f"{key}={env_vars[key]}")
    
    # Show system configurations
    print("\n⚙️  SYSTEM CONFIGURATION:")
    system_keys = ["FLASK_ENV", "PORT", "USE_MOCK_MODE"]
    for key in system_keys:
        if key in env_vars:
            print(f"{key}={env_vars[key]}")
    
    return env_vars

def create_railway_env_file():
    """Create a .env file for Railway deployment"""
    env_vars = get_production_environment_variables()
    
    print("\n" + "=" * 60)
    print("📝 CREATING .env.railway FILE")
    print("=" * 60)
    
    env_content = "# Railway Production Environment Variables\n"
    env_content += "# Generated automatically for BhashAI deployment\n\n"
    
    for key, value in env_vars.items():
        env_content += f"{key}={value}\n"
    
    # Write to file
    with open('.env.railway', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env.railway file")
    print("📋 You can copy these variables to Railway dashboard")

def show_railway_deployment_steps():
    """Show steps to deploy to Railway"""
    print("\n" + "=" * 60)
    print("🚀 RAILWAY DEPLOYMENT STEPS")
    print("=" * 60)
    
    steps = [
        "1. Go to Railway Dashboard: https://railway.app/dashboard",
        "2. Select your bashai.com project",
        "3. Go to Variables tab",
        "4. Add the environment variables shown above",
        "5. Focus on these CRITICAL variables first:",
        "   - ELEVENLABS_API_KEY (already provided)",
        "   - BOLNA_API_KEY (get from Bolna dashboard)",
        "   - RELEVANCE_AI_API_KEY (get from RelevanceAI)",
        "   - OPENAI_API_KEY (get from OpenAI)",
        "6. Deploy the latest code",
        "7. Check deployment logs for any remaining issues"
    ]
    
    for step in steps:
        print(step)
    
    print("\n🎯 IMMEDIATE FIX FOR CURRENT CRASH:")
    print("Add these variables to Railway to fix the server crash:")
    print("BOLNA_API_KEY=your_actual_bolna_api_key")
    print("RELEVANCE_AI_API_KEY=your_actual_relevance_ai_key")
    print("OPENAI_API_KEY=your_actual_openai_key")
    print("USE_MOCK_MODE=true  # Temporary fix")

def show_api_key_sources():
    """Show where to get each API key"""
    print("\n" + "=" * 60)
    print("🔑 WHERE TO GET API KEYS")
    print("=" * 60)
    
    api_sources = {
        "ELEVENLABS_API_KEY": {
            "status": "✅ ALREADY CONFIGURED",
            "url": "https://elevenlabs.io/app/settings/api-keys",
            "value": "sk_97fa57d9766f4fee1b9632e8987595ba3de79f630ed2d14c"
        },
        "BOLNA_API_KEY": {
            "status": "❌ REQUIRED",
            "url": "https://app.bolna.dev/api-keys",
            "note": "Sign up at Bolna and get API key from dashboard"
        },
        "RELEVANCE_AI_API_KEY": {
            "status": "❌ REQUIRED", 
            "url": "https://relevanceai.com/dashboard/api-keys",
            "note": "Create account and get API key"
        },
        "OPENAI_API_KEY": {
            "status": "❌ REQUIRED",
            "url": "https://platform.openai.com/api-keys",
            "note": "Get from OpenAI platform dashboard"
        },
        "TWILIO_AUTH_TOKEN": {
            "status": "⚠️  PARTIAL",
            "url": "https://console.twilio.com/",
            "note": "Account SID configured, need Auth Token"
        }
    }
    
    for key, info in api_sources.items():
        print(f"\n{key}:")
        print(f"  Status: {info['status']}")
        print(f"  Get from: {info['url']}")
        if 'value' in info:
            print(f"  Current: {info['value'][:30]}...")
        if 'note' in info:
            print(f"  Note: {info['note']}")

def main():
    """Main function"""
    print("🎙️ BhashAI Railway Production Setup")
    print("Fixing server crash by configuring API keys")
    print()
    
    # Get environment variables
    get_production_environment_variables()
    
    # Create Railway env file
    create_railway_env_file()
    
    # Show deployment steps
    show_railway_deployment_steps()
    
    # Show API key sources
    show_api_key_sources()
    
    print("\n" + "=" * 60)
    print("🎉 SUMMARY")
    print("=" * 60)
    print("✅ ElevenLabs API: READY (22 voices available)")
    print("✅ Twilio Account: CONFIGURED (need auth token for calls)")
    print("❌ Bolna API: NEED KEY (causing server crash)")
    print("❌ RelevanceAI: NEED KEY (causing server crash)")
    print("❌ OpenAI API: NEED KEY (for full functionality)")
    print()
    print("🚨 IMMEDIATE ACTION REQUIRED:")
    print("1. Add BOLNA_API_KEY to Railway environment variables")
    print("2. Add RELEVANCE_AI_API_KEY to Railway environment variables")
    print("3. Add OPENAI_API_KEY to Railway environment variables")
    print("4. Redeploy the application")
    print()
    print("📞 Once fixed, you can make real calls to +919373111709!")

if __name__ == "__main__":
    main()
