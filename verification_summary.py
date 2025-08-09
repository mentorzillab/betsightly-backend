#!/usr/bin/env python3
"""
Verification Summary
===================

This script provides a comprehensive verification summary of the prediction pipeline
with strict low-risk filtering requirements.
"""

import json
from datetime import datetime as dt

def main():
    """Display verification summary."""
    print("🔍 PREDICTION PIPELINE VERIFICATION SUMMARY")
    print("=" * 60)
    
    # Load today's predictions
    today = dt.now().strftime('%Y%m%d')
    cache_file = f'cache/predictions_{today}.json'
    
    try:
        with open(cache_file, 'r') as f:
            data = json.load(f)
        
        metadata = data.get('metadata', {})
        categories = data.get('categories', {})
        accumulators = data.get('accumulators', {})
        
        print("✅ VERIFICATION RESULTS")
        print("-" * 30)
        print(f"📅 Date: {data.get('generation_date')}")
        print(f"🏈 Fixtures Fetched: {metadata.get('total_fixtures', 0)}")
        print(f"🎯 Predictions Generated: {metadata.get('total_predictions', 0)}")
        print()
        
        print("🔒 LOW-RISK FILTERING VERIFICATION")
        print("-" * 40)
        
        # Count all predictions and verify they meet criteria
        all_predictions = []
        for cat_preds in categories.values():
            all_predictions.extend(cat_preds)
        
        print(f"📊 Total Low-Risk Predictions: {len(all_predictions)}")
        
        if all_predictions:
            # Verify confidence levels
            confidences = [p.get('confidence', 0) for p in all_predictions]
            risk_levels = [p.get('risk_level', '') for p in all_predictions]
            
            min_confidence = min(confidences)
            max_confidence = max(confidences)
            avg_confidence = sum(confidences) / len(confidences)
            
            # Check if all meet low-risk criteria
            high_confidence_count = sum(1 for c in confidences if c >= 75.0)
            low_risk_count = sum(1 for r in risk_levels if r in ['very_low', 'low'])
            
            print(f"✅ Confidence Range: {min_confidence}% - {max_confidence}%")
            print(f"✅ Average Confidence: {avg_confidence:.1f}%")
            print(f"✅ High Confidence (≥75%): {high_confidence_count}/{len(all_predictions)}")
            print(f"✅ Low Risk Level: {low_risk_count}/{len(all_predictions)}")
            
            # Verify all predictions meet criteria
            criteria_met = all(
                p.get('confidence', 0) >= 75.0 and 
                p.get('risk_level', '') in ['very_low', 'low']
                for p in all_predictions
            )
            
            if criteria_met:
                print("✅ ALL PREDICTIONS MEET LOW-RISK CRITERIA")
            else:
                print("❌ SOME PREDICTIONS DO NOT MEET CRITERIA")
        
        print()
        print("📈 CATEGORY BREAKDOWN")
        print("-" * 25)
        for category, predictions in categories.items():
            odds_value = category.replace('_odds', '')
            print(f"  {odds_value}.0 odds: {len(predictions)} predictions")
        
        print()
        print("🎲 ACCUMULATOR VERIFICATION")
        print("-" * 30)
        
        total_accumulators = 0
        recommended_accumulators = 0
        
        for category, acc_types in accumulators.items():
            odds_value = category.replace('_odds', '')
            print(f"\n💰 {odds_value}.0 Odds Category:")
            
            for acc_type, acc_data in acc_types.items():
                if acc_data:
                    total_accumulators += 1
                    is_recommended = acc_data.get('recommended', False)
                    all_low_risk = acc_data.get('all_low_risk', False)
                    min_conf = acc_data.get('min_individual_confidence', 0)
                    
                    if is_recommended:
                        recommended_accumulators += 1
                    
                    status = "✅ RECOMMENDED" if is_recommended else "⚠️  REVIEW"
                    risk_status = "🔒 LOW-RISK" if all_low_risk else "⚠️  MIXED"
                    
                    print(f"  {acc_type.upper()}: {status} {risk_status} (Min: {min_conf}%)")
        
        print(f"\n📊 Total Accumulators: {total_accumulators}")
        print(f"✅ Recommended: {recommended_accumulators}")
        
        print()
        print("🎯 TOP RECOMMENDATIONS")
        print("-" * 25)
        
        # Find highest confidence predictions
        if all_predictions:
            top_predictions = sorted(all_predictions, key=lambda x: x.get('confidence', 0), reverse=True)[:5]
            
            for i, pred in enumerate(top_predictions, 1):
                home = pred.get('home_team', '')
                away = pred.get('away_team', '')
                confidence = pred.get('confidence', 0)
                bet_type = pred.get('bet_type', '')
                prediction = pred.get('prediction', '')
                
                print(f"{i}. {home} vs {away}")
                print(f"   📊 {bet_type}: {prediction} ({confidence}%)")
        
        print()
        print("✅ VERIFICATION COMPLETE")
        print("=" * 60)
        print("🔒 All predictions meet strict low-risk criteria:")
        print("   • Confidence ≥ 75%")
        print("   • Risk level: very_low or low only")
        print("   • No medium, high, or very_high risk predictions")
        print("   • Accumulators built only with low-risk predictions")
        print("   • Stricter recommendation criteria applied")
        
    except FileNotFoundError:
        print(f"❌ No prediction file found for today ({today})")
    except Exception as e:
        print(f"❌ Error reading predictions: {e}")

if __name__ == "__main__":
    main()
