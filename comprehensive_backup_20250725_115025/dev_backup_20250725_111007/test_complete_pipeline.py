#!/usr/bin/env python3
"""
Test Complete Pipeline
Quick test script to verify the complete prediction pipeline works.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from complete_prediction_pipeline import CompletePredictionPipeline

def test_model_availability():
    """Test model availability checking."""
    print("🔍 Testing model availability check...")
    
    try:
        pipeline = CompletePredictionPipeline()
        status = pipeline.check_models_availability()
        
        print(f"✅ Model check completed:")
        print(f"   Available: {status['total_available']}/{status['total_required']}")
        print(f"   Percentage: {status['availability_percentage']:.1f}%")
        print(f"   Sufficient: {'Yes' if status['sufficient'] else 'No'}")
        
        return status['sufficient']
        
    except Exception as e:
        print(f"❌ Model check failed: {str(e)}")
        return False

def test_fixture_fetching():
    """Test fixture fetching from APIFootball."""
    print("\n🌐 Testing fixture fetching...")
    
    try:
        pipeline = CompletePredictionPipeline()
        fixtures = pipeline.fetch_todays_fixtures()
        
        print(f"✅ Fixture fetching completed:")
        print(f"   Found: {len(fixtures)} fixtures")
        
        if fixtures:
            print("   Sample fixtures:")
            for i, fixture in enumerate(fixtures[:3], 1):
                home = fixture.get('home_team', 'Unknown')
                away = fixture.get('away_team', 'Unknown')
                league = fixture.get('league', 'Unknown')
                print(f"     {i}. {home} vs {away} ({league})")
        
        return len(fixtures) > 0
        
    except Exception as e:
        print(f"❌ Fixture fetching failed: {str(e)}")
        return False

def test_api_connection():
    """Test API connection."""
    print("\n🔗 Testing API connections...")
    
    try:
        from services.apifootball_service import APIFootballService
        
        service = APIFootballService()
        
        # Test connection
        if not service.api_key:
            print("⚠️  APIFootball API key not configured")
            return False
        
        print("✅ APIFootball service initialized")
        return True
        
    except Exception as e:
        print(f"❌ API connection test failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("🧪 COMPLETE PIPELINE TEST SUITE")
    print("=" * 50)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    tests = [
        ("API Connection", test_api_connection),
        ("Model Availability", test_model_availability),
        ("Fixture Fetching", test_fixture_fetching),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running: {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   Result: {status}")
        except Exception as e:
            results[test_name] = False
            print(f"   Result: ❌ ERROR - {str(e)}")
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("💡 The complete pipeline should work correctly")
        print("\n🚀 Ready to run:")
        print("   python complete_prediction_pipeline.py")
        print("   python run_daily_predictions.py")
    else:
        print(f"\n⚠️  {total - passed} TESTS FAILED")
        print("🔧 Please check the configuration and dependencies")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
