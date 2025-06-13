#!/usr/bin/env python3
"""
Comprehensive ModSecurity Test Suite
"""

import requests
import json
import time
import sys

class ModSecurityTester:
    def __init__(self, target_url, timeout=10):
        self.target_url = target_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.results = {
            'blocked': [],
            'allowed': [],
            'errors': []
        }
    
    def test_payload(self, test_name, method='GET', path='/', headers=None, data=None, params=None):
        """Test a single payload"""
        url = f"{self.target_url}{path}"
        
        default_headers = {
            'User-Agent': 'ModSecurity-Test-Suite/1.0',
            'Accept': '*/*'
        }
        
        if headers:
            default_headers.update(headers)
            
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, headers=default_headers, 
                                          timeout=self.timeout, allow_redirects=False)
            elif method.upper() == 'POST':
                response = self.session.post(url, data=data, headers=default_headers,
                                           timeout=self.timeout, allow_redirects=False)
            
            # Check if blocked
            if response.status_code in [403, 406, 501, 502, 503]:
                self.results['blocked'].append({
                    'test': test_name,
                    'status': response.status_code
                })
                print(f"✅ BLOCKED: {test_name}")
                return True
            else:
                self.results['allowed'].append({
                    'test': test_name,
                    'status': response.status_code
                })
                print(f"⚠️  ALLOWED: {test_name}")
                return False
                
        except Exception as e:
            self.results['errors'].append({
                'test': test_name,
                'error': str(e)
            })
            print(f"❌ ERROR: {test_name} - {str(e)}")
            return None
    
    def run_comprehensive_tests(self):
        """Run comprehensive tests"""
        print(f"🚀 Starting Comprehensive ModSecurity Tests on {self.target_url}")
        print("=" * 60)
        
        # SQL Injection Tests
        print("\n📋 Testing SQL Injection...")
        sql_tests = [
            "' OR '1'='1",
            "' OR 1=1--",
            "' UNION SELECT 1,2,3--",
            "'; DROP TABLE users;--",
            "' AND SLEEP(5)--"
        ]
        
        for payload in sql_tests:
            self.test_payload(f"SQL: {payload[:20]}...", 'GET', '/', params={'id': payload})
            time.sleep(0.1)
        
        # XSS Tests
        print("\n📋 Testing XSS...")
        xss_tests = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(1)'></iframe>"
        ]
        
        for payload in xss_tests:
            self.test_payload(f"XSS: {payload[:20]}...", 'GET', '/', params={'q': payload})
            time.sleep(0.1)
        
        # LFI Tests
        print("\n📋 Testing LFI...")
        lfi_tests = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "/proc/version",
            "/var/log/apache2/access.log"
        ]
        
        for payload in lfi_tests:
            self.test_payload(f"LFI: {payload[:20]}...", 'GET', '/', params={'file': payload})
            time.sleep(0.1)
        
        # Command Injection Tests
        print("\n📋 Testing Command Injection...")
        cmd_tests = [
            "; ls -la",
            "| whoami",
            "&& cat /etc/passwd",
            "`id`",
            "$(whoami)"
        ]
        
        for payload in cmd_tests:
            self.test_payload(f"CMD: {payload[:20]}...", 'GET', '/', params={'cmd': payload})
            self.test_payload(f"CMD POST: {payload[:20]}...", 'POST', '/', data={'command': payload})
            time.sleep(0.1)
        
        # Scanner Detection Tests
        print("\n📋 Testing Scanner Detection...")
        scanners = [
            "sqlmap/1.0",
            "Nessus",
            "Nikto",
            "OWASP ZAP"
        ]
        
        for scanner in scanners:
            self.test_payload(f"Scanner: {scanner}", 'GET', '/', headers={'User-Agent': scanner})
            time.sleep(0.1)
        
        # Protocol Tests
        print("\n📋 Testing Protocol Attacks...")
        self.test_payload("Header Injection", 'GET', '/', headers={'X-Test': 'value\r\nInjected: header'})
        self.test_payload("Large Header", 'GET', '/', headers={'X-Large': 'A' * 8192})
        
        self.print_results()
    
    def print_results(self):
        """Print results summary"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS")
        print("=" * 60)
        
        total = len(self.results['blocked']) + len(self.results['allowed']) + len(self.results['errors'])
        blocked = len(self.results['blocked'])
        allowed = len(self.results['allowed'])
        errors = len(self.results['errors'])
        
        print(f"Total Tests: {total}")
        print(f"Blocked: {blocked}")
        print(f"Allowed: {allowed}")
        print(f"Errors: {errors}")
        
        if total > 0:
            protection_rate = (blocked / (blocked + allowed)) * 100 if (blocked + allowed) > 0 else 0
            print(f"Protection Rate: {protection_rate:.1f}%")
            
            if protection_rate >= 80:
                print("🟢 EXCELLENT Protection!")
            elif protection_rate >= 60:
                print("🟡 GOOD Protection")
            else:
                print("🔴 NEEDS IMPROVEMENT")

def main():
    if len(sys.argv) != 2:
        print("Usage: python comprehensive_test.py <url>")
        print("Example: python comprehensive_test.py http://localhost")
        sys.exit(1)
    
    url = sys.argv[1]
    print("⚠️  WARNING: This sends attack payloads!")
    print("Only test systems you own or have permission to test.")
    
    response = input("Continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Cancelled.")
        return
    
    tester = ModSecurityTester(url)
    tester.run_comprehensive_tests()

if __name__ == "__main__":
    main() 