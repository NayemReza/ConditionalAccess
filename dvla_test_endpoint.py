#!/usr/bin/env python3
"""
Test DVLA API endpoints to understand structure
Then attempt real lookup
"""

import requests
import json


def test_dvla_api_structure():
    """
    REFLECTION: Try the DVLA API endpoints to see what happens without a key
    Test both UAT and production
    Document the response structure
    """
    print("\n🧪 TESTING DVLA API ENDPOINTS")
    print("=" * 70)
    print("Strategy: Test official endpoints to understand requirements\n")

    endpoints = [
        {
            "name": "DVLA UAT (Test Environment)",
            "url": "https://uat.driver-vehicle-licensing.api.gov.uk/vehicle-enquiry/v1/vehicles",
            "vrn": "AA19AAA"  # Known test VRN
        },
        {
            "name": "DVLA Production",
            "url": "https://driver-vehicle-licensing.api.gov.uk/vehicle-enquiry/v1/vehicles",
            "vrn": "AK09OCF"  # Our target
        }
    ]

    results = {}

    for endpoint in endpoints:
        print(f"\n{'─'*70}")
        print(f"Testing: {endpoint['name']}")
        print(f"VRN: {endpoint['vrn']}")
        print(f"{'─'*70}\n")

        # Try without API key first
        print("Attempt 1: Without API key")
        try:
            response = requests.post(
                endpoint['url'],
                json={"registrationNumber": endpoint['vrn']},
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0'
                },
                timeout=10
            )

            print(f"   Status: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")
            print(f"   Body preview: {response.text[:500]}")

            results[f"{endpoint['name']}_no_key"] = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text
            }

        except Exception as e:
            print(f"   Error: {str(e)}")
            results[f"{endpoint['name']}_no_key"] = {"error": str(e)}

        # Try with a dummy API key to see the error message
        print("\nAttempt 2: With dummy API key")
        try:
            response = requests.post(
                endpoint['url'],
                json={"registrationNumber": endpoint['vrn']},
                headers={
                    'Content-Type': 'application/json',
                    'x-api-key': 'test-key-12345',
                    'User-Agent': 'Mozilla/5.0'
                },
                timeout=10
            )

            print(f"   Status: {response.status_code}")
            print(f"   Body: {response.text[:500]}")

            results[f"{endpoint['name']}_dummy_key"] = {
                "status_code": response.status_code,
                "body": response.text
            }

        except Exception as e:
            print(f"   Error: {str(e)}")
            results[f"{endpoint['name']}_dummy_key"] = {"error": str(e)}

    # Save results
    with open('dvla_api_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*70}")
    print("Test complete. Results saved to: dvla_api_test_results.json")
    print(f"{'='*70}\n")

    return results


def test_mot_api_endpoints():
    """
    Test DVSA MOT API endpoints
    """
    print("\n🧪 TESTING DVSA MOT API ENDPOINTS")
    print("=" * 70)

    endpoints = [
        "https://beta.check-mot.service.gov.uk/trade/vehicles/mot-tests?registration=AK09OCF",
        "https://history.mot.api.gov.uk/v1/trade/vehicles/registration/AK09OCF",
    ]

    for url in endpoints:
        print(f"\nTrying: {url}")
        try:
            # Try without auth
            resp = requests.get(url, timeout=10)
            print(f"   No auth - Status: {resp.status_code}")
            print(f"   Response: {resp.text[:200]}")

            # Try with dummy key
            resp2 = requests.get(
                url,
                headers={'X-API-Key': 'test-key'},
                timeout=10
            )
            print(f"   Dummy key - Status: {resp2.status_code}")
            print(f"   Response: {resp2.text[:200]}")

        except Exception as e:
            print(f"   Error: {str(e)}")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("  UK VEHICLE API ENDPOINT TESTING")
    print("  Discovering API requirements and response structures")
    print("="*70)

    results = test_dvla_api_structure()
    test_mot_api_endpoints()

    print("\n\n📋 SUMMARY OF FINDINGS:")
    print("="*70)
    for key, value in results.items():
        status = value.get('status_code', value.get('error', 'unknown'))
        print(f"   {key}: {status}")
