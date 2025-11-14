#!/usr/bin/env python3
"""
Working UK Vehicle Lookup using Confused.com endpoint
Based on successful GitHub implementation
"""

import requests
import json
from typing import Dict, Any


class WorkingVehicleLookup:
    """
    REFLECTION: Found working endpoint from GitHub repo
    - confused.com offers free registration lookups
    - Requires session cookies first, then POST to lookup endpoint
    """

    def __init__(self, registration: str):
        self.registration = registration.upper().replace(" ", "")
        self.session = requests.Session()
        # Use realistic browser headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://motor.confused.com/',
            'Origin': 'https://motor.confused.com',
            'DNT': '1',
            'Connection': 'keep-alive',
        })

    def lookup_via_confused(self) -> Dict[str, Any]:
        """
        Use confused.com's registration lookup endpoint
        This is the method from the GitHub repo
        """
        print(f"\n🚗 Looking up {self.registration} via Confused.com")
        print("=" * 70)
        print("Strategy: Use insurance comparison site's free lookup service\n")

        try:
            # Step 1: Establish session cookies
            print("Step 1: Establishing session cookies...")
            init_url = "https://motor.confused.com/"
            init_response = self.session.get(init_url, timeout=15)
            print(f"   → Status: {init_response.status_code}")
            print(f"   → Cookies set: {len(self.session.cookies)} cookie(s)")

            # Step 2: Submit registration lookup
            print(f"\nStep 2: Submitting registration lookup...")
            lookup_url = "https://motor.confused.com/Motor/RegistrationLookup"

            # Send as form data
            form_data = {
                'registrationNumber': self.registration
            }

            response = self.session.post(
                lookup_url,
                data=form_data,
                timeout=15
            )

            print(f"   → Status: {response.status_code}")
            print(f"   → Content-Type: {response.headers.get('Content-Type', 'N/A')}")

            if response.status_code == 200:
                # Parse the JSON response
                data = response.json()
                print(f"   ✓ Got response!")

                # The response structure from confused.com
                if 'data' in data:
                    vehicle_data = data['data']

                    # Sometimes vehicle comes as a JSON string
                    if isinstance(vehicle_data.get('vehicle'), str):
                        vehicle_data['vehicle'] = json.loads(vehicle_data['vehicle'])

                    print(f"\n{'='*70}")
                    print("VEHICLE INFORMATION FOUND!")
                    print(f"{'='*70}\n")

                    return {
                        "status": "success",
                        "source": "confused.com",
                        "registration": self.registration,
                        "data": vehicle_data
                    }
                else:
                    return {
                        "status": "no_data",
                        "message": "Response didn't contain expected data structure",
                        "raw_response": data
                    }
            else:
                return {
                    "status": "failed",
                    "status_code": response.status_code,
                    "response": response.text[:500]
                }

        except Exception as e:
            print(f"   ✗ Error: {str(e)}")
            return {"status": "error", "message": str(e)}

    def try_alternative_endpoints(self) -> Dict[str, Any]:
        """
        REFLECTION: Try other comparison sites that might offer lookups
        - comparethemarket.com
        - gocompare.com
        - moneysupermarket.com
        """
        print(f"\n🔄 Trying alternative comparison sites...")
        print("=" * 70)

        alternatives = [
            {
                "name": "CompareTheMarket",
                "init_url": "https://www.comparethemarket.com/",
                "lookup_url": "https://www.comparethemarket.com/car-insurance/vehicle-lookup/",
                "param_name": "registration"
            },
            {
                "name": "GoCompare",
                "init_url": "https://www.gocompare.com/",
                "lookup_url": "https://www.gocompare.com/car-insurance/vrm-lookup/",
                "param_name": "vrm"
            }
        ]

        results = {}

        for alt in alternatives:
            print(f"\nTrying {alt['name']}...")
            try:
                # Get session
                init_resp = self.session.get(alt['init_url'], timeout=10)
                print(f"   → Session: {init_resp.status_code}")

                # Try POST
                form_data = {alt['param_name']: self.registration}
                lookup_resp = self.session.post(
                    alt['lookup_url'],
                    data=form_data,
                    timeout=10
                )
                print(f"   → Lookup: {lookup_resp.status_code}")

                if lookup_resp.status_code == 200:
                    try:
                        data = lookup_resp.json()
                        results[alt['name']] = {"status": "success", "data": data}
                        print(f"   ✓ Got JSON response!")
                    except:
                        results[alt['name']] = {
                            "status": "html_response",
                            "preview": lookup_resp.text[:200]
                        }
                else:
                    results[alt['name']] = {
                        "status": "failed",
                        "status_code": lookup_resp.status_code
                    }

            except Exception as e:
                print(f"   ✗ Error: {str(e)}")
                results[alt['name']] = {"status": "error", "message": str(e)}

        return results

    def format_vehicle_data(self, data: Dict[str, Any]) -> str:
        """Format vehicle data for display"""
        if data.get('status') != 'success':
            return f"Status: {data.get('status')}\n{json.dumps(data, indent=2)}"

        output = []
        output.append(f"\n{'='*70}")
        output.append(f"VEHICLE DETAILS: {self.registration}")
        output.append(f"{'='*70}\n")

        vehicle = data.get('data', {})

        # Extract common fields
        fields = {
            'Make': vehicle.get('make') or vehicle.get('Make'),
            'Model': vehicle.get('model') or vehicle.get('Model'),
            'Year': vehicle.get('year') or vehicle.get('Year'),
            'Colour': vehicle.get('colour') or vehicle.get('Colour') or vehicle.get('color'),
            'Fuel Type': vehicle.get('fuelType') or vehicle.get('FuelType') or vehicle.get('fuel'),
            'Engine Size': vehicle.get('engineSize') or vehicle.get('EngineSize') or vehicle.get('engineCapacity'),
            'Transmission': vehicle.get('transmission') or vehicle.get('Transmission'),
            'Body Style': vehicle.get('bodyStyle') or vehicle.get('BodyStyle'),
            'Doors': vehicle.get('doors') or vehicle.get('Doors'),
            'Seats': vehicle.get('seats') or vehicle.get('Seats'),
        }

        for key, value in fields.items():
            if value:
                output.append(f"   {key:.<20} {value}")

        output.append(f"\n{'='*70}")
        output.append(f"Data source: {data.get('source', 'Unknown')}")
        output.append(f"{'='*70}\n")

        return '\n'.join(output)

    def run(self) -> Dict[str, Any]:
        """Run the lookup"""
        # Try confused.com first (known working)
        result = self.lookup_via_confused()

        if result.get('status') == 'success':
            # Format and display
            print(self.format_vehicle_data(result))

            # Save to file
            filename = f'vehicle_data_{self.registration}.json'
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"💾 Data saved to: {filename}\n")

            return result

        # If confused.com failed, try alternatives
        print("\n⚠️ Primary lookup failed, trying alternatives...")
        alt_results = self.try_alternative_endpoints()

        # Check if any succeeded
        for name, res in alt_results.items():
            if res.get('status') == 'success':
                result = {
                    "status": "success",
                    "source": name,
                    "registration": self.registration,
                    "data": res['data']
                }
                print(self.format_vehicle_data(result))
                return result

        # Nothing worked
        print("\n❌ All lookup methods failed")
        return {
            "status": "all_failed",
            "confused_result": result,
            "alternative_results": alt_results
        }


def main():
    import sys

    reg = sys.argv[1] if len(sys.argv) > 1 else "AK09OCF"

    print(f"\n{'#'*70}")
    print(f"#  UK VEHICLE REGISTRATION LOOKUP")
    print(f"#  Using proven working endpoints")
    print(f"{'#'*70}\n")

    lookup = WorkingVehicleLookup(reg)
    result = lookup.run()

    # Print final status
    if result.get('status') == 'success':
        print("✅ SUCCESS! Vehicle information retrieved.")
    else:
        print(f"\n⚠️  Final status: {result.get('status')}")
        print("\nFallback: Manual lookup required at:")
        print("   • https://www.confused.com/car-insurance")
        print("   • https://www.gov.uk/check-mot-history")

    return result


if __name__ == '__main__':
    main()
