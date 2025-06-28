#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Simple Transport API Test Script
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()


def test_transport_api():
    """Test the Transport NSW API integration"""

    # Check if API key is set
    api_key = os.getenv("TRANSPORT_API_KEY")
    if not api_key:
        print("❌ TRANSPORT_API_KEY environment variable not set")
        print("Please set it manually:")
        print("export TRANSPORT_API_KEY='your_api_key_here'")
        return False

    print("🚆 Testing Transport NSW API Integration")
    print("=" * 50)

    try:
        # Test the import first
        print("🔍 Testing import...")
        from lib.transport_api import TransportNSWAPI

        print("✅ Import successful")

        # Initialize API
        api = TransportNSWAPI(api_key)
        print("✅ API initialized successfully")

        # Test stop search
        print("\n🔍 Testing stop search...")
        stops = api.find_stop("Central")
        if stops and "locations" in stops:
            print(f"✅ Found {len(stops['locations'])} stops for 'Central'")
        else:
            print("❌ Stop search failed")
            return False

        # Test Rhodes to Central journey
        print("\n🚉 Testing Rhodes to Central journey...")
        journey_stops = api.get_simplified_journey_stops("213891", "10101100")
        if journey_stops:
            print(f"✅ Found {len(journey_stops)} stops in journey")
            if journey_stops:
                first_stop = journey_stops[0]
                print(f"   First stop: {first_stop.get('name', 'N/A')}")
                print(
                    f"   Minutes from now: {first_stop.get('minutes_from_now', 'N/A')}"
                )
        else:
            print("❌ No journey found")
            return False

        print("\n🎉 All tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_transport_api()
    sys.exit(0 if success else 1)
