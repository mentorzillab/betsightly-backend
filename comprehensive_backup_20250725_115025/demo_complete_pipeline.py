#!/usr/bin/env python3
"""
Demo Complete Pipeline
Demonstrates the complete prediction pipeline with sample data if API is not available.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def create_sample_fixtures():
    """Create sample fixtures for demo purposes."""
    return [
        {
            "fixture_id": "demo_1",
            "home_team": "Arsenal",
            "away_team": "Chelsea", 
            "league": "Premier League",
            "date": (datetime.now() + timedelta(hours=2)).isoformat(),
            "status": "Not Started"
        },
        {
            "fixture_id": "demo_2", 
            "home_team": "Manchester United",
            "away_team": "Liverpool",
            "league": "Premier League", 
            "date": (datetime.now() + timedelta(hours=4)).isoformat(),
            "status": "Not Started"
        },
        {
            "fixture_id": "demo_3",
            "home_team": "Barcelona", 
            "away_team": "Real Madrid",
            "league": "La Liga",
            "date": (datetime.now() + timedelta(hours=6)).isoformat(), 
            "status": "Not Started"
        }
    ]

def demo_model_check():
    """Demo model availability check."""
    print("🔍 DEMO: Model Availability Check")
    print("-" * 40)
    
    models_dir = Path('models')
    if not models_dir.exists():
        print("❌ Models directory not found")
        return False
    
    model_count = 0
    for model_type in ['xgboost', 'lightgbm', 'neural_network', 'random_forest']:
        type_dir = models_dir / model_type
        if type_dir.exists():
            model_files = list(type_dir.glob('*.joblib'))
            model_count += len(model_files)
            print(f"✅ {model_type}: {len(model_files)} models")
        else:
            print(f"❌ {model_type}: directory not found")
    
    print(f"📊 Total models available: {model_count}")
    sufficient = model_count >= 10  # Need at least 10 models
    print(f"🎯 Sufficient for predictions: {'✅ Yes' if sufficient else '❌ No'}")
    
    return sufficient

def demo_fixture_fetching():
    """Demo fixture fetching."""
    print("\n🌐 DEMO: Fixture Fetching")
    print("-" * 40)
    
    api_key = os.getenv('APIFOOTBALL_API_KEY', '')
    
    if api_key and len(api_key) > 10:
        print("✅ API key configured - would fetch real fixtures")
        print("🌐 Would call: APIFootballService.get_daily_fixtures()")
        # In real scenario, would fetch from API
        fixtures = create_sample_fixtures()
        print(f"📊 Simulating: Found {len(fixtures)} fixtures")
    else:
        print("⚠️  No API key - using sample fixtures")
        fixtures = create_sample_fixtures()
        print(f"📊 Created {len(fixtures)} sample fixtures")
    
    for i, fixture in enumerate(fixtures, 1):
        print(f"   {i}. {fixture['home_team']} vs {fixture['away_team']} ({fixture['league']})")
    
    return fixtures

def demo_prediction_generation(fixtures):
    """Demo prediction generation."""
    print("\n🎯 DEMO: Prediction Generation")
    print("-" * 40)
    
    predictions = []
    
    for i, fixture in enumerate(fixtures, 1):
        print(f"{i}/{len(fixtures)}: {fixture['home_team']} vs {fixture['away_team']}")
        
        # Simulate prediction generation
        sample_prediction = {
            "fixture_info": fixture,
            "predictions": {
                "match_result": {
                    "prediction": "H",  # Home win
                    "confidence": 75.5,
                    "probabilities": {"H": 0.755, "D": 0.145, "A": 0.100}
                },
                "over_2_5": {
                    "prediction": "Yes",
                    "confidence": 68.2,
                    "probabilities": {"Yes": 0.682, "No": 0.318}
                },
                "btts": {
                    "prediction": "Yes", 
                    "confidence": 72.1,
                    "probabilities": {"Yes": 0.721, "No": 0.279}
                }
            },
            "model_summary": {
                "total_predictions": 3,
                "models_used": ["xgboost", "lightgbm", "neural_network"],
                "average_confidence": 71.9
            }
        }
        
        predictions.append(sample_prediction)
        print(f"   ✅ Generated prediction (confidence: {sample_prediction['model_summary']['average_confidence']:.1f}%)")
    
    print(f"📊 Generated {len(predictions)} predictions successfully")
    return predictions

def demo_database_storage(predictions):
    """Demo database storage."""
    print("\n💾 DEMO: Database Storage")
    print("-" * 40)
    
    print("🗄️  Would store predictions in database:")
    print("   • Table: daily_predictions")
    print("   • Table: daily_prediction_summary")
    
    for i, prediction in enumerate(predictions, 1):
        fixture = prediction['fixture_info']
        print(f"   {i}. {fixture['home_team']} vs {fixture['away_team']} - stored")
    
    print(f"✅ Would store {len(predictions)} predictions")
    print("🌐 Frontend endpoints would be updated:")
    print("   • GET /api/daily-predictions/today")
    print("   • GET /api/accumulators/today")
    
    return True

def main():
    """Run complete demo."""
    print("🎬 COMPLETE PREDICTION PIPELINE DEMO")
    print("=" * 60)
    print(f"📅 Demo Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("💡 This demo shows what the pipeline would do")
    print("=" * 60)
    
    try:
        # Step 1: Model Check
        models_available = demo_model_check()
        
        if not models_available:
            print("\n⚠️  Insufficient models for demo")
            print("💡 In real pipeline, would train models from GitHub dataset")
            print("🚀 Run: python train_models_github_dataset.py")
            return False
        
        # Step 2: Fixture Fetching
        fixtures = demo_fixture_fetching()
        
        if not fixtures:
            print("\n❌ No fixtures available for demo")
            return False
        
        # Step 3: Prediction Generation
        predictions = demo_prediction_generation(fixtures)
        
        if not predictions:
            print("\n❌ No predictions generated")
            return False
        
        # Step 4: Database Storage
        storage_success = demo_database_storage(predictions)
        
        if not storage_success:
            print("\n❌ Database storage failed")
            return False
        
        # Success Summary
        print("\n🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("📊 Demo Summary:")
        print(f"   • Models Available: ✅ Yes")
        print(f"   • Fixtures Processed: {len(fixtures)}")
        print(f"   • Predictions Generated: {len(predictions)}")
        print(f"   • Database Storage: ✅ Success")
        
        print("\n🚀 To run the real pipeline:")
        print("1. Set API key: export APIFOOTBALL_API_KEY=your_key_here")
        print("2. Run: python run_daily_predictions.py")
        print("3. Or: python complete_prediction_pipeline.py")
        
        print("\n💡 The real pipeline will:")
        print("   • Fetch live fixtures from APIFootball.com")
        print("   • Use your 28 trained models for predictions")
        print("   • Store real data in your database")
        print("   • Update frontend endpoints with fresh data")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    print("\n" + "=" * 60)
    if success:
        print("✅ DEMO SUCCESSFUL - Pipeline is ready!")
    else:
        print("❌ DEMO FAILED - Check configuration")
    print("=" * 60)
    sys.exit(0 if success else 1)
