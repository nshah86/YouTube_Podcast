"""
Script to fix production readiness issues
"""
import os
import sys

def check_and_fix_env():
    """Check and fix .env file issues"""
    env_file = '.env'
    env_example = '.env.example'
    
    print("=" * 60)
    print("Production Readiness Fix Script")
    print("=" * 60)
    
    # Check if .env exists
    if not os.path.exists(env_file):
        print(f"❌ {env_file} not found!")
        if os.path.exists(env_example):
            print(f"📋 Copy {env_example} to {env_file} and fill in values")
        return False
    
    print(f"✅ {env_file} exists")
    
    # Read .env
    with open(env_file, 'r') as f:
        content = f.read()
    
    issues = []
    fixes = []
    
    # Check for required variables
    required_vars = {
        'SECRET_KEY': 'SECRET_KEY=your-secret-key-here-change-in-production',
        'OPENAI_API_KEY': 'OPENAI_API_KEY=your-openai-api-key',
        'REACT_APP_SUPABASE_URL': 'REACT_APP_SUPABASE_URL=https://your-project.supabase.co',
        'REACT_APP_SUPABASE_ANON_KEY': 'REACT_APP_SUPABASE_ANON_KEY=your-anon-key',
    }
    
    optional_vars = {
        'STRIPE_SECRET_KEY': 'STRIPE_SECRET_KEY=sk_test_your-key',
        'STRIPE_WEBHOOK_SECRET': 'STRIPE_WEBHOOK_SECRET=whsec_your-secret',
        'STRIPE_PRICE_PLUS': 'STRIPE_PRICE_PLUS=price_xxxxx',
        'STRIPE_PRICE_PRO': 'STRIPE_PRICE_PRO=price_xxxxx',
    }
    
    # Check required vars
    for var, default in required_vars.items():
        if var not in content:
            issues.append(f"Missing required: {var}")
            fixes.append(default)
        else:
            print(f"✅ {var} is set")
    
    # Check optional vars
    for var, default in optional_vars.items():
        if var not in content:
            print(f"⚠️  Optional: {var} not set (needed for payments)")
        else:
            print(f"✅ {var} is set")
    
    # Check for VITE variables (wrong naming)
    if 'VITE_SUPABASE_URL' in content:
        issues.append("Found VITE_SUPABASE_URL (should be REACT_APP_SUPABASE_URL)")
    if 'VITE_SUPABASE_ANON_KEY' in content:
        issues.append("Found VITE_SUPABASE_ANON_KEY (should be REACT_APP_SUPABASE_ANON_KEY)")
    
    if issues:
        print("\n❌ Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        print("\n📋 Add these to your .env file:")
        for fix in fixes:
            print(f"  {fix}")
        return False
    else:
        print("\n✅ All required environment variables are set!")
        return True

def check_files():
    """Check if required files exist"""
    print("\n" + "=" * 60)
    print("Checking Required Files")
    print("=" * 60)
    
    required_files = [
        'app.py',
        'requirements.txt',
        'config.py',
        'database_schema.sql',
        'templates/base.html',
        'templates/index.html',
        'static/css/style.css',
        'static/js/main.js'
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} MISSING")
            all_exist = False
    
    return all_exist

def check_dependencies():
    """Check if Python dependencies are installed"""
    print("\n" + "=" * 60)
    print("Checking Dependencies")
    print("=" * 60)
    
    try:
        import flask
        print("✅ Flask installed")
    except ImportError:
        print("❌ Flask NOT installed - run: pip install -r requirements.txt")
        return False
    
    try:
        import supabase
        print("✅ Supabase installed")
    except ImportError:
        print("❌ Supabase NOT installed - run: pip install -r requirements.txt")
        return False
    
    try:
        import stripe
        print("✅ Stripe installed")
    except ImportError:
        print("⚠️  Stripe NOT installed (optional for payments)")
    
    try:
        from flask_wtf import CSRFProtect
        print("✅ Flask-WTF installed (CSRF protection)")
    except ImportError:
        print("❌ Flask-WTF NOT installed - run: pip install flask-wtf")
        return False
    
    return True

def main():
    """Main function"""
    print("\n🔍 Running Production Readiness Checks...\n")
    
    files_ok = check_files()
    env_ok = check_and_fix_env()
    deps_ok = check_dependencies()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if files_ok and env_ok and deps_ok:
        print("✅ All checks passed! Application is ready.")
        print("\n📋 Next steps:")
        print("  1. Run database_schema.sql in Supabase")
        print("  2. Run database_schema_payments.sql in Supabase")
        print("  3. Test the application: python start.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        if not deps_ok:
            print("\n💡 Install dependencies: pip install -r requirements.txt")
        if not env_ok:
            print("\n💡 Fix .env file using .env.example as template")

if __name__ == '__main__':
    main()

