#!/usr/bin/env python3
"""
Setup and Test Script for ModSecurity Testing
This script helps set up the test environment and run tests
"""

import subprocess
import time
import sys
import os
import threading
import requests

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "requests"])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")
        return False

def start_test_server():
    """Start the Flask test server in background"""
    print("🚀 Starting test server...")
    try:
        # Start the server in a separate process
        process = subprocess.Popen([sys.executable, "test_server.py"], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Test if server is running
        try:
            response = requests.get("http://localhost:5000", timeout=5)
            print("✅ Test server is running on http://localhost:5000")
            return process
        except requests.RequestException:
            print("❌ Test server failed to start")
            process.terminate()
            return None
            
    except Exception as e:
        print(f"❌ Error starting test server: {e}")
        return None

def test_without_modsecurity():
    """Test the server without ModSecurity to establish baseline"""
    print("\n🧪 Testing server WITHOUT ModSecurity (baseline)...")
    print("=" * 60)
    
    # Import and run our test
    try:
        from comprehensive_test import ModSecurityTester
        tester = ModSecurityTester("http://localhost:5000")
        tester.run_comprehensive_tests()
        return tester.results
    except Exception as e:
        print(f"❌ Error running baseline tests: {e}")
        return None

def show_modsecurity_instructions():
    """Show instructions for setting up ModSecurity"""
    print("\n" + "=" * 80)
    print("🔒 NEXT STEPS: Setting up ModSecurity")
    print("=" * 80)
    print("""
To test ModSecurity protection, you need to:

1. Install ModSecurity with Nginx:
   - Ubuntu/Debian: apt-get install libmodsecurity3 nginx-module-modsecurity
   - CentOS/RHEL: yum install modsecurity nginx-module-modsecurity

2. Configure Nginx to proxy to our test server:
   Create /etc/nginx/sites-available/modsecurity-test:
   
   server {
       listen 80;
       server_name localhost;
       
       # Enable ModSecurity
       modsecurity on;
       modsecurity_rules_file /etc/nginx/modsecurity/modsecurity.conf;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }

3. Enable the site:
   ln -s /etc/nginx/sites-available/modsecurity-test /etc/nginx/sites-enabled/
   
4. Restart Nginx:
   systemctl restart nginx

5. Test ModSecurity protection:
   python comprehensive_test.py http://localhost
   
6. Compare results with baseline to see what ModSecurity blocked!
""")

def run_quick_test():
    """Run a quick test without full setup"""
    print("🚀 Running Quick ModSecurity Test")
    print("=" * 60)
    
    # Check if we can test an existing URL
    test_url = input("Enter the URL to test (or press Enter for localhost:5000): ").strip()
    if not test_url:
        test_url = "http://localhost:5000"
    
    print(f"🎯 Testing: {test_url}")
    
    try:
        from test_modsec import test_modsecurity
        test_modsecurity(test_url)
    except Exception as e:
        print(f"❌ Error running tests: {e}")

def main():
    print("🔒 ModSecurity Test Suite Setup")
    print("=" * 60)
    
    # Check what the user wants to do
    print("Choose an option:")
    print("1. Full setup (install requirements, start test server, run baseline)")
    print("2. Quick test (test existing URL)")
    print("3. Show ModSecurity setup instructions")
    print("4. Start test server only")
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == "1":
        # Full setup
        if not install_requirements():
            return
        
        server_process = start_test_server()
        if not server_process:
            return
        
        try:
            # Run baseline test
            baseline_results = test_without_modsecurity()
            
            if baseline_results:
                allowed_count = len(baseline_results['allowed'])
                print(f"\n📊 Baseline: {allowed_count} attacks reached the server")
                print("   (This shows what would happen WITHOUT ModSecurity)")
            
            show_modsecurity_instructions()
            
            input("\nPress Enter to stop the test server...")
            
        finally:
            if server_process:
                server_process.terminate()
                print("🛑 Test server stopped")
    
    elif choice == "2":
        run_quick_test()
    
    elif choice == "3":
        show_modsecurity_instructions()
    
    elif choice == "4":
        if not install_requirements():
            return
        
        server_process = start_test_server()
        if server_process:
            print("✅ Test server is running")
            print("🌐 Visit http://localhost:5000 in your browser")
            print("📋 Use the web interface to test attacks manually")
            input("Press Enter to stop the server...")
            server_process.terminate()
            print("🛑 Test server stopped")
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main() 