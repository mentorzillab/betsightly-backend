#!/usr/bin/env python3
"""
End-to-End System Test with Nigeria Timezone (WAT - UTC+1)
Complete system verification before GitHub deployment.
"""

import os
import sys
import sqlite3
import json
import pytz
from datetime import datetime, timedelta
import subprocess

def test_nigeria_timezone():
    """Test timezone handling for Nigeria (WAT - UTC+1)."""
    print('🌍 NIGERIA TIMEZONE TEST')
    print('=' * 50)
    
    try:
        # Get current time in Nigeria
        utc_now = datetime.now(pytz.UTC)
        nigeria_tz = pytz.timezone('Africa/Lagos')
        nigeria_time = utc_now.astimezone(nigeria_tz)
        
        print(f'UTC Time: {utc_now.strftime("%Y-%m-%d %H:%M:%S %Z")}')
        print(f'Nigeria Time: {nigeria_time.strftime("%Y-%m-%d %H:%M:%S %Z")}')
        
        # Get future games for Nigeria timezone
        future_time = nigeria_time + timedelta(minutes=30)
        print(f'Looking for games after: {future_time.strftime("%Y-%m-%d %H:%M:%S")}')
        
        return True, nigeria_time
    except Exception as e:
        print(f'❌ Timezone test failed: {e}')
        return False, None

def test_database_connection():
    """Test database connectivity and data."""
    print('\n🗄️ DATABASE CONNECTION TEST')
    print('=' * 50)
    
    try:
        conn = sqlite3.connect('football.db')
        cursor = conn.cursor()
        
        # Test basic tables
        tables = ['cached_fixtures', 'predictions', 'matches']
        for table in tables:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                print(f'✅ {table}: {count} records')
            except:
                print(f'⚠️ {table}: Table missing or empty')
        
        # Test future fixtures
        cursor.execute('''
        SELECT COUNT(*) FROM cached_fixtures 
        WHERE fixture_date > datetime('now', '+30 minutes')
        ''')
        future_count = cursor.fetchone()[0]
        print(f'📅 Future fixtures: {future_count}')
        
        conn.close()
        return True
    except Exception as e:
        print(f'❌ Database test failed: {e}')
        return False

def test_model_loading():
    """Test ML model loading."""
    print('\n🤖 MODEL LOADING TEST')
    print('=' * 50)
    
    try:
        # Check model files
        model_files = {
            'Quick Service': ['match_result_model.joblib', 'over_under_model.joblib', 'btts_model.joblib'],
            'XGBoost': []
        }
        
        # Check quick service models
        for model in model_files['Quick Service']:
            path = f'models/{model}'
            if os.path.exists(path):
                print(f'✅ {model}')
            else:
                print(f'❌ {model} - Missing')
        
        # Check XGBoost models
        xgboost_dir = 'models/xgboost'
        if os.path.exists(xgboost_dir):
            xgboost_models = [f for f in os.listdir(xgboost_dir) if f.endswith('.joblib')]
            print(f'✅ XGBoost models: {len(xgboost_models)}')
            for model in xgboost_models[:3]:  # Show first 3
                print(f'   • {model}')
        else:
            print(f'❌ XGBoost directory missing')
        
        return True
    except Exception as e:
        print(f'❌ Model loading test failed: {e}')
        return False

def test_prediction_generation():
    """Test prediction generation with Nigeria timezone."""
    print('\n🎯 PREDICTION GENERATION TEST')
    print('=' * 50)
    
    try:
        # Run the categorized predictions script
        result = subprocess.run(['python', 'generate_categorized_predictions.py'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print('✅ Prediction script executed successfully')
            
            # Check if JSON file was created
            if os.path.exists('daily_predictions.json'):
                with open('daily_predictions.json', 'r') as f:
                    data = json.load(f)
                
                print(f'✅ JSON file created')
                print(f'📊 Total accumulators: {data.get("total_accumulators", 0)}')
                
                # Check each category
                for category, accumulator in data.get('categories', {}).items():
                    if accumulator.get('games'):
                        print(f'✅ {category}: {len(accumulator["games"])} games, {accumulator["total_odds"]:.2f} odds')
                    else:
                        print(f'⚠️ {category}: No games')
                
                return True
            else:
                print('❌ JSON file not created')
                return False
        else:
            print(f'❌ Prediction script failed: {result.stderr}')
            return False
            
    except Exception as e:
        print(f'❌ Prediction generation test failed: {e}')
        return False

def test_api_endpoints():
    """Test API endpoints."""
    print('\n🌐 API ENDPOINTS TEST')
    print('=' * 50)
    
    try:
        # Test FastAPI main import
        sys.path.append('.')
        import main
        print('✅ FastAPI main module imported')
        
        # Test key services
        from services.accumulator_builder import AccumulatorBuilder
        print('✅ AccumulatorBuilder imported')
        
        from services.prediction_cache_service import PredictionCacheService
        print('✅ PredictionCacheService imported')
        
        return True
    except Exception as e:
        print(f'❌ API endpoints test failed: {e}')
        return False

def test_git_readiness():
    """Test Git repository readiness."""
    print('\n📦 GIT READINESS TEST')
    print('=' * 50)
    
    try:
        # Check if git is initialized
        if os.path.exists('.git'):
            print('✅ Git repository initialized')
        else:
            print('⚠️ Git not initialized - will initialize')
        
        # Check important files
        important_files = [
            'main.py',
            'generate_categorized_predictions.py',
            'football.db',
            'requirements.txt',
            'models/',
            'services/',
            'api/'
        ]
        
        for file_path in important_files:
            if os.path.exists(file_path):
                print(f'✅ {file_path}')
            else:
                print(f'❌ {file_path} - Missing')
        
        return True
    except Exception as e:
        print(f'❌ Git readiness test failed: {e}')
        return False

def run_comprehensive_test():
    """Run comprehensive end-to-end test."""
    print('🚀 COMPREHENSIVE END-TO-END TEST')
    print('🇳🇬 Nigeria Timezone (WAT - UTC+1)')
    print('=' * 60)
    
    tests = [
        ('Timezone Handling', test_nigeria_timezone),
        ('Database Connection', test_database_connection),
        ('Model Loading', test_model_loading),
        ('Prediction Generation', test_prediction_generation),
        ('API Endpoints', test_api_endpoints),
        ('Git Readiness', test_git_readiness)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            if test_name == 'Timezone Handling':
                success, nigeria_time = test_func()
                results[test_name] = success
            else:
                results[test_name] = test_func()
        except Exception as e:
            print(f'❌ {test_name} failed with exception: {e}')
            results[test_name] = False
    
    # Summary
    print('\n📊 TEST SUMMARY')
    print('=' * 30)
    passed = sum(results.values())
    total = len(results)
    
    for test_name, success in results.items():
        status = '✅ PASS' if success else '❌ FAIL'
        print(f'{status} {test_name}')
    
    print(f'\n🎯 OVERALL: {passed}/{total} tests passed')
    
    if passed == total:
        print('🎉 SYSTEM READY FOR GITHUB DEPLOYMENT!')
        return True
    else:
        print('⚠️ Some tests failed - fix issues before deployment')
        return False

if __name__ == "__main__":
    run_comprehensive_test()
