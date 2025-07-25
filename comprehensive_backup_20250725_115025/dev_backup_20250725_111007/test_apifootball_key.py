#!/usr/bin/env python3
"""
Test APIFootball Key
Check if the APIFootball API key is available and working.
"""

import os
import sys
import requests
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def load_env_file():
    """Load environment variables from .env file."""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env file loaded")
        return True
    except ImportError:
        # Manual parsing if python-dotenv not available
        print("⚠️  python-dotenv not available, parsing manually...")
        
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        
        print("✅ .env file parsed manually")
        return True

def check_api_key():
    """Check if APIFootball API key is available."""
    print("🔑 Checking APIFootball API key...")
    
    api_key = os.getenv('APIFOOTBALL_API_KEY', '')
    
    if not api_key:
        print("❌ APIFOOTBALL_API_KEY not found in environment")
        return None
    
    if len(api_key) < 10:
        print(f"⚠️  API key seems too short: {len(api_key)} characters")
        return None
    
    print(f"✅ API key found: {api_key[:10]}...{api_key[-4:]} ({len(api_key)} chars)")
    return api_key

def test_api_connection(api_key):
    """Test APIFootball API connection."""
    print("\n🌐 Testing APIFootball API connection...")
    
    try:
        # APIFootball.com test endpoint
        url = "https://apiv3.apifootball.com/"
        params = {
            "action": "get_countries",
            "APIkey": api_key
        }
        
        print(f"📡 Making request to: {url}")
        print(f"🔧 Parameters: action=get_countries")
        
        response = requests.get(url, params=params, timeout=30)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, dict) and "error" in data:
                print(f"❌ API Error: {data['error']}")
                return False
            elif isinstance(data, list) and len(data) > 0:
                print(f"✅ API connection successful!")
                print(f"📊 Received {len(data)} countries")
                print(f"🌍 Sample countries: {[country.get('country_name', 'Unknown') for country in data[:3]]}")
                return True
            else:
                print(f"⚠️  Unexpected response format: {type(data)}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"📄 Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout - API might be slow")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - check internet connection")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_fixtures_endpoint(api_key):
    """Test fixtures endpoint."""
    print("\n📅 Testing fixtures endpoint...")
    
    try:
        url = "https://apiv3.apifootball.com/"
        today = datetime.now().strftime("%Y-%m-%d")
        
        params = {
            "action": "get_events",
            "from": today,
            "to": today,
            "APIkey": api_key
        }
        
        print(f"📡 Getting fixtures for: {today}")
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, dict) and "error" in data:
                print(f"❌ API Error: {data['error']}")
                return False
            elif isinstance(data, list):
                print(f"✅ Fixtures endpoint working!")
                print(f"📊 Found {len(data)} fixtures for today")
                
                if len(data) > 0:
                    sample = data[0]
                    home = sample.get('match_hometeam_name', 'Unknown')
                    away = sample.get('match_awayteam_name', 'Unknown')
                    league = sample.get('league_name', 'Unknown')
                    print(f"🏆 Sample fixture: {home} vs {away} ({league})")
                
                return True
            else:
                print(f"⚠️  Unexpected response: {type(data)}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing fixtures: {str(e)}")
        return False

def main():
    """Main test function."""
    print("🔍 APIFOOTBALL API KEY TEST")
    print("=" * 50)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Step 1: Load environment
    if not load_env_file():
        print("\n❌ Could not load environment variables")
        return False
    
    # Step 2: Check API key
    api_key = check_api_key()
    if not api_key:
        print("\n❌ No valid API key found")
        print("\n💡 To fix this:")
        print("1. Get API key from: https://apifootball.com/")
        print("2. Add to .env file: APIFOOTBALL_API_KEY=your_key_here")
        print("3. Or set environment: export APIFOOTBALL_API_KEY=your_key_here")
        return False
    
    # Step 3: Test API connection
    connection_ok = test_api_connection(api_key)
    if not connection_ok:
        print("\n❌ API connection failed")
        return False
    
    # Step 4: Test fixtures endpoint
    fixtures_ok = test_fixtures_endpoint(api_key)
    if not fixtures_ok:
        print("\n⚠️  Fixtures endpoint had issues (might be normal if no games today)")
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    print(f"✅ API Key: Available")
    print(f"✅ Connection: {'Working' if connection_ok else 'Failed'}")
    print(f"{'✅' if fixtures_ok else '⚠️ '} Fixtures: {'Working' if fixtures_ok else 'Limited'}")
    
    if connection_ok:
        print("\n🎉 APIFOOTBALL API IS READY!")
        print("💡 You can now run the complete prediction pipeline:")
        print("   python run_daily_predictions.py")
        print("   python complete_prediction_pipeline.py")
        return True
    else:
        print("\n❌ API NOT READY")
        print("🔧 Please check your API key and internet connection")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
