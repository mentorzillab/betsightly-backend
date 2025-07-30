#!/usr/bin/env python3
"""
🧪 TEST UPDATED PREDICTION SERVICE
Test the updated advanced prediction service to ensure it can fetch real fixtures.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_advanced_prediction_service():
    """Test the updated advanced prediction service."""
    print("🧪 TESTING UPDATED ADVANCED PREDICTION SERVICE")
    print("=" * 60)
    
    try:
        # Import the updated service
        from services.advanced_prediction_service import AdvancedPredictionService
        
        print("🚀 Initializing Advanced Prediction Service...")
        service = AdvancedPredictionService()
        
        print(f"✅ Service initialized successfully")
        print(f"🔑 APIFootball key configured: {'Yes' if service.apifootball_api_key else 'No'}")
        print(f"🤖 Models loaded: {service.models_loaded}")
        
        # Test fixture fetching for tomorrow
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"\n📅 Testing fixture fetching for {tomorrow}...")
        
        # Test the internal fixture fetching method
        fixtures = service._get_fixtures_from_api(tomorrow)
        
        print(f"✅ Fetched {len(fixtures)} fixtures from API")
        
        if fixtures:
            print("⚽ Sample fixtures:")
            for i, fixture in enumerate(fixtures[:3]):
                home_team = fixture.get('home_team', 'Unknown')
                away_team = fixture.get('away_team', 'Unknown')
                league = fixture.get('league_name', 'Unknown League')
                date = fixture.get('date', 'Unknown')
                
                print(f"   {i+1}. {home_team} vs {away_team}")
                print(f"      🏆 League: {league}")
                print(f"      📅 Date: {date}")
        
        # Test full prediction generation
        print(f"\n🎯 Testing full prediction generation for {tomorrow}...")
        result = service.get_predictions_for_date(tomorrow)
        
        print(f"📊 Prediction result status: {result.get('status', 'unknown')}")
        print(f"🎯 Total predictions: {len(result.get('predictions', []))}")
        print(f"📈 Total fixtures processed: {result.get('metadata', {}).get('total_fixtures', 0)}")
        
        # Show categories
        categories = result.get('categories', {})
        print(f"\n🎲 Predictions by category:")
        for category, preds in categories.items():
            print(f"   • {category}: {len(preds)} predictions")
        
        # Show sample predictions if available
        predictions = result.get('predictions', [])
        if predictions:
            print(f"\n⚽ Sample predictions:")
            for i, pred in enumerate(predictions[:2]):
                home_team = pred.get('home_team', 'Unknown')
                away_team = pred.get('away_team', 'Unknown')
                prediction = pred.get('prediction', 'Unknown')
                confidence = pred.get('confidence', 0)
                odds = pred.get('odds', 0)
                
                print(f"   {i+1}. {home_team} vs {away_team}")
                print(f"      🎯 Prediction: {prediction}")
                print(f"      📊 Confidence: {confidence:.1%}")
                print(f"      💰 Odds: {odds:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing advanced prediction service: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🔧 TESTING UPDATED PREDICTION SERVICE CONFIGURATION")
    print("=" * 80)
    
    success = test_advanced_prediction_service()
    
    print(f"\n📋 TEST RESULT: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    if success:
        print("🎉 The prediction service is now configured to use real API data!")
        print("🚀 Ready to generate real predictions with the multi-day system!")
    else:
        print("🔧 Please check the configuration and try again.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
