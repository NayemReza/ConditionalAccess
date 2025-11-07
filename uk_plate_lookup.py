#!/usr/bin/env python3
"""
UK Vehicle Registration Plate Lookup Tool
Checks public sources for vehicle information
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional


class UKVehicleLookup:
    """Lookup UK vehicle registration details from public sources"""

    def __init__(self, registration: str):
        self.registration = registration.upper().replace(" ", "")
        self.results = {}

    def decode_registration_year(self) -> Dict[str, Any]:
        """
        Decode the registration year from the UK plate format
        UK plates since 2001 use format: AA## AAA
        Where ## is the age identifier
        """
        info = {
            "registration": self.registration,
            "format_info": {}
        }

        # Check if it's a current format (post-2001)
        if len(self.registration) == 7:
            age_identifier = self.registration[2:4]

            # Try to decode the year
            try:
                age_num = int(age_identifier)

                # March-August registrations (e.g., 09 = 2009)
                if 1 <= age_num <= 50:
                    year = 2000 + age_num
                    period = "March-August"
                # September-February registrations (e.g., 59 = Sept 2009)
                elif 51 <= age_num <= 99:
                    year = 2000 + (age_num - 50)
                    period = "September-February"
                else:
                    year = None
                    period = None

                if year:
                    info["format_info"] = {
                        "format": "Current (2001-present)",
                        "age_identifier": age_identifier,
                        "registration_year": year,
                        "registration_period": period,
                        "local_memory_tag": self.registration[:2],
                        "random_letters": self.registration[4:]
                    }
            except ValueError:
                info["format_info"]["format"] = "Unknown or special format"
        else:
            info["format_info"]["format"] = "Non-standard length"

        return info

    def check_mot_history_scrape(self) -> Optional[Dict[str, Any]]:
        """
        Attempt to check MOT history via the public gov.uk endpoint
        Note: This may not work if the site has CSRF protection or requires cookies
        """
        print(f"🔍 Attempting to check MOT history for {self.registration}...")

        # The gov.uk MOT check service endpoint (may be protected)
        url = "https://www.gov.uk/check-mot-history"

        # Try a simple request to see if there's a public API
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

            # First, get the main page to establish session
            response = session.get(url, timeout=10)
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": "Gov.uk MOT check page is accessible",
                    "note": "Manual lookup required at: https://www.gov.uk/check-mot-history"
                }
        except Exception as e:
            print(f"   Error: {str(e)}")
            return {"status": "error", "message": str(e)}

        return None

    def check_beta_mot_api(self, api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Attempt to check the beta MOT API
        Requires API key - this will likely fail without proper credentials
        """
        if not api_key:
            return {
                "status": "skipped",
                "message": "No API key provided. Register at: https://documentation.history.mot.api.gov.uk/"
            }

        print(f"🔍 Checking beta MOT API for {self.registration}...")

        url = f"https://beta.check-mot.service.gov.uk/trade/vehicles/mot-tests?registration={self.registration}"

        headers = {
            'X-API-Key': api_key,
            'Accept': 'application/json'
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                return {
                    "status": "success",
                    "data": response.json()
                }
            else:
                return {
                    "status": "failed",
                    "status_code": response.status_code,
                    "message": response.text[:200]
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def check_third_party_apis(self) -> Dict[str, Any]:
        """
        Check if any third-party services have public endpoints
        This is exploratory and may not work
        """
        results = {}

        # Try some known patterns that third-party services might use
        # Note: Most require API keys, but we can try

        endpoints = [
            {
                "name": "UK Vehicle Data (unauthenticated test)",
                "url": f"https://uk1.ukvehicledata.co.uk/api/datapackage/VehicleData?v=2&api_nullitems=1&auth_apikey=&key_VRM={self.registration}",
                "note": "Likely requires API key"
            }
        ]

        for endpoint in endpoints:
            print(f"🔍 Trying {endpoint['name']}...")
            try:
                response = requests.get(
                    endpoint['url'],
                    timeout=10,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )

                results[endpoint['name']] = {
                    "status_code": response.status_code,
                    "note": endpoint.get('note', ''),
                    "response_preview": response.text[:200] if response.text else None
                }

                if response.status_code == 200:
                    try:
                        results[endpoint['name']]['data'] = response.json()
                    except:
                        pass

                print(f"   Status: {response.status_code}")

            except Exception as e:
                results[endpoint['name']] = {
                    "status": "error",
                    "message": str(e)
                }
                print(f"   Error: {str(e)}")

        return results

    def run_all_checks(self, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Run all available checks"""
        print(f"\n{'='*60}")
        print(f"UK Vehicle Registration Lookup: {self.registration}")
        print(f"{'='*60}\n")

        # 1. Decode registration format
        print("📋 STEP 1: Decoding registration format...")
        self.results['format_decode'] = self.decode_registration_year()
        self._print_format_info(self.results['format_decode'])

        # 2. Check MOT history page
        print("\n📋 STEP 2: Checking gov.uk MOT service...")
        self.results['mot_check'] = self.check_mot_history_scrape()

        # 3. Try beta API (if key provided)
        print("\n📋 STEP 3: Attempting beta MOT API...")
        self.results['beta_api'] = self.check_beta_mot_api(api_key)

        # 4. Try third-party endpoints
        print("\n📋 STEP 4: Trying third-party endpoints...")
        self.results['third_party'] = self.check_third_party_apis()

        # 5. Summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}\n")
        self._print_summary()

        return self.results

    def _print_format_info(self, info: Dict[str, Any]):
        """Print formatted registration info"""
        if 'format_info' in info and info['format_info']:
            fmt = info['format_info']
            print(f"\n   Registration: {info['registration']}")
            print(f"   Format: {fmt.get('format', 'Unknown')}")

            if 'registration_year' in fmt:
                print(f"   Registered: {fmt['registration_period']} {fmt['registration_year']}")
                print(f"   Age Identifier: {fmt['age_identifier']}")
                print(f"   Local Memory Tag: {fmt['local_memory_tag']}")

    def _print_summary(self):
        """Print summary of findings"""
        print("✅ Information gathered from registration format:")
        if 'format_decode' in self.results:
            info = self.results['format_decode'].get('format_info', {})
            if 'registration_year' in info:
                print(f"   • First registered: {info['registration_period']} {info['registration_year']}")
                print(f"   • Registration area: {info['local_memory_tag']}")

        print("\n📌 Manual lookup required for detailed information:")
        print("   • MOT History: https://www.gov.uk/check-mot-history")
        print("   • Vehicle Tax: https://www.gov.uk/check-vehicle-tax")
        print("   • Vehicle Info: https://www.gov.uk/get-vehicle-information-from-dvla")

        print("\n💡 API Access (requires registration):")
        print("   • DVLA VES API: https://developer-portal.driver-vehicle-licensing.api.gov.uk/")
        print("   • DVSA MOT API: https://documentation.history.mot.api.gov.uk/")

    def save_results(self, filename: str = None):
        """Save results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vehicle_lookup_{self.registration}_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\n💾 Results saved to: {filename}")
        return filename


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='UK Vehicle Registration Lookup Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python uk_plate_lookup.py AK09OCF
  python uk_plate_lookup.py AK09OCF --api-key YOUR_API_KEY
  python uk_plate_lookup.py AK09OCF --save results.json

Note: Most official APIs require registration and API keys.
      This tool will show what's publicly accessible.
        """
    )

    parser.add_argument(
        'registration',
        help='UK vehicle registration number (e.g., AK09OCF)'
    )

    parser.add_argument(
        '--api-key',
        help='Optional API key for MOT History API',
        default=None
    )

    parser.add_argument(
        '--save',
        help='Save results to JSON file',
        metavar='FILENAME',
        nargs='?',
        const='auto'
    )

    args = parser.parse_args()

    # Create lookup instance and run checks
    lookup = UKVehicleLookup(args.registration)
    results = lookup.run_all_checks(api_key=args.api_key)

    # Save if requested
    if args.save:
        filename = args.save if args.save != 'auto' else None
        lookup.save_results(filename)

    return results


if __name__ == '__main__':
    main()
