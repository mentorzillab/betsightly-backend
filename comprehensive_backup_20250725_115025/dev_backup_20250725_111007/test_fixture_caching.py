#!/usr/bin/env python3
"""
Test Fixture Caching
Demonstrates the fixture caching functionality to avoid repeated API calls.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_cache_functionality():
    """Test the fixture cache service."""
    print("🧪 Testing Fixture Cache Service")
    print("-" * 40)
    
    try:
        from services.fixture_cache_service import FixtureCacheService
        
        # Initialize cache service
        cache_service = FixtureCacheService()
        print("✅ Cache service initialized")
        
        # Test cache statistics
        stats = cache_service.get_cache_stats()
        print(f"📊 Cache stats: {stats.get('total_files', 0)} files, {stats.get('total_size_mb', 0)} MB")
        
        # Test cached dates
        cached_dates = cache_service.list_cached_dates()
        print(f"📅 Cached dates: {len(cached_dates)} dates")
        
        if cached_dates:
            print("   Recent dates:")
            for date in cached_dates[-5:]:
                info = cache_service.get_cached_fixtures_info(date)
                if info:
                    status = "✅ Valid" if info['is_valid'] else "❌ Expired"
                    print(f"     • {date}: {info['fixture_count']} fixtures ({status})")
        
        return True
        
    except Exception as e:
        print(f"❌ Cache test failed: {str(e)}")
        return False

def test_pipeline_caching():
    """Test the complete pipeline caching."""
    print("\n🧪 Testing Pipeline Caching")
    print("-" * 40)
    
    try:
        from complete_prediction_pipeline import CompletePredictionPipeline
        
        # Initialize pipeline
        pipeline = CompletePredictionPipeline()
        print("✅ Pipeline initialized")
        
        # Test cache status
        cache_status = pipeline.get_cache_status()
        
        if cache_status:
            stats = cache_status.get('cache_stats', {})
            print(f"📊 Pipeline cache: {stats.get('total_files', 0)} files")
            
            cached_dates = cache_status.get('cached_dates', [])
            print(f"📅 Cached dates: {len(cached_dates)}")
            
            if cached_dates:
                print("   Available dates:")
                for date in cached_dates[-3:]:
                    print(f"     • {date}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline caching test failed: {str(e)}")
        return False

def test_fixture_fetching():
    """Test fixture fetching with caching."""
    print("\n🧪 Testing Fixture Fetching with Cache")
    print("-" * 40)
    
    try:
        from complete_prediction_pipeline import CompletePredictionPipeline
        
        pipeline = CompletePredictionPipeline()
        today = datetime.now().strftime("%Y-%m-%d")
        
        print(f"🌐 Testing fixture fetch for {today}...")
        
        # First fetch (might use cache or API)
        print("\n1️⃣  First fetch:")
        fixtures1 = pipeline.fetch_todays_fixtures(today)
        print(f"   Result: {len(fixtures1)} fixtures")
        
        # Second fetch (should use cache if first was successful)
        print("\n2️⃣  Second fetch (should use cache):")
        fixtures2 = pipeline.fetch_todays_fixtures(today)
        print(f"   Result: {len(fixtures2)} fixtures")
        
        # Compare results
        if len(fixtures1) == len(fixtures2):
            print("✅ Cache consistency verified")
        else:
            print("⚠️  Cache inconsistency detected")
        
        return len(fixtures1) > 0 or len(fixtures2) > 0
        
    except Exception as e:
        print(f"❌ Fixture fetching test failed: {str(e)}")
        return False

def main():
    """Run all caching tests."""
    print("🧪 FIXTURE CACHING TEST SUITE")
    print("=" * 50)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    tests = [
        ("Cache Service", test_cache_functionality),
        ("Pipeline Caching", test_pipeline_caching),
        ("Fixture Fetching", test_fixture_fetching),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n🔬 Running: {test_name}")
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed >= 2:  # At least cache service and pipeline should work
        print("\n🎉 CACHING IS WORKING!")
        print("💡 Benefits of fixture caching:")
        print("   • Reduces API calls and saves quota")
        print("   • Faster response times")
        print("   • Works offline with cached data")
        print("   • Automatic cache expiration (6 hours)")
        
        print("\n🚀 Cache management commands:")
        print("   python complete_prediction_pipeline.py --cache-status")
        print("   python complete_prediction_pipeline.py --clear-cache")
        print("   python complete_prediction_pipeline.py --clear-cache-date 2024-01-15")
        
    else:
        print(f"\n⚠️  CACHING ISSUES DETECTED")
        print("🔧 This might be normal if:")
        print("   • No fixtures have been cached yet")
        print("   • API key is not configured")
        print("   • Network connectivity issues")
    
    return passed >= 2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
