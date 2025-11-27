#!/usr/bin/env python3
"""
Test script for People Section API endpoints
Run this to verify all endpoints are working correctly
"""

import requests
import json
import sys
from datetime import datetime, timedelta

BASE_URL = 'http://localhost:5002'  # Adjust if your backend runs on different port

def test_endpoint(name, method, url, data=None, expected_status=200):
    """Test an API endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    print(f"Method: {method}")
    print(f"URL: {url}")
    
    try:
        if method == 'GET':
            response = requests.get(url, cookies={'session': 'test'})
        elif method == 'POST':
            response = requests.post(url, json=data, cookies={'session': 'test'})
        elif method == 'PUT':
            response = requests.put(url, json=data, cookies={'session': 'test'})
        elif method == 'DELETE':
            response = requests.delete(url, cookies={'session': 'test'})
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == expected_status:
            print(f"✅ PASSED - Status {response.status_code}")
            try:
                result = response.json()
                print(f"Response keys: {list(result.keys())}")
                if 'persons' in result:
                    print(f"  - Found {len(result['persons'])} persons")
                if 'families' in result:
                    print(f"  - Found {len(result['families'])} families")
                if 'cases' in result:
                    print(f"  - Found {len(result['cases'])} cases")
                if 'new_christians' in result:
                    print(f"  - Found {len(result['new_christians'])} new Christians")
                if 'missing_streaks' in result:
                    print(f"  - Found {len(result['missing_streaks'])} missing streaks")
                return True
            except:
                print(f"Response: {response.text[:200]}")
                return True
        else:
            print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ FAILED - Could not connect to {BASE_URL}")
        print("   Make sure the backend server is running!")
        return False
    except Exception as e:
        print(f"❌ FAILED - Error: {e}")
        return False

def main():
    print("="*60)
    print("People Section API Endpoint Tests")
    print("="*60)
    print(f"Testing against: {BASE_URL}")
    print("\nNote: These tests require authentication.")
    print("You may need to log in first or adjust the session cookie.")
    
    results = []
    
    # Test 1: Enhanced GET /api/persons
    results.append((
        "GET /api/persons (enhanced)",
        test_endpoint(
            "GET /api/persons (enhanced)",
            "GET",
            f"{BASE_URL}/api/persons"
        )
    ))
    
    # Test 2: GET /api/persons with new_people filter
    results.append((
        "GET /api/persons?new_people=true",
        test_endpoint(
            "GET /api/persons?new_people=true",
            "GET",
            f"{BASE_URL}/api/persons?new_people=true"
        )
    ))
    
    # Test 3: GET /api/persons with new_christians filter
    results.append((
        "GET /api/persons?new_christians=true",
        test_endpoint(
            "GET /api/persons?new_christians=true",
            "GET",
            f"{BASE_URL}/api/persons?new_christians=true"
        )
    ))
    
    # Test 4: GET /api/people/families
    results.append((
        "GET /api/people/families",
        test_endpoint(
            "GET /api/people/families",
            "GET",
            f"{BASE_URL}/api/people/families"
        )
    ))
    
    # Test 5: GET /api/heartbeat/dashboard
    results.append((
        "GET /api/heartbeat/dashboard",
        test_endpoint(
            "GET /api/heartbeat/dashboard",
            "GET",
            f"{BASE_URL}/api/heartbeat/dashboard"
        )
    ))
    
    # Test 6: GET /api/pastoral-care/cases
    results.append((
        "GET /api/pastoral-care/cases",
        test_endpoint(
            "GET /api/pastoral-care/cases",
            "GET",
            f"{BASE_URL}/api/pastoral-care/cases"
        )
    ))
    
    # Test 7: GET /api/people/new-christians
    results.append((
        "GET /api/people/new-christians",
        test_endpoint(
            "GET /api/people/new-christians",
            "GET",
            f"{BASE_URL}/api/people/new-christians"
        )
    ))
    
    # Test 8: GET /api/attendance/patterns
    results.append((
        "GET /api/attendance/patterns",
        test_endpoint(
            "GET /api/attendance/patterns",
            "GET",
            f"{BASE_URL}/api/attendance/patterns"
        )
    ))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())

