#!/usr/bin/env python3
"""
Test script to verify the application works without Clerk dependencies
"""

import sys
import os

def test_imports():
    """Test that all imports work without Clerk"""
    print("🧪 Testing imports without Clerk...")
    
    try:
        # Test main.py imports
        sys.path.insert(0, os.getcwd())
        
        print("   Testing auth system...")
        from auth import auth_manager, login_required
        print("   ✅ Local auth system imported successfully")
        
        print("   Testing auth routes...")
        from auth_routes import auth_bp
        print("   ✅ Auth routes imported successfully")
        
        print("   Testing main app...")
        # Just import, don't run
        import main
        print("   ✅ Main app imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_auth_system():
    """Test the local authentication system"""
    print("\n🔐 Testing local authentication system...")
    
    try:
        from auth import auth_manager
        
        # Test basic auth manager functionality
        print("   Testing auth manager initialization...")
        if hasattr(auth_manager, 'db_path'):
            print(f"   ✅ Auth manager initialized with database: {auth_manager.db_path}")
        else:
            print("   ❌ Auth manager not properly initialized")
            return False
            
        # Test if we can check for existing users
        print("   Testing user lookup...")
        # Try to authenticate with test credentials (this tests user lookup)
        test_user, error = auth_manager.authenticate_user('admin@bhashai.com', 'admin123')
        if test_user:
            print(f"   ✅ Found test user: {test_user.get('email', 'Unknown')}")
        else:
            print("   ⚠️  No test user found or wrong password (this is fine for fresh installs)")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Auth system error: {e}")
        return False

def test_no_clerk_references():
    """Check that no Clerk imports remain"""
    print("\n🚫 Checking for remaining Clerk references...")
    
    try:
        import main
        
        # Check if any Clerk-related attributes exist
        clerk_refs = []
        
        for attr in dir(main):
            if 'clerk' in attr.lower():
                clerk_refs.append(attr)
        
        if clerk_refs:
            print(f"   ⚠️  Found possible Clerk references: {clerk_refs}")
        else:
            print("   ✅ No Clerk references found in main module")
            
        # Try to import Clerk (should fail)
        try:
            import clerk_auth
            print("   ❌ clerk_auth module still exists!")
            return False
        except ImportError:
            print("   ✅ clerk_auth module properly removed")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking Clerk references: {e}")
        return False

def test_flask_app_creation():
    """Test that Flask app can be created"""
    print("\n🌐 Testing Flask app creation...")
    
    try:
        # Set environment variable to avoid actual server start
        os.environ['TESTING'] = 'true'
        
        from main import app
        
        if app:
            print("   ✅ Flask app created successfully")
            print(f"   ✅ App name: {app.name}")
            
            # Test that auth blueprint is registered
            blueprint_names = [bp.name for bp in app.blueprints.values()]
            if 'auth' in blueprint_names:
                print("   ✅ Auth blueprint registered")
            else:
                print("   ❌ Auth blueprint not found")
                return False
                
            return True
        else:
            print("   ❌ Flask app not created")
            return False
            
    except Exception as e:
        print(f"   ❌ Flask app creation error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing BhashAI without Clerk dependencies")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_auth_system,
        test_no_clerk_references,
        test_flask_app_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print(f"\n❌ Test failed: {test.__name__}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Application is ready without Clerk.")
        print("\n📋 Next steps:")
        print("1. Start the application: python main.py")
        print("2. Visit: http://localhost:5000/login")
        print("3. Use demo credentials from CLERK_REMOVAL_SUMMARY.md")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 