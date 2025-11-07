#!/usr/bin/env python3
"""
Enhanced UK Vehicle Registration Plate Lookup Tool
More sophisticated approach with browser simulation
"""

import requests
from datetime import datetime
from typing import Dict, Any
import json


def get_browser_headers():
    """Return realistic browser headers"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }


def decode_uk_registration(reg: str) -> Dict[str, Any]:
    """
    Comprehensive decode of UK registration plates
    """
    reg = reg.upper().replace(" ", "")

    # Memory tag to area mapping (current format - post 2001)
    area_codes = {
        'A': 'Anglia',
        'B': 'Birmingham',
        'C': 'Cymru (Wales)',
        'D': 'Deeside',
        'E': 'Essex',
        'F': 'Forest and Fens',
        'G': 'Garden of England',
        'H': 'Hampshire and Dorset',
        'K': 'Luton (no motor show)',
        'L': 'London',
        'M': 'Manchester',
        'N': 'North',
        'O': 'Oxford',
        'P': 'Preston',
        'R': 'Reading',
        'S': 'Scotland',
        'V': 'Severn Valley',
        'W': 'West of England',
        'X': 'Personal export',
        'Y': 'Yorkshire'
    }

    # Specific office mappings for Anglia (A)
    anglia_offices = {
        'AA-AN': 'Peterborough',
        'AO-AU': 'Norwich',
        'AV-AY': 'Ipswich'
    }

    info = {
        'registration': reg,
        'length': len(reg),
        'format': 'Unknown'
    }

    if len(reg) == 7:
        first_letter = reg[0]
        memory_tag = reg[:2]
        age_id = reg[2:4]
        random = reg[4:]

        # Determine region
        region = area_codes.get(first_letter, 'Unknown')

        # Specific office for Anglia
        office = None
        if first_letter == 'A':
            if memory_tag <= 'AN':
                office = 'Peterborough'
            elif memory_tag <= 'AU':
                office = 'Norwich'
            elif memory_tag <= 'AY':
                office = 'Ipswich'

        try:
            age_num = int(age_id)

            if 1 <= age_num <= 50:
                year = 2000 + age_num
                period = 'March-August'
                month_range = 'March to August'
            elif 51 <= age_num <= 99:
                year = 2000 + (age_num - 50)
                period = 'September-February'
                month_range = 'September to February'
            else:
                year = None
                period = None
                month_range = None

            info.update({
                'format': 'Current format (2001-present)',
                'memory_tag': memory_tag,
                'age_identifier': age_id,
                'random_letters': random,
                'region': region,
                'dvla_office': office,
                'registration_year': year,
                'registration_period': period,
                'month_range': month_range,
                'approximate_age_years': datetime.now().year - year if year else None
            })

        except ValueError:
            info['format'] = 'Non-standard age identifier'

    elif len(reg) == 6:
        info['format'] = 'Possible prefix or suffix format (1983-2001)'
    else:
        info['format'] = 'Non-standard or dateless format'

    return info


def check_vehicle_smart_api(reg: str) -> Dict[str, Any]:
    """
    Try VehicleSmart-style endpoint
    This is exploratory and may require authentication
    """
    print(f"🔍 Checking VehicleSmart-style endpoint...")

    try:
        session = requests.Session()
        session.headers.update(get_browser_headers())

        # Try a generic vehicle info endpoint pattern
        url = f"https://vehiclesmart.com/api/v1/vehicle/{reg}"

        response = session.get(url, timeout=10)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()
                return {'status': 'success', 'data': data}
            except:
                return {'status': 'html_response', 'note': 'Returned HTML, not JSON'}
        else:
            return {
                'status': 'failed',
                'status_code': response.status_code,
                'note': 'May require API key or different endpoint'
            }

    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def check_regcheck_api(reg: str) -> Dict[str, Any]:
    """
    Try RegCheck-style endpoint
    """
    print(f"🔍 Checking RegCheck-style patterns...")

    try:
        session = requests.Session()
        session.headers.update(get_browser_headers())

        # Try various potential endpoints
        endpoints = [
            f"https://www.regcheck.org.uk/api/reg.asmx/Check?RegistrationNumber={reg}",
            f"https://www.regcheck.org.uk/api/v1/vehicle/{reg}",
        ]

        for url in endpoints:
            try:
                response = session.get(url, timeout=10)
                print(f"   Trying: {url[:50]}... Status: {response.status_code}")

                if response.status_code == 200:
                    return {
                        'status': 'possible_success',
                        'url': url,
                        'preview': response.text[:300]
                    }
            except:
                continue

        return {'status': 'no_public_endpoint_found'}

    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def generate_report(reg: str) -> str:
    """
    Generate a comprehensive report
    """
    print(f"\n{'='*70}")
    print(f"UK VEHICLE REGISTRATION LOOKUP REPORT")
    print(f"{'='*70}\n")
    print(f"Registration: {reg}")
    print(f"Lookup Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    # Decode registration
    print("📋 REGISTRATION DECODE")
    print("-" * 70)

    info = decode_uk_registration(reg)

    for key, value in info.items():
        if value is not None:
            print(f"   {key.replace('_', ' ').title()}: {value}")

    print()

    # Summary
    if 'registration_year' in info and info['registration_year']:
        print("✅ DECODED INFORMATION:")
        print(f"   • Region: {info.get('region', 'Unknown')}")
        if info.get('dvla_office'):
            print(f"   • DVLA Office: {info['dvla_office']}")
        print(f"   • First Registered: {info['month_range']} {info['registration_year']}")
        print(f"   • Approximate Age: {info['approximate_age_years']} years")
        print()

    # Try API endpoints
    print("🌐 API ENDPOINT CHECKS")
    print("-" * 70)

    vehiclesmart_result = check_vehicle_smart_api(reg)
    print(f"   VehicleSmart: {vehiclesmart_result.get('status', 'unknown')}")

    regcheck_result = check_regcheck_api(reg)
    print(f"   RegCheck: {regcheck_result.get('status', 'unknown')}")

    print()

    # Manual lookup links
    print("🔗 MANUAL LOOKUP RESOURCES (Free)")
    print("-" * 70)
    print(f"   • MOT History Check:")
    print(f"     https://www.gov.uk/check-mot-history")
    print(f"     (Enter: {reg})")
    print()
    print(f"   • Vehicle Tax Check:")
    print(f"     https://www.gov.uk/check-vehicle-tax")
    print(f"     (Enter: {reg})")
    print()
    print(f"   • Get Vehicle Information from DVLA:")
    print(f"     https://www.gov.uk/get-vehicle-information-from-dvla")
    print(f"     (Enter: {reg})")
    print()

    # Third-party free checks
    print("🔗 THIRD-PARTY FREE CHECKS")
    print("-" * 70)
    print(f"   • CarCheck.co.uk: https://www.carcheck.co.uk/")
    print(f"   • VehicleScore.co.uk: https://vehiclescore.co.uk/")
    print(f"   • CheckCarDetails.co.uk: https://www.checkcardetails.co.uk/")
    print(f"   • CarVeto.co.uk: https://www.carveto.co.uk/")
    print()

    # API access info
    print("💡 API ACCESS (For Automated Lookups)")
    print("-" * 70)
    print("   Official Government APIs:")
    print("   • DVLA Vehicle Enquiry Service (VES)")
    print("     Portal: https://developer-portal.driver-vehicle-licensing.api.gov.uk/")
    print("     Info: Requires registration and API key")
    print()
    print("   • DVSA MOT History API")
    print("     Docs: https://documentation.history.mot.api.gov.uk/")
    print("     Info: Requires application and approval")
    print()
    print("   Commercial APIs (with free trials):")
    print("   • UK Vehicle Data: https://ukvehicledata.co.uk/")
    print("   • CarAnalytics: https://www.caranalytics.co.uk/")
    print("   • One Auto API: https://www.oneautoapi.com/")
    print()

    print("=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("1. Use the gov.uk MOT check to see MOT history and mileage")
    print("2. Use gov.uk vehicle tax check to see current tax status")
    print("3. For make/model/spec, use one of the free third-party checks")
    print("4. For API access, register with DVLA or commercial providers")
    print("=" * 70)

    return info


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Enhanced UK Vehicle Registration Lookup',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'registration',
        help='UK vehicle registration number'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format'
    )

    parser.add_argument(
        '--save',
        metavar='FILE',
        help='Save report to file'
    )

    args = parser.parse_args()

    if args.json:
        info = decode_uk_registration(args.registration)
        print(json.dumps(info, indent=2))
    else:
        info = generate_report(args.registration)

        if args.save:
            with open(args.save, 'w') as f:
                json.dump(info, f, indent=2, default=str)
            print(f"\n💾 Data saved to: {args.save}")


if __name__ == '__main__':
    main()
