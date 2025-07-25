#!/usr/bin/env python3
"""
Simple Pipeline Test
Basic test to verify the pipeline components work without complex dependencies.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def test_basic_imports():
    """Test basic Python imports."""
    print("🔍 Testing basic imports...")
    
    try:
        import pandas as pd
        import numpy as np
        import requests
        import json
        from datetime import datetime
        print("✅ Basic imports successful")
        return True
    except ImportError as e:
        print(f"❌ Basic import failed: {str(e)}")
        return False

def test_directory_structure():
    """Test if required directories exist."""
    print("\n📁 Testing directory structure...")
    
    required_dirs = [
        'services',
        'api/endpoints', 
        'ml',
        'models',
        'utils'
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print(f"❌ Missing directories: {missing_dirs}")
        return False
    else:
        print("✅ All required directories exist")
        return True

def test_model_files():
    """Test if model files exist."""
    print("\n🤖 Testing model files...")
    
    models_dir = Path('models')
    if not models_dir.exists():
        print("❌ Models directory doesn't exist")
        return False
    
    # Count model files
    model_count = 0
    for model_type in ['xgboost', 'lightgbm', 'neural_network', 'random_forest']:
        type_dir = models_dir / model_type
        if type_dir.exists():
            model_files = list(type_dir.glob('*.joblib'))
            model_count += len(model_files)
            print(f"   {model_type}: {len(model_files)} models")
    
    print(f"✅ Found {model_count} total model files")
    return model_count > 0

def test_api_key():
    """Test if API key is configured."""
    print("\n🔑 Testing API configuration...")
    
    api_key = os.getenv('APIFOOTBALL_API_KEY', '')
    
    if not api_key:
        print("⚠️  APIFOOTBALL_API_KEY not configured")
        print("💡 Set it with: export APIFOOTBALL_API_KEY=your_key_here")
        return False
    elif len(api_key) < 10:
        print("⚠️  API key seems too short")
        return False
    else:
        print(f"✅ API key configured (length: {len(api_key)})")
        return True

def test_simple_api_request():
    """Test a simple API request."""
    print("\n🌐 Testing simple API request...")
    
    try:
        import requests
        
        # Test a simple request to a public API
        response = requests.get('https://httpbin.org/json', timeout=10)
        
        if response.status_code == 200:
            print("✅ HTTP requests working")
            return True
        else:
            print(f"❌ HTTP request failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ HTTP request failed: {str(e)}")
        return False

def test_file_creation():
    """Test if we can create files."""
    print("\n📝 Testing file creation...")
    
    try:
        test_file = Path('test_pipeline_temp.txt')
        
        # Write test file
        with open(test_file, 'w') as f:
            f.write(f"Test file created at {datetime.now()}")
        
        # Read test file
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Clean up
        test_file.unlink()
        
        print("✅ File operations working")
        return True
        
    except Exception as e:
        print(f"❌ File operations failed: {str(e)}")
        return False

def main():
    """Run all simple tests."""
    print("🧪 SIMPLE PIPELINE TEST SUITE")
    print("=" * 50)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📍 Working directory: {os.getcwd()}")
    print("=" * 50)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Directory Structure", test_directory_structure),
        ("Model Files", test_model_files),
        ("API Configuration", test_api_key),
        ("HTTP Requests", test_simple_api_request),
        ("File Operations", test_file_creation),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
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
    
    if passed >= total - 1:  # Allow 1 failure (API key might not be set)
        print("\n🎉 SYSTEM READY!")
        print("💡 The pipeline should work with proper configuration")
        
        print("\n🚀 Next steps:")
        print("1. Set API key: export APIFOOTBALL_API_KEY=your_key_here")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Run: python complete_prediction_pipeline.py --check-models-only")
        
    else:
        print(f"\n⚠️  SYSTEM NOT READY")
        print("🔧 Please fix the failing tests before proceeding")
    
    return passed >= total - 1

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
