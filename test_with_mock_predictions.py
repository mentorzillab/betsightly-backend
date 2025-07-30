#!/usr/bin/env python3
"""
🧪 TEST MULTI-DAY PREDICTIONS WITH MOCK DATA
Demonstrate the full functionality of the multi-day prediction system with sample data.
"""

import json
import pytz
from datetime import datetime, timedelta
from format_and_save_predictions import format_and_save_from_results

def create_mock_prediction_results():
    """Create mock prediction results to demonstrate the system functionality."""
    
    # Calculate dates
    nigeria_tz = pytz.timezone('Africa/Lagos')
    utc_now = datetime.now(pytz.UTC)
    nigeria_time = utc_now.astimezone(nigeria_tz)
    tomorrow = nigeria_time + timedelta(days=1)
    
    # Mock predictions for demonstration
    mock_predictions = [
        {
            "home_team": "Arsenal",
            "away_team": "Chelsea",
            "league": "Premier League",
            "prediction": "Home Win",
            "confidence": 0.75,
            "odds": 2.1,
            "category": "2_odds",
            "nigeria_datetime": "2025-07-31 15:30:00 WAT",
            "nigeria_date": "2025-07-31",
            "nigeria_time": "15:30",
            "day_of_week": "Thursday",
            "prediction_generated_at": nigeria_time.strftime('%Y-%m-%d %H:%M:%S WAT'),
            "prediction_type": "Home Win",
            "confidence_level": "High",
            "risk_category": "Very Low Risk",
            "explanations": {"feature_importance": "Home advantage, recent form"},
            "advanced_features": {
                "meta_stacking": True,
                "ensemble_voting": True,
                "feature_engineering": "advanced",
                "models_used": 9
            }
        },
        {
            "home_team": "Manchester City",
            "away_team": "Liverpool",
            "league": "Premier League",
            "prediction": "Over 2.5 Goals",
            "confidence": 0.68,
            "odds": 1.8,
            "category": "2_odds",
            "nigeria_datetime": "2025-07-31 18:00:00 WAT",
            "nigeria_date": "2025-07-31",
            "nigeria_time": "18:00",
            "day_of_week": "Thursday",
            "prediction_generated_at": nigeria_time.strftime('%Y-%m-%d %H:%M:%S WAT'),
            "prediction_type": "Over 2.5 Goals",
            "confidence_level": "Medium",
            "risk_category": "Very Low Risk",
            "explanations": {"feature_importance": "High-scoring teams, attacking style"},
            "advanced_features": {
                "meta_stacking": True,
                "ensemble_voting": True,
                "feature_engineering": "advanced",
                "models_used": 9
            }
        },
        {
            "home_team": "Barcelona",
            "away_team": "Real Madrid",
            "league": "La Liga",
            "prediction": "BTTS Yes",
            "confidence": 0.82,
            "odds": 4.5,
            "category": "5_odds",
            "nigeria_datetime": "2025-08-01 20:00:00 WAT",
            "nigeria_date": "2025-08-01",
            "nigeria_time": "20:00",
            "day_of_week": "Friday",
            "prediction_generated_at": nigeria_time.strftime('%Y-%m-%d %H:%M:%S WAT'),
            "prediction_type": "BTTS Yes",
            "confidence_level": "Very High",
            "risk_category": "Low Risk",
            "explanations": {"feature_importance": "El Clasico, both teams score regularly"},
            "advanced_features": {
                "meta_stacking": True,
                "ensemble_voting": True,
                "feature_engineering": "advanced",
                "models_used": 9
            }
        },
        {
            "home_team": "Bayern Munich",
            "away_team": "Borussia Dortmund",
            "league": "Bundesliga",
            "prediction": "Away Win",
            "confidence": 0.55,
            "odds": 8.2,
            "category": "10_odds",
            "nigeria_datetime": "2025-08-02 16:30:00 WAT",
            "nigeria_date": "2025-08-02",
            "nigeria_time": "16:30",
            "day_of_week": "Saturday",
            "prediction_generated_at": nigeria_time.strftime('%Y-%m-%d %H:%M:%S WAT'),
            "prediction_type": "Away Win",
            "confidence_level": "Low",
            "risk_category": "Medium Risk",
            "explanations": {"feature_importance": "Dortmund's away form, Bayern's injuries"},
            "advanced_features": {
                "meta_stacking": True,
                "ensemble_voting": True,
                "feature_engineering": "advanced",
                "models_used": 9
            }
        },
        {
            "home_team": "Juventus",
            "away_team": "AC Milan",
            "league": "Serie A",
            "prediction": "Draw",
            "confidence": 0.72,
            "odds": 2.8,
            "category": "rollover",
            "nigeria_datetime": "2025-08-03 14:00:00 WAT",
            "nigeria_date": "2025-08-03",
            "nigeria_time": "14:00",
            "day_of_week": "Sunday",
            "prediction_generated_at": nigeria_time.strftime('%Y-%m-%d %H:%M:%S WAT'),
            "prediction_type": "Draw",
            "confidence_level": "High",
            "risk_category": "Very Low Risk (Accumulator)",
            "explanations": {"feature_importance": "Evenly matched teams, defensive styles"},
            "advanced_features": {
                "meta_stacking": True,
                "ensemble_voting": True,
                "feature_engineering": "advanced",
                "models_used": 9
            }
        }
    ]
    
    # Organize predictions by date and category
    daily_predictions = {}
    categories_by_date = {}
    
    for pred in mock_predictions:
        date = pred["nigeria_date"]
        category = pred["category"]
        
        if date not in daily_predictions:
            daily_predictions[date] = []
            categories_by_date[date] = {"2_odds": [], "5_odds": [], "10_odds": [], "rollover": []}
        
        daily_predictions[date].append(pred)
        categories_by_date[date][category].append(pred)
    
    # Create the full results structure
    results = {
        "generation_info": {
            "generated_at": nigeria_time.strftime('%Y-%m-%d %H:%M:%S WAT'),
            "date_range": {
                "start_date": "2025-07-31",
                "end_date": "2025-08-03",
                "total_days": 4
            },
            "timezone": "Nigeria (WAT - UTC+1)"
        },
        "daily_predictions": {},
        "summary": {
            "total_days": 4,
            "successful_days": 4,
            "total_predictions": len(mock_predictions),
            "total_by_category": {"2_odds": 0, "5_odds": 0, "10_odds": 0, "rollover": 0}
        }
    }
    
    # Build daily predictions structure
    dates = ["2025-07-31", "2025-08-01", "2025-08-02", "2025-08-03"]
    day_names = ["Thursday", "Friday", "Saturday", "Sunday"]
    
    for i, date in enumerate(dates):
        day_preds = daily_predictions.get(date, [])
        day_categories = categories_by_date.get(date, {"2_odds": [], "5_odds": [], "10_odds": [], "rollover": []})
        
        results["daily_predictions"][date] = {
            "date": date,
            "day_name": day_names[i],
            "status": "success",
            "predictions": day_preds,
            "categories": day_categories,
            "metadata": {
                "service": "advanced_prediction_service",
                "models_used": ["xgboost_match_result", "xgboost_over_2_5", "xgboost_btts"],
                "total_fixtures": len(day_preds),
                "total_predictions": len(day_preds),
                "processing_time_seconds": 2.5,
                "advanced_features": {
                    "xgboost_models": 9,
                    "ensemble_models": 3,
                    "explainers_available": 2,
                    "feature_engineering": "advanced"
                }
            },
            "total_predictions": len(day_preds)
        }
        
        # Update category counts
        for category, preds in day_categories.items():
            results["summary"]["total_by_category"][category] += len(preds)
    
    return results

