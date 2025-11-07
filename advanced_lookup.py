#!/usr/bin/env python3
"""
Advanced UK Vehicle Lookup - Deep dive with web scraping
Ultra-think approach: Try every possible method
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from typing import Dict, Any, Optional
import time


class AdvancedUKVehicleLookup:
    """Advanced lookup using scraping and form submission techniques"""

    def __init__(self, registration: str):
        self.registration = registration.upper().replace(" ", "")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def analyze_mot_check_page(self) -> Dict[str, Any]:
        """
        REFLECTION: The gov.uk MOT history check likely has:
        1. A form with CSRF token
        2. POST endpoint that returns results
        3. Session cookies required

        Strategy: Fetch page, extract form details, submit with registration
        """
        print("\n🔬 DEEP ANALYSIS: GOV.UK MOT History Check")
        print("=" * 70)
        print("Reflection: The page likely uses form submission with CSRF protection.")
        print("Approach: Fetch form, extract tokens, simulate user submission.\n")

        url = "https://www.gov.uk/check-mot-history"

        try:
            # Step 1: Get the initial page
            print(f"Step 1: Fetching initial page: {url}")
            response = self.session.get(url, timeout=15)
            print(f"   → Status: {response.status_code}")
            print(f"   → Content length: {len(response.text)} bytes")

            if response.status_code != 200:
                return {"status": "failed", "reason": f"HTTP {response.status_code}"}

            # Step 2: Parse HTML
            print(f"\nStep 2: Parsing HTML structure")
            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for forms
            forms = soup.find_all('form')
            print(f"   → Found {len(forms)} form(s)")

            # Look for input fields
            inputs = soup.find_all('input')
            print(f"   → Found {len(inputs)} input field(s)")

            # Extract form details
            form_data = {}
            for form in forms:
                print(f"\n   Form found:")
                print(f"      Action: {form.get('action', 'N/A')}")
                print(f"      Method: {form.get('method', 'N/A')}")

                # Get all inputs in this form
                form_inputs = form.find_all('input')
                for inp in form_inputs:
                    name = inp.get('name')
                    value = inp.get('value', '')
                    inp_type = inp.get('type', 'text')
                    print(f"      Input: name='{name}', type='{inp_type}', value='{value[:50]}'")

                    if name:
                        form_data[name] = value

            # Step 3: Look for the actual service URL
            print(f"\nStep 3: Analyzing page content for service URLs")

            # Check if this is a start page that redirects
            start_button = soup.find('a', class_=re.compile(r'.*button.*start.*', re.I))
            if start_button:
                start_url = start_button.get('href', '')
                print(f"   → Found 'Start now' button: {start_url}")

                if start_url and not start_url.startswith('http'):
                    start_url = 'https://www.gov.uk' + start_url

                # Follow the start button
                return self.follow_mot_service(start_url)

            # Look for links to the actual service
            links = soup.find_all('a', href=re.compile(r'vehicleenquiry|mot|check', re.I))
            print(f"   → Found {len(links)} relevant links")
            for link in links[:5]:
                print(f"      {link.get('href')}: {link.text.strip()[:50]}")

            return {
                "status": "analyzed",
                "forms_found": len(forms),
                "form_data": form_data,
                "page_length": len(response.text)
            }

        except Exception as e:
            print(f"   ✗ Error: {str(e)}")
            return {"status": "error", "message": str(e)}

    def follow_mot_service(self, start_url: str) -> Dict[str, Any]:
        """Follow the MOT service to the actual form"""
        print(f"\n🔍 Following service URL: {start_url}")

        try:
            response = self.session.get(start_url, timeout=15)
            print(f"   → Status: {response.status_code}")
            print(f"   → Final URL: {response.url}")

            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for registration input
            reg_input = soup.find('input', {'name': re.compile(r'registration|vrm|reg', re.I)})
            if reg_input:
                print(f"   ✓ Found registration input field: {reg_input.get('name')}")

                # Find the form this input belongs to
                form = reg_input.find_parent('form')
                if form:
                    return self.submit_mot_form(form, response.url)

            return {"status": "no_form_found", "url": response.url}

        except Exception as e:
            print(f"   ✗ Error: {str(e)}")
            return {"status": "error", "message": str(e)}

    def submit_mot_form(self, form_soup, base_url: str) -> Dict[str, Any]:
        """
        REFLECTION: Now we have the form, need to:
        1. Extract all hidden fields (CSRF tokens, etc.)
        2. Add our registration number
        3. Submit POST request
        4. Parse response for vehicle data
        """
        print(f"\n📝 Preparing to submit MOT form")
        print("Reflection: Need to preserve all hidden fields and tokens")

        # Get form action
        action = form_soup.get('action', '')
        method = form_soup.get('method', 'post').upper()

        if not action.startswith('http'):
            from urllib.parse import urljoin
            action = urljoin(base_url, action)

        print(f"   → Action: {action}")
        print(f"   → Method: {method}")

        # Build form data
        form_data = {}
        for input_field in form_soup.find_all('input'):
            name = input_field.get('name')
            if name:
                value = input_field.get('value', '')
                input_type = input_field.get('type', 'text')

                # Set our registration for the relevant field
                if re.match(r'.*(registration|vrm|reg).*', name, re.I):
                    form_data[name] = self.registration
                    print(f"   → Setting {name} = {self.registration}")
                else:
                    form_data[name] = value
                    if value:
                        print(f"   → Hidden field: {name} = {value[:50]}")

        # Submit form
        try:
            print(f"\n   Submitting form...")
            if method == 'POST':
                response = self.session.post(action, data=form_data, timeout=15)
            else:
                response = self.session.get(action, params=form_data, timeout=15)

            print(f"   → Response status: {response.status_code}")
            print(f"   → Response URL: {response.url}")

            # Parse response
            return self.parse_mot_results(response.text, response.url)

        except Exception as e:
            print(f"   ✗ Error submitting: {str(e)}")
            return {"status": "error", "message": str(e)}

    def parse_mot_results(self, html: str, url: str) -> Dict[str, Any]:
        """
        REFLECTION: Parse the MOT results page for vehicle data
        Looking for: Make, Model, Year, MOT dates, mileage, test results
        """
        print(f"\n🔍 Parsing MOT results")

        soup = BeautifulSoup(html, 'html.parser')
        results = {
            "status": "parsed",
            "url": url,
            "registration": self.registration
        }

        # Save HTML for debugging
        with open(f'mot_response_{self.registration}.html', 'w') as f:
            f.write(html)
        print(f"   → Saved response to mot_response_{self.registration}.html")

        # Look for common patterns in gov.uk pages
        # Vehicle details are usually in definition lists or divs

        # Try to find vehicle make/model
        make_patterns = [
            soup.find(text=re.compile(r'Make', re.I)),
            soup.find('dt', text=re.compile(r'Make', re.I)),
        ]

        for make_elem in make_patterns:
            if make_elem:
                # Find associated value
                dd = make_elem.find_next('dd') if hasattr(make_elem, 'find_next') else None
                if dd:
                    results['make'] = dd.text.strip()
                    print(f"   ✓ Make: {results['make']}")
                break

        # Look for any tables (MOT history often in tables)
        tables = soup.find_all('table')
        if tables:
            print(f"   → Found {len(tables)} table(s)")
            results['tables_found'] = len(tables)

        # Look for error messages
        errors = soup.find_all(class_=re.compile(r'error', re.I))
        if errors:
            error_text = ' '.join([e.text.strip() for e in errors])
            print(f"   ⚠ Errors found: {error_text[:200]}")
            results['errors'] = error_text

        # Check if we got vehicle data
        if 'make' in results:
            results['status'] = 'success'
        elif 'error' in results:
            results['status'] = 'error'
        else:
            results['status'] = 'unknown'
            print("   → Could not determine if request succeeded")

        return results

    def try_direct_mot_api_endpoints(self) -> Dict[str, Any]:
        """
        REFLECTION: Sometimes gov.uk services have JSON endpoints
        Let's try variations of potential API endpoints
        """
        print("\n🎯 TRYING DIRECT API ENDPOINTS")
        print("=" * 70)
        print("Reflection: Gov.uk services sometimes expose JSON APIs")
        print("Strategy: Try common endpoint patterns\n")

        endpoints = [
            f"https://www.check-mot.service.gov.uk/results?registration={self.registration}",
            f"https://beta.check-mot.service.gov.uk/results?registration={self.registration}",
            f"https://vehicleenquiry.service.gov.uk/?registration={self.registration}",
            f"https://www.gov.uk/get-vehicle-information-from-dvla?registration={self.registration}",
        ]

        results = {}

        for endpoint in endpoints:
            print(f"\nTrying: {endpoint}")
            try:
                # Try with Accept: application/json
                headers = self.session.headers.copy()
                headers['Accept'] = 'application/json'

                response = self.session.get(endpoint, headers=headers, timeout=10, allow_redirects=True)
                print(f"   → Status: {response.status_code}")
                print(f"   → Final URL: {response.url}")
                print(f"   → Content-Type: {response.headers.get('Content-Type', 'N/A')}")

                results[endpoint] = {
                    "status_code": response.status_code,
                    "final_url": response.url,
                    "content_type": response.headers.get('Content-Type'),
                    "content_preview": response.text[:500]
                }

                # Try to parse as JSON
                if 'json' in response.headers.get('Content-Type', ''):
                    try:
                        json_data = response.json()
                        print(f"   ✓ Got JSON response!")
                        results[endpoint]['json'] = json_data
                        return {"status": "success", "data": json_data, "endpoint": endpoint}
                    except:
                        pass

                # Check if HTML contains vehicle data
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    if soup.find(text=re.compile(r'make|model|mot', re.I)):
                        print(f"   → HTML contains vehicle-related content")
                        # Save for analysis
                        with open(f'endpoint_response_{len(results)}.html', 'w') as f:
                            f.write(response.text)

            except Exception as e:
                print(f"   ✗ Error: {str(e)}")
                results[endpoint] = {"status": "error", "message": str(e)}

        return {"status": "attempted", "results": results}

    def check_public_data_downloads(self) -> Dict[str, Any]:
        """
        REFLECTION: DVSA might publish bulk MOT data publicly
        This could contain our vehicle's information
        """
        print("\n📊 CHECKING PUBLIC DATA SOURCES")
        print("=" * 70)
        print("Reflection: DVSA publishes anonymized MOT test data")
        print("Strategy: Check if there's accessible bulk data\n")

        # DVSA data.gov.uk datasets
        data_urls = [
            "https://data.gov.uk/dataset/e3939ef8-30c7-4ca8-9c7c-ad9475cc9b2f/anonymised-mot-tests-and-results",
            "https://data.dft.gov.uk/api/3/action/package_show?id=anonymised-mot-test",
        ]

        results = {}

        for url in data_urls:
            print(f"\nChecking: {url}")
            try:
                response = self.session.get(url, timeout=15)
                print(f"   → Status: {response.status_code}")

                if response.status_code == 200:
                    # Try parsing as JSON (CKAN API)
                    try:
                        data = response.json()
                        if 'result' in data:
                            print(f"   ✓ Found dataset metadata")
                            results[url] = {"status": "success", "data": data}

                            # Look for download URLs
                            if 'resources' in data.get('result', {}):
                                resources = data['result']['resources']
                                print(f"   → Found {len(resources)} resources")
                                for r in resources[:3]:
                                    print(f"      - {r.get('name', 'Unknown')}: {r.get('url', 'N/A')}")
                    except:
                        pass

            except Exception as e:
                print(f"   ✗ Error: {str(e)}")
                results[url] = {"status": "error", "message": str(e)}

        return {"status": "checked", "results": results}

    def run_comprehensive_check(self) -> Dict[str, Any]:
        """Run all possible checks in sequence"""
        print(f"\n{'='*70}")
        print(f"COMPREHENSIVE UK VEHICLE LOOKUP: {self.registration}")
        print(f"{'='*70}")
        print("\n💭 ULTRATHINKING MODE ACTIVATED")
        print("Trying every possible avenue to retrieve data...\n")

        all_results = {}

        # Method 1: Analyze and scrape MOT check page
        all_results['mot_scraping'] = self.analyze_mot_check_page()
        time.sleep(1)  # Be polite

        # Method 2: Try direct API endpoints
        all_results['direct_apis'] = self.try_direct_mot_api_endpoints()
        time.sleep(1)

        # Method 3: Check public data sources
        all_results['public_data'] = self.check_public_data_downloads()

        # Save all results
        with open(f'comprehensive_results_{self.registration}.json', 'w') as f:
            json.dump(all_results, f, indent=2, default=str)

        print(f"\n{'='*70}")
        print("COMPREHENSIVE CHECK COMPLETE")
        print(f"{'='*70}")
        print(f"\n💾 All results saved to: comprehensive_results_{self.registration}.json")

        return all_results


def main():
    import sys

    reg = sys.argv[1] if len(sys.argv) > 1 else "AK09OCF"

    lookup = AdvancedUKVehicleLookup(reg)
    results = lookup.run_comprehensive_check()

    print("\n\n📋 SUMMARY:")
    print("=" * 70)
    for method, result in results.items():
        status = result.get('status', 'unknown')
        print(f"{method}: {status}")

    return results


if __name__ == '__main__':
    main()
