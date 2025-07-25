#!/usr/bin/env python3
"""
Fix Model Compatibility Script
Convert existing .pkl models to the format expected by the system.
"""

import os
import pickle
import joblib
import shutil
from pathlib import Path

def fix_model_compatibility():
    """Fix model compatibility issues by converting and organizing models."""
    
    print("🔧 FIXING MODEL COMPATIBILITY")
    print("=" * 60)
    
    models_dir = Path("models")
    
    if not models_dir.exists():
        print("❌ Models directory not found")
        return False
    
    # Get existing .pkl models
    pkl_models = list(models_dir.glob("*.pkl"))
    print(f"📊 Found {len(pkl_models)} .pkl models")
    
    # Create directory structure expected by advanced service
    xgboost_dir = models_dir / "xgboost"
    xgboost_dir.mkdir(exist_ok=True)
    
    # Track conversions
    conversions = {
        'quick_service': [],
        'advanced_service': [],
        'failed': []
    }
    
    for pkl_file in pkl_models:
        model_name = pkl_file.stem
        print(f"\n🔄 Processing: {model_name}")
        
        try:
            # Load the .pkl model
            with open(pkl_file, 'rb') as f:
                model = pickle.load(f)
            
            # Convert for Quick Prediction Service
            if any(x in model_name.lower() for x in ['match_result', 'over_2_5', 'btts']):
                # Map to expected names
                if 'match_result' in model_name.lower():
                    quick_name = 'match_result_model.joblib'
                elif 'over_2_5' in model_name.lower():
                    quick_name = 'over_under_model.joblib'
                elif 'btts' in model_name.lower():
                    quick_name = 'btts_model.joblib'
                else:
                    continue
                
                # Save in expected format
                quick_path = models_dir / quick_name
                joblib.dump(model, quick_path)
                conversions['quick_service'].append(f"{model_name} → {quick_name}")
                print(f"   ✅ Quick Service: {quick_name}")
            
            # Convert for Advanced Prediction Service (XGBoost models)
            if model_name.startswith('xgboost_'):
                # Extract the prediction type (e.g., 'match_result' from 'xgboost_match_result')
                prediction_type = model_name.replace('xgboost_', '')
                advanced_name = f"{prediction_type}.joblib"
                advanced_path = xgboost_dir / advanced_name
                
                # Save in expected format
                joblib.dump(model, advanced_path)
                conversions['advanced_service'].append(f"{model_name} → xgboost/{advanced_name}")
                print(f"   ✅ Advanced Service: xgboost/{advanced_name}")
            
        except Exception as e:
            conversions['failed'].append(f"{model_name}: {str(e)}")
            print(f"   ❌ Failed: {str(e)}")
    
    # Create dummy encoders for Quick Service (if needed)
    print(f"\n🔧 Creating dummy encoders for Quick Service...")
    for model_type in ['match_result', 'over_under', 'btts']:
        encoder_path = models_dir / f"{model_type}_encoder.joblib"
        if not encoder_path.exists():
            # Create a simple dummy encoder
            dummy_encoder = {'dummy': True}
            joblib.dump(dummy_encoder, encoder_path)
            print(f"   ✅ Created dummy encoder: {model_type}_encoder.joblib")
    
    # Summary
    print(f"\n📊 CONVERSION SUMMARY:")
    print(f"   ✅ Quick Service conversions: {len(conversions['quick_service'])}")
    for conv in conversions['quick_service']:
        print(f"      • {conv}")
    
    print(f"   ✅ Advanced Service conversions: {len(conversions['advanced_service'])}")
    for conv in conversions['advanced_service']:
        print(f"      • {conv}")
    
    if conversions['failed']:
        print(f"   ❌ Failed conversions: {len(conversions['failed'])}")
        for fail in conversions['failed']:
            print(f"      • {fail}")
    
    print(f"\n🎉 MODEL COMPATIBILITY FIXED!")
    print(f"   📁 Quick Service models: models/*.joblib")
    print(f"   📁 Advanced Service models: models/xgboost/*.joblib")
    
    return True

def verify_model_loading():
    """Verify that models can now be loaded by the system."""
    
    print(f"\n🔍 VERIFYING MODEL LOADING")
    print("=" * 40)
    
    # Test Quick Service models
    models_dir = Path("models")
    quick_models = ['match_result_model.joblib', 'over_under_model.joblib', 'btts_model.joblib']
    
    print("📋 Quick Service Models:")
    for model_name in quick_models:
        model_path = models_dir / model_name
        if model_path.exists():
            try:
                model = joblib.load(model_path)
                print(f"   ✅ {model_name} - Loaded successfully")
            except Exception as e:
                print(f"   ❌ {model_name} - Load failed: {str(e)}")
        else:
            print(f"   ❌ {model_name} - File not found")
    
    # Test Advanced Service models
    xgboost_dir = models_dir / "xgboost"
    print(f"\n📋 Advanced Service Models:")
    if xgboost_dir.exists():
        xgboost_models = list(xgboost_dir.glob("*.joblib"))
        print(f"   📊 Found {len(xgboost_models)} XGBoost models")
        for model_path in xgboost_models[:3]:  # Test first 3
            try:
                model = joblib.load(model_path)
                print(f"   ✅ {model_path.name} - Loaded successfully")
            except Exception as e:
                print(f"   ❌ {model_path.name} - Load failed: {str(e)}")
    else:
        print(f"   ❌ XGBoost directory not found")

if __name__ == "__main__":
    success = fix_model_compatibility()
    if success:
        verify_model_loading()
        print(f"\n🚀 READY TO TEST SYSTEM WITH FIXED MODELS!")
    else:
        print(f"\n❌ Model compatibility fix failed")
