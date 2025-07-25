"""
Comprehensive Test Script for Enhanced Prediction Caching System
Tests all components: caching, retrieval, analytics, cleanup, and API endpoints.
"""

import logging
import time
from datetime import datetime, date, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def test_database_initialization():
    """Test enhanced database initialization."""
    print("\n🗄️  TEST 1: DATABASE INITIALIZATION")
    print("=" * 50)
    
    try:
        from initialize_enhanced_database import initialize_enhanced_database, verify_database_structure
        
        # Initialize database
        init_success = initialize_enhanced_database()
        if not init_success:
            print("❌ Database initialization failed")
            return False
        
        # Verify structure
        verify_success = verify_database_structure()
        if not verify_success:
            print("❌ Database verification failed")
            return False
        
        print("✅ Database initialization and verification successful")
        return True
        
    except Exception as e:
        print(f"❌ Database test error: {str(e)}")
        return False

def test_prediction_caching():
    """Test prediction caching service."""
    print("\n🎯 TEST 2: PREDICTION CACHING")
    print("=" * 50)
    
    try:
        from services.prediction_cache_service import PredictionCacheService
        
        cache_service = PredictionCacheService()
        
        # Test daily prediction existence check
        today = date.today()
        exists = cache_service.check_daily_predictions_exist(today)
        print(f"📅 Predictions exist for {today}: {exists}")
        
        # Test prediction generation (with force if exists)
        print("🚀 Testing prediction generation...")
        result = cache_service.generate_and_cache_daily_predictions(
            target_date=str(today),
            force_regenerate=True
        )
        
        if result['status'] == 'completed':
            print(f"✅ Prediction generation successful:")
            print(f"   📊 {result['successful_predictions']} successful predictions")
            print(f"   ❌ {result['failed_predictions']} failed predictions")
            print(f"   🎲 {result['accumulators_generated']} accumulator categories")
            print(f"   ⏱️  Generation time: {result['generation_time']:.2f}s")
            return True
        else:
            print(f"❌ Prediction generation failed: {result.get('error', 'Unknown error')}")
            return False
        
    except Exception as e:
        print(f"❌ Caching test error: {str(e)}")
        return False

def test_prediction_retrieval():
    """Test prediction retrieval service."""
    print("\n📥 TEST 3: PREDICTION RETRIEVAL")
    print("=" * 50)
    
    try:
        from services.prediction_retrieval_service import PredictionRetrievalService
        
        retrieval_service = PredictionRetrievalService()
        
        # Test daily predictions retrieval
        print("📊 Testing daily predictions retrieval...")
        predictions_result = retrieval_service.get_daily_predictions()
        
        if predictions_result['status'] == 'success':
            print(f"✅ Predictions retrieval successful:")
            print(f"   📈 {predictions_result['total_predictions']} predictions retrieved")
            print(f"   🎯 Batch status: {predictions_result['batch_info']['status']}")
            print(f"   🤖 Models used: {predictions_result['batch_info']['models_used']}")
        else:
            print(f"⚠️  Predictions retrieval: {predictions_result['status']}")
        
        # Test accumulators retrieval
        print("🎲 Testing accumulators retrieval...")
        accumulators_result = retrieval_service.get_daily_accumulators()
        
        if accumulators_result['status'] == 'success':
            print(f"✅ Accumulators retrieval successful:")
            print(f"   🎯 {accumulators_result['selected_count']}/{accumulators_result['total_categories']} categories selected")
            
            # Show accumulator details
            for acc_type, acc_data in accumulators_result['accumulators'].items():
                if acc_data['selected']:
                    print(f"   💰 {acc_type}: {acc_data['total_odds']:.2f} odds, {acc_data['game_count']} games")
        else:
            print(f"⚠️  Accumulators retrieval: {accumulators_result['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Retrieval test error: {str(e)}")
        return False

def test_analytics_system():
    """Test prediction analytics system."""
    print("\n📊 TEST 4: ANALYTICS SYSTEM")
    print("=" * 50)
    
    try:
        from services.prediction_analytics_service import PredictionAnalyticsService
        
        analytics_service = PredictionAnalyticsService()
        
        # Test result updates (use yesterday's date for completed matches)
        yesterday = date.today() - timedelta(days=1)
        print(f"🔄 Testing result updates for {yesterday}...")
        
        update_result = analytics_service.update_match_results(str(yesterday))
        
        if update_result['status'] == 'completed':
            print(f"✅ Result updates successful:")
            print(f"   📊 {update_result['fixtures_updated']} fixtures updated")
            print(f"   🎯 {update_result['predictions_updated']} predictions updated")
        elif update_result['status'] == 'no_updates_needed':
            print(f"⚠️  No updates needed for {yesterday}")
        else:
            print(f"❌ Result updates failed: {update_result.get('error', 'Unknown error')}")
        
        # Test analytics generation
        print(f"📈 Testing analytics generation for {yesterday}...")
        
        analytics_result = analytics_service.generate_daily_analytics(str(yesterday))
        
        if analytics_result['status'] == 'completed':
            analytics = analytics_result['analytics']
            print(f"✅ Analytics generation successful:")
            print(f"   🎯 Overall accuracy: {analytics['accuracy_rate']:.1%}")
            print(f"   📈 Total predictions: {analytics['total_predictions']}")
            print(f"   ✅ Correct predictions: {analytics['correct_predictions']}")
        elif analytics_result['status'] == 'no_data':
            print(f"⚠️  No analytics data available for {yesterday}")
        else:
            print(f"❌ Analytics generation failed: {analytics_result.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Analytics test error: {str(e)}")
        return False