def main():
    """Test the multi-day prediction system with mock data."""
    print("🧪 TESTING MULTI-DAY PREDICTIONS WITH MOCK DATA")
    print("=" * 60)
    print("")
    
    # Create mock results
    print("📊 Creating mock prediction results...")
    results = create_mock_prediction_results()
    
    # Save mock results to JSON
    with open("mock_predictions_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("💾 Mock results saved to mock_predictions_results.json")
    
    # Format and save to text file
    print("📄 Formatting and saving mock predictions...")
    filename = format_and_save_from_results(results)
    
    if filename:
        # Rename to indicate it's a demo
        demo_filename = filename.replace("predictions_", "DEMO_predictions_")
        import os
        os.rename(filename, demo_filename)
        
        print(f"✅ Demo predictions saved to: {demo_filename}")
        print("")
        
        # Display summary
        summary = results.get('summary', {})
        print("📋 DEMO SUMMARY:")
        print("-" * 30)
        print(f"🎯 Total Predictions: {summary.get('total_predictions', 0)}")
        print(f"📅 Date Range: 2025-07-31 to 2025-08-03")
        print("")
        
        print("🎲 Predictions by Category:")
        total_by_category = summary.get('total_by_category', {})
        category_names = {
            '2_odds': '2.0 Odds (Very Low Risk)',
            '5_odds': '5.0 Odds (Low Risk)',
            '10_odds': '10.0 Odds (Medium Risk)',
            'rollover': 'Rollover/Accumulator (Very Low Risk)'
        }
        
        for category, count in total_by_category.items():
            category_name = category_names.get(category, category.upper())
            print(f"   • {category_name}: {count} predictions")
        
        print("")
        print("📖 This demonstrates the full functionality of the system:")
        print("   ✅ Multi-day prediction generation")
        print("   ✅ Nigeria timezone handling")
        print("   ✅ Comprehensive metadata collection")
        print("   ✅ Categorization by risk levels")
        print("   ✅ Structured text output formatting")
        print("   ✅ Clear filename with date range")
        print("")
        print(f"📁 Review the demo output in: {demo_filename}")
        
    else:
        print("❌ Failed to format and save demo predictions")

if __name__ == "__main__":
    main()
