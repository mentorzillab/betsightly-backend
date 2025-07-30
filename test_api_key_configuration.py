#!/usr/bin/env python3
"""
🔑 TEST API KEY CONFIGURATION
Test the APIFootball.com API key and verify it can fetch real fixture data.
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_apifootball_api():
    """Test APIFootball.com API key and fetch sample data."""
    print("🔑 TESTING APIFOOTBALL.COM API CONFIGURATION")
    print("=" * 60)
    
    # Get API key from environment
    api_key = os.getenv('APIFOOTBALL_API_KEY', '')
    
    if not api_key:
        print("❌ APIFOOTBALL_API_KEY not found in environment")
        return False
    
    print(f"✅ API key found: {api_key[:10]}...{api_key[-4:]} ({len(api_key)} chars)")
    
    # Test API connection with countries endpoint (lightweight test)
    print("\n🌐 Testing API connection...")
    try:
        url = "https://apiv3.apifootball.com/"
        params = {
            "action": "get_countries",
            "APIkey": api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if isinstance(data, dict) and "error" in data:
            print(f"❌ API Error: {data['error']}")
            return False
        
        countries = data if isinstance(data, list) else []
        print(f"✅ API connection successful! Found {len(countries)} countries")
        
        # Show sample countries
        if countries:
            print("📋 Sample countries:")
            for i, country in enumerate(countries[:5]):
                country_name = country.get('country_name', 'Unknown')
                country_id = country.get('country_id', 'N/A')
                print(f"   {i+1}. {country_name} (ID: {country_id})")
        
    except Exception as e:
        print(f"❌ API connection failed: {str(e)}")
        return False
    
    # Test fixture fetching for today
    print("\n📅 Testing fixture fetching for today...")
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        
        params = {
            "action": "get_events",
            "from": today,
            "to": today,
            "APIkey": api_key
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if isinstance(data, dict) and "error" in data:
            print(f"⚠️  API Error for fixtures: {data['error']}")
            # Try tomorrow instead
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            print(f"🔄 Trying tomorrow ({tomorrow}) instead...")
            
            params["from"] = tomorrow
            params["to"] = tomorrow
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
        
        fixtures = data if isinstance(data, list) else []
        print(f"✅ Fixture fetching successful! Found {len(fixtures)} fixtures")
        
        # Show sample fixtures
        if fixtures:
            print("⚽ Sample fixtures:")
            for i, fixture in enumerate(fixtures[:3]):
                home_team = fixture.get('match_hometeam_name', 'Unknown')
                away_team = fixture.get('match_awayteam_name', 'Unknown')
                league = fixture.get('league_name', 'Unknown League')
                match_date = fixture.get('match_date', 'Unknown')
                match_time = fixture.get('match_time', 'Unknown')
                
                print(f"   {i+1}. {home_team} vs {away_team}")
                print(f"      🏆 League: {league}")
                print(f"      📅 Date/Time: {match_date} {match_time}")
        else:
            print("📭 No fixtures found for the tested dates")
        
        return True
        
    except Exception as e:
        print(f"❌ Fixture fetching failed: {str(e)}")
        return False

def test_service_integration():
    """Test the APIFootball service integration."""
    print("\n🔧 TESTING SERVICE INTEGRATION")
    print("-" * 40)
    
    try:
        # Import and test the service
        from services.apifootball_service import APIFootballService
        
        service = APIFootballService()
        
        if not service.api_key:
            print("❌ Service API key not configured")
            return False
        
        print(f"✅ Service initialized with API key: {service.api_key[:10]}...{service.api_key[-4:]}")
        
        # Test getting fixtures for tomorrow
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"📅 Testing fixture retrieval for {tomorrow}...")
        
        fixtures = service.get_daily_fixtures(tomorrow)
        
        print(f"✅ Service returned {len(fixtures)} fixtures")
        
        if fixtures:
            print("⚽ Sample fixture from service:")
            fixture = fixtures[0]
            print(f"   🏠 Home: {fixture.get('home_team', 'Unknown')}")
            print(f"   🏃 Away: {fixture.get('away_team', 'Unknown')}")
            print(f"   🏆 League: {fixture.get('league_name', 'Unknown')}")
            print(f"   📅 Date: {fixture.get('date', 'Unknown')}")
            print(f"   🆔 Fixture ID: {fixture.get('fixture_id', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Service integration test failed: {str(e)}")
        return False

def main():
    """Main test function."""
    print("🧪 API KEY CONFIGURATION TEST")
    print("=" * 80)
    
    # Test 1: Direct API testing
    api_test_passed = test_apifootball_api()
    
    # Test 2: Service integration testing
    service_test_passed = test_service_integration()
    
    # Summary
    print("\n📋 TEST SUMMARY")
    print("=" * 30)
    print(f"🔑 Direct API Test: {'✅ PASSED' if api_test_passed else '❌ FAILED'}")
    print(f"🔧 Service Integration: {'✅ PASSED' if service_test_passed else '❌ FAILED'}")
    
    if api_test_passed and service_test_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ API key is properly configured and working")
        print("✅ Service integration is functional")
        print("🚀 Ready to generate real predictions!")
        return True
    else:
        print("\n❌ SOME TESTS FAILED")
        print("🔧 Please check the API key configuration and try again")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