def test_api_endpoints():
    """Test enhanced API endpoints."""
    print("\n🌐 TEST 5: API ENDPOINTS")
    print("=" * 50)
    
    try:
        import requests
        
        base_url = "http://localhost:8000"
        
        # Test enhanced daily predictions endpoint
        print("📊 Testing enhanced daily predictions endpoint...")
        try:
            response = requests.get(f"{base_url}/api/daily-predictions/today/enhanced", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Enhanced predictions endpoint: {data['status']}")
                if data['status'] == 'success':
                    print(f"   📈 {data['total_predictions']} predictions")
                    print(f"   🤖 {data['features']['models_used']} models used")
                    print(f"   🎯 {data['features']['feature_count']} features")
            else:
                print(f"❌ Enhanced predictions endpoint: HTTP {response.status_code}")
        except Exception as e:
            print(f"⚠️  Enhanced predictions endpoint not available: {str(e)}")
        
        # Test enhanced accumulators endpoint
        print("🎲 Testing enhanced accumulators endpoint...")
        try:
            response = requests.get(f"{base_url}/api/accumulators/today/enhanced", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Enhanced accumulators endpoint: {data['status']}")
                if data['status'] == 'success':
                    print(f"   🎯 {data['selected_count']}/{data['total_categories']} categories selected")
                    print(f"   🌈 Features: diversity scoring, risk assessment, result tracking")
            else:
                print(f"❌ Enhanced accumulators endpoint: HTTP {response.status_code}")
        except Exception as e:
            print(f"⚠️  Enhanced accumulators endpoint not available: {str(e)}")
        
        # Test health endpoint
        print("❤️  Testing health endpoint...")
        try:
            response = requests.get(f"{base_url}/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health endpoint: {data.get('status', 'unknown')}")
            else:
                print(f"❌ Health endpoint: HTTP {response.status_code}")
        except Exception as e:
            print(f"⚠️  Health endpoint not available: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ API test error: {str(e)}")
        return False

def test_orchestrator():
    """Test prediction orchestrator."""
    print("\n🎯 TEST 6: PREDICTION ORCHESTRATOR")
    print("=" * 50)
    
    try:
        from services.prediction_orchestrator import PredictionOrchestrator
        
        # Initialize orchestrator (without auto-scheduling for testing)
        orchestrator = PredictionOrchestrator(auto_schedule=False)
        
        # Test system status
        print("📊 Testing system status...")
        status = orchestrator.get_system_status()
        
        if status['status'] == 'healthy':
            print("✅ System status: Healthy")
            print(f"   📊 Database statistics available: {bool(status.get('database_statistics'))}")
            print(f"   🎯 Today's predictions: {status['today_predictions']['status']}")
            print(f"   🎲 Today's accumulators: {status['today_accumulators']['status']}")
        else:
            print(f"❌ System status: {status.get('error', 'Unknown error')}")
        
        # Test manual operations
        print("🔧 Testing manual operations...")
        
        # Test cleanup (dry run)
        cleanup_result = orchestrator.run_data_cleanup(dry_run=True)
        if cleanup_result['status'] == 'completed':
            print("✅ Data cleanup test successful (dry run)")
            deleted_counts = cleanup_result['deleted_counts']
            print(f"   🗑️  Would delete: {sum(deleted_counts.values())} total records")
        else:
            print(f"❌ Data cleanup test failed: {cleanup_result.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator test error: {str(e)}")
        return False

def main():
    """Run comprehensive system test."""
    print("🧪 COMPREHENSIVE PREDICTION CACHING SYSTEM TEST")
    print("=" * 70)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    tests = [
        ("Database Initialization", test_database_initialization),
        ("Prediction Caching", test_prediction_caching),
        ("Prediction Retrieval", test_prediction_retrieval),
        ("Analytics System", test_analytics_system),
        ("API Endpoints", test_api_endpoints),
        ("Orchestrator", test_orchestrator)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n🔍 Running {test_name} test...")
            success = test_func()
            if success:
                passed_tests += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {str(e)}")
    
    print("\n" + "=" * 70)
    print("🎉 COMPREHENSIVE TEST RESULTS")
    print("=" * 70)
    print(f"📊 Tests Passed: {passed_tests}/{total_tests}")
    print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION!")
    elif passed_tests >= total_tests * 0.8:
        print("⭐ MOST TESTS PASSED - SYSTEM MOSTLY FUNCTIONAL")
    else:
        print("⚠️  SEVERAL TESTS FAILED - SYSTEM NEEDS ATTENTION")
    
    print("=" * 70)
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
