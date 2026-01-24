#!/usr/bin/env python3
"""
Quick test script to verify login works
"""

import os
import requests
import json

LOGIN_URL = "https://vtuapi.internyet.in/api/v1/auth/login"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-GB,en;q=0.6",
    "origin": "https://vtu.internyet.in",
    "referer": "https://vtu.internyet.in/",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

# Get credentials
email = os.getenv("VTU_EMAIL") or input("Enter VTU email: ")
password = os.getenv("VTU_PASSWORD") or input("Enter VTU password: ")

print(f"\nTesting login for: {email}")
print("=" * 70)

try:
    resp = requests.post(
        LOGIN_URL,
        json={"email": email, "password": password},
        headers=HEADERS,
        timeout=30
    )
    
    print(f"Status Code: {resp.status_code}")
    print(f"Response Headers:")
    for key, value in resp.headers.items():
        if 'cookie' in key.lower() or 'set-cookie' in key.lower():
            print(f"  {key}: {value[:100]}...")
    
    print(f"\nResponse Body:")
    try:
        data = resp.json()
        print(json.dumps(data, indent=2))
    except:
        print(resp.text[:500])
    
    print(f"\nCookies from response:")
    for cookie in resp.cookies:
        print(f"  {cookie.name} = {cookie.value[:50]}...")
    
    if resp.status_code == 200:
        cookies_dict = {c.name: c.value for c in resp.cookies}
        if 'access_token' in cookies_dict:
            print("\n✓ Login successful! access_token found in cookies.")
        else:
            print("\n⚠ Login may have succeeded but access_token not in cookies.")
            print(f"  Available cookies: {list(cookies_dict.keys())}")
    else:
        print("\n✗ Login failed")
        
except Exception as e:
    print(f"\n✗ Error: {e}")

