#!/usr/bin/env python3

import requests
import sys

def test_modsecurity(url):
    """Test basic ModSecurity functionality"""
    
    # Test SQL Injection
    sql_tests = [
        "' OR '1'='1",
        "' OR 1=1--",
        "'; DROP TABLE users;--"
    ]
    
    # Test XSS
    xss_tests = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')"
    ]
    
    # Test LFI
    lfi_tests = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts"
    ]
    
    blocked = 0
    total = 0
    
    print(f"Testing ModSecurity at: {url}")
    print("=" * 50)
    
    # Test SQL Injection
    print("\nTesting SQL Injection:")
    for payload in sql_tests:
        total += 1
        try:
            response = requests.get(url, params={'id': payload}, timeout=10)
            if response.status_code in [403, 406]:
                print(f"✅ BLOCKED: {payload[:30]}...")
                blocked += 1
            else:
                print(f"⚠️  ALLOWED: {payload[:30]}...")
        except Exception as e:
            print(f"❌ ERROR: {payload[:30]}... - {e}")
    
    # Test XSS
    print("\nTesting XSS:")
    for payload in xss_tests:
        total += 1
        try:
            response = requests.get(url, params={'q': payload}, timeout=10)
            if response.status_code in [403, 406]:
                print(f"✅ BLOCKED: {payload[:30]}...")
                blocked += 1
            else:
                print(f"⚠️  ALLOWED: {payload[:30]}...")
        except Exception as e:
            print(f"❌ ERROR: {payload[:30]}... - {e}")
    
    # Test LFI
    print("\nTesting LFI:")
    for payload in lfi_tests:
        total += 1
        try:
            response = requests.get(url, params={'file': payload}, timeout=10)
            if response.status_code in [403, 406]:
                print(f"✅ BLOCKED: {payload[:30]}...")
                blocked += 1
            else:
                print(f"⚠️  ALLOWED: {payload[:30]}...")
        except Exception as e:
            print(f"❌ ERROR: {payload[:30]}... - {e}")
    
    print("\n" + "=" * 50)
    print(f"RESULTS: {blocked}/{total} attacks blocked")
    protection_rate = (blocked / total) * 100 if total > 0 else 0
    print(f"Protection Rate: {protection_rate:.1f}%")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_modsec.py <url>")
        print("Example: python test_modsec.py http://localhost")
        sys.exit(1)
    
    test_modsecurity(sys.argv[1]) 