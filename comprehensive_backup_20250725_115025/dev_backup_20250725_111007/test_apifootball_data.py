#!/usr/bin/env python3
"""
Test APIFootball Data
Check what data structure and fields we're getting from APIFootball API.
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def load_api_key():
    """Load API key from environment."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    api_key = os.getenv('APIFOOTBALL_API_KEY', '')
    
    if not api_key:
        print("❌ APIFOOTBALL_API_KEY not found in environment")
        print("💡 Set it with: export APIFOOTBALL_API_KEY=your_key_here")
        return None
    
    print(f"✅ API key found: {api_key[:10]}...{api_key[-4:]}")
    return api_key

def test_basic_api_call(api_key):
    """Test basic API call to get countries."""
    print("\n🌐 Testing basic API call (countries)...")
    
    try:
        url = "https://apiv3.apifootball.com/"
        params = {
            "action": "get_countries",
            "APIkey": api_key
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                print(f"✅ API working: {len(data)} countries returned")
                print(f"📊 Sample countries: {[c.get('country_name', 'Unknown') for c in data[:3]]}")
                return True
            else:
                print(f"⚠️  Unexpected response: {type(data)}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_fixtures_api_call(api_key):
    """Test fixtures API call and examine data structure."""
    print("\n📅 Testing fixtures API call...")
    
    try:
        url = "https://apiv3.apifootball.com/"
        today = datetime.now().strftime("%Y-%m-%d")
        
        params = {
            "action": "get_events",
            "from": today,
            "to": today,
            "APIkey": api_key
        }
        
        print(f"🔍 Fetching fixtures for: {today}")
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                print(f"✅ Fixtures API working: {len(data)} fixtures returned")
                
                if len(data) > 0:
                    # Examine first fixture structure
                    sample_fixture = data[0]
                    print(f"\n📋 Sample fixture structure:")
                    print(f"   Match ID: {sample_fixture.get('match_id', 'N/A')}")
                    print(f"   Home Team: {sample_fixture.get('match_hometeam_name', 'N/A')}")
                    print(f"   Away Team: {sample_fixture.get('match_awayteam_name', 'N/A')}")
                    print(f"   League: {sample_fixture.get('league_name', 'N/A')}")
                    print(f"   Date: {sample_fixture.get('match_date', 'N/A')}")
                    print(f"   Time: {sample_fixture.get('match_time', 'N/A')}")
                    print(f"   Status: {sample_fixture.get('match_status', 'N/A')}")
                    print(f"   Home Score: {sample_fixture.get('match_hometeam_score', 'N/A')}")
                    print(f"   Away Score: {sample_fixture.get('match_awayteam_score', 'N/A')}")
                    
                    # Check for odds fields
                    print(f"\n💰 Checking for odds fields:")
                    odds_fields = [
                        'match_hometeam_odds', 'match_awayteam_odds', 'match_draw_odds',
                        'odds_1', 'odds_x', 'odds_2', 'odds_home', 'odds_away', 'odds_draw',
                        'bet365_odds_1', 'bet365_odds_x', 'bet365_odds_2'
                    ]
                    
                    found_odds = False
                    for field in odds_fields:
                        if field in sample_fixture:
                            print(f"   ✅ {field}: {sample_fixture[field]}")
                            found_odds = True
                    
                    if not found_odds:
                        print("   ❌ No odds fields found in fixture data")
                    
                    # Show all available fields
                    print(f"\n🔍 All available fields ({len(sample_fixture)} total):")
                    for key, value in sample_fixture.items():
                        value_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                        print(f"   • {key}: {value_str}")
                
                return True
            else:
                print(f"⚠️  Unexpected response type: {type(data)}")
                if isinstance(data, dict) and "error" in data:
                    print(f"❌ API Error: {data['error']}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_odds_api_call(api_key):
    """Test if there's a separate odds API endpoint."""
    print("\n💰 Testing odds API call...")
    
    try:
        url = "https://apiv3.apifootball.com/"
        today = datetime.now().strftime("%Y-%m-%d")
        
        params = {
            "action": "get_odds",
            "from": today,
            "to": today,
            "APIkey": api_key
        }
        
        print(f"🔍 Fetching odds for: {today}")
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                print(f"✅ Odds API working: {len(data)} odds returned")
                
                if len(data) > 0:
                    sample_odds = data[0]
                    print(f"\n📋 Sample odds structure:")
                    for key, value in sample_odds.items():
                        value_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                        print(f"   • {key}: {value_str}")
                
                return True
            else:
                print(f"⚠️  Unexpected response type: {type(data)}")
                if isinstance(data, dict) and "error" in data:
                    print(f"❌ API Error: {data['error']}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Run all APIFootball data tests."""
    print("🧪 APIFOOTBALL DATA STRUCTURE TEST")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Load API key
    api_key = load_api_key()
    if not api_key:
        return False
    
    # Run tests
    tests = [
        ("Basic API", lambda: test_basic_api_call(api_key)),
        ("Fixtures API", lambda: test_fixtures_api_call(api_key)),
        ("Odds API", lambda: test_odds_api_call(api_key)),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n🔬 Running: {test_name}")
            print("-" * 40)
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed >= 2:
        print("\n🎉 APIFOOTBALL API IS WORKING!")
        print("💡 Key findings:")
        print("   • API connection successful")
        print("   • Fixture data available")
        print("   • Check console output for data structure details")
        
        print("\n🔧 Next steps:")
        print("   • Review the fixture data structure above")
        print("   • Check if odds fields are available")
        print("   • Update prediction pipeline to handle the data correctly")
        
    else:
        print(f"\n⚠️  API ISSUES DETECTED")
        print("🔧 Please check:")
        print("   • API key validity")
        print("   • Internet connection")
        print("   • API quota limits")
    
    return passed >= 2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
