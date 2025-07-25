#!/usr/bin/env python3
"""
Show Low Risk Accumulators - SAFE BETS ONLY
Display conservative accumulator bets with up to 10 games each.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.accumulator_builder import AccumulatorBuilder
from services.prediction_retrieval_service import PredictionRetrievalService
from datetime import date

def show_low_risk_accumulators():
    """Display low-risk accumulator bets for upcoming games only."""
    
    print("🛡️ LOW RISK ACCUMULATOR BETS - SAFE BETS ONLY")
    print("=" * 80)
    print("🎯 Configuration: 80%+ confidence, up to 10 games per accumulator")
    print("📊 Odds Range: 1.15 - 1.80 per game (ultra conservative)")
    print()
    
    # Get today's predictions
    service = PredictionRetrievalService()
    predictions_data = service.get_comprehensive_daily_predictions()
    
    if predictions_data['status'] != 'success' or not predictions_data['predictions']:
        print("❌ No predictions available for today")
        return
    
    print(f"📅 Date: {predictions_data['date']}")
    print(f"📊 Total Upcoming Games: {len(predictions_data['predictions'])}")
    print()
    
    # Initialize low-risk accumulator builder
    builder = AccumulatorBuilder()
    predictions = predictions_data['predictions']
    
    # Build all accumulators at once using the correct method
    try:
        accumulators_result = builder.build_accumulators(predictions)

        if accumulators_result['status'] == 'success':
            accumulators = accumulators_result['accumulators']

            print(f"📊 High-confidence selections found: {accumulators_result['high_confidence_selections']}")
            print()

            # Display each accumulator category
            categories = ['2_odds', '5_odds', '10_odds', 'rollover']

            for category in categories:
                print(f"🎲 {category.upper().replace('_', ' ')} ACCUMULATOR (LOW RISK)")
                print("-" * 60)

                if category in accumulators:
                    acc = accumulators[category]

                    if acc.get('selected', False):
                        print(f"✅ SAFE ACCUMULATOR FOUND:")
                        print(f"   📈 Total Odds: {acc['total_odds']:.2f}")
                        print(f"   🎮 Games: {len(acc['games'])}")
                        print(f"   🎯 Avg Confidence: {acc['average_confidence']:.1f}%")
                        print(f"   🌟 Diversity Score: {acc['diversity_score']:.2f}")
                        print(f"   🛡️ Risk Level: {acc['risk_level']}")
                        print(f"   💰 Recommended Stake: ${acc['recommended_stake']:.2f}")
                        print()
                        print(f"   🎯 SAFE GAMES IN THIS ACCUMULATOR:")

                        for i, game in enumerate(acc['games'], 1):
                            home_team = game.get('home_team', 'Unknown')
                            away_team = game.get('away_team', 'Unknown')
                            prediction = game.get('readable_prediction', 'Unknown')
                            odds = game.get('estimated_odds', 1.0)
                            confidence = game.get('confidence', 0)
                            fixture_date = game.get('date', 'Unknown')

                            print(f"      {i}. {home_team} vs {away_team}")
                            print(f"         🎯 Prediction: {prediction}")
                            print(f"         📊 Confidence: {confidence:.1f}% | Odds: {odds:.2f}")
                            print(f"         🕐 Time: {fixture_date}")
                            print()

                    else:
                        print(f"❌ NO SAFE ACCUMULATOR FOUND")
                        print(f"   📝 Reason: {acc.get('reason', 'Unknown')}")
                        print(f"   🛡️ Required: 80%+ confidence, 1.15-1.80 odds range")
                        print()
                else:
                    print(f"❌ CATEGORY NOT FOUND")
                    print()

                print()
        else:
            print(f"❌ ERROR BUILDING ACCUMULATORS: {accumulators_result.get('message', 'Unknown error')}")

    except Exception as e:
        print(f"❌ SYSTEM ERROR: {str(e)}")
        print()
    
    print("🛡️ SAFETY NOTES:")
    print("• Only games with 80%+ confidence included")
    print("• Individual game odds limited to 1.15-1.80 (very safe range)")
    print("• Up to 10 games per accumulator for better odds")
    print("• Sorted by safety score (confidence × safety factor)")
    print("• All finished games automatically excluded")

if __name__ == "__main__":
    show_low_risk_accumulators()
