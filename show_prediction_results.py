#!/usr/bin/env python3
"""
Display Prediction Results
=========================

This script displays the results from the complete prediction pipeline
in a readable format, showing categorized predictions and accumulators.
"""

import json
import os
from datetime import datetime as dt
from typing import Dict, List, Any

def load_latest_predictions() -> Dict[str, Any]:
    """Load the latest prediction results."""
    cache_dir = 'cache'
    if not os.path.exists(cache_dir):
        print("❌ No cache directory found")
        return {}
    
    # Find the latest prediction file
    today = dt.now().strftime('%Y%m%d')
    cache_file = f"{cache_dir}/predictions_{today}.json"
    
    if not os.path.exists(cache_file):
        print(f"❌ No predictions found for today ({today})")
        return {}
    
    with open(cache_file, 'r') as f:
        return json.load(f)

def display_summary(data: Dict[str, Any]):
    """Display pipeline execution summary."""
    metadata = data.get('metadata', {})
    
    print("🎯 PREDICTION PIPELINE SUMMARY")
    print("=" * 50)
    print(f"📅 Generation Date: {data.get('generation_date')}")
    print(f"⏰ Generation Time: {data.get('generation_time')}")
    print(f"🏈 Total Fixtures: {metadata.get('total_fixtures', 0)}")
    print(f"🎯 Total Predictions: {metadata.get('total_predictions', 0)}")
    print(f"📊 Categorized Predictions: {metadata.get('categorized_predictions', 0)}")
    print(f"🤖 Models Used: {', '.join(metadata.get('models_used', []))}")
    print(f"📈 Data Source: {metadata.get('data_source', 'Unknown')}")
    print(f"🔒 Risk Filter: {metadata.get('risk_filter', 'Unknown')}")
    print(f"📏 Confidence Threshold: {metadata.get('confidence_threshold', 0)}%")
    print()

def display_categories(data: Dict[str, Any]):
    """Display prediction categories."""
    categories = data.get('categories', {})
    
    print("📈 PREDICTION CATEGORIES")
    print("=" * 50)
    
    for category, predictions in categories.items():
        odds_value = category.replace('_odds', '')
        print(f"\n🎲 {odds_value}.0 ODDS CATEGORY ({len(predictions)} predictions)")
        print("-" * 40)
        
        if not predictions:
            print("   No predictions in this category")
            continue
        
        # Group by league for better display
        leagues = {}
        for pred in predictions:
            league = pred.get('league', 'Unknown')
            if league not in leagues:
                leagues[league] = []
            leagues[league].append(pred)
        
        for league, league_preds in leagues.items():
            print(f"\n   🏆 {league} ({len(league_preds)} predictions)")
            
            # Show top 5 predictions for this league
            for pred in league_preds[:5]:
                home = pred.get('home_team', '')
                away = pred.get('away_team', '')
                bet_type = pred.get('bet_type', '')
                prediction = pred.get('prediction', '')
                confidence = pred.get('confidence', 0)
                
                print(f"      ⚽ {home} vs {away}")
                print(f"         📊 {bet_type}: {prediction} (Confidence: {confidence}%)")
            
            if len(league_preds) > 5:
                print(f"         ... and {len(league_preds) - 5} more predictions")

def display_accumulators(data: Dict[str, Any]):
    """Display accumulator bets."""
    accumulators = data.get('accumulators', {})
    
    print("\n🎲 ACCUMULATOR BETS")
    print("=" * 50)
    
    for category, acc_types in accumulators.items():
        odds_value = category.replace('_odds', '')
        print(f"\n💰 {odds_value}.0 ODDS ACCUMULATORS")
        print("-" * 30)
        
        for acc_type, acc_data in acc_types.items():
            if acc_data is None:
                continue
                
            size = acc_data.get('size', 0)
            combined_odds = acc_data.get('combined_odds', 0)
            combined_confidence = acc_data.get('combined_confidence', 0)
            recommended = acc_data.get('recommended', False)
            predictions = acc_data.get('predictions', [])
            all_low_risk = acc_data.get('all_low_risk', False)
            min_confidence = acc_data.get('min_individual_confidence', 0)
            avg_confidence = acc_data.get('avg_individual_confidence', 0)

            status = "✅ RECOMMENDED" if recommended else "⚠️  REVIEW"
            risk_status = "🔒 LOW-RISK" if all_low_risk else "⚠️  MIXED RISK"

            print(f"\n   🎯 {acc_type.upper()} ({size} selections) {status} {risk_status}")
            print(f"      💰 Combined Odds: {combined_odds}")
            print(f"      📊 Combined Confidence: {combined_confidence}%")
            print(f"      📏 Min Individual: {min_confidence}% | Avg: {avg_confidence:.1f}%")
            print(f"      🎮 Selections:")
            
            for i, pred in enumerate(predictions, 1):
                home = pred.get('home_team', '')
                away = pred.get('away_team', '')
                bet_type = pred.get('bet_type', '')
                prediction = pred.get('prediction', '')
                confidence = pred.get('confidence', 0)
                
                print(f"         {i}. {home} vs {away}")
                print(f"            📊 {bet_type}: {prediction} ({confidence}%)")

def display_top_picks(data: Dict[str, Any]):
    """Display top recommended picks."""
    categories = data.get('categories', {})
    
    print("\n⭐ TOP RECOMMENDED PICKS")
    print("=" * 50)
    
    all_predictions = []
    for category, predictions in categories.items():
        all_predictions.extend(predictions)
    
    # Sort by confidence
    top_predictions = sorted(all_predictions, key=lambda x: x.get('confidence', 0), reverse=True)
    
    print("\n🏆 HIGHEST CONFIDENCE PREDICTIONS (Top 10)")
    print("-" * 45)
    
    for i, pred in enumerate(top_predictions[:10], 1):
        home = pred.get('home_team', '')
        away = pred.get('away_team', '')
        league = pred.get('league', '')
        bet_type = pred.get('bet_type', '')
        prediction = pred.get('prediction', '')
        confidence = pred.get('confidence', 0)
        odds = pred.get('estimated_odds', 0)
        
        print(f"\n{i:2d}. ⚽ {home} vs {away}")
        print(f"     🏆 {league}")
        print(f"     📊 {bet_type}: {prediction}")
        print(f"     💪 Confidence: {confidence}% | 💰 Odds: ~{odds}")

def main():
    """Main function to display prediction results."""
    print("🚀 BETSIGHTLY PREDICTION RESULTS")
    print("=" * 60)
    
    # Load latest predictions
    data = load_latest_predictions()
    
    if not data:
        print("❌ No prediction data available")
        return
    
    # Display all sections
    display_summary(data)
    display_categories(data)
    display_accumulators(data)
    display_top_picks(data)
    
    print("\n" + "=" * 60)
    print("✅ Results display complete!")
    print("💡 Tip: Use these predictions responsibly and always gamble within your means.")

if __name__ == "__main__":
    main()
