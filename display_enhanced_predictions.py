#!/usr/bin/env python3
"""
Enhanced Prediction Display System
Shows comprehensive prediction information with all fixture details.
"""

import sqlite3
import json
from datetime import datetime, date
from typing import Dict, List, Any
import argparse

def format_time(datetime_str: str) -> str:
    """Format datetime string to readable time."""
    try:
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return dt.strftime('%H:%M')
    except:
        return 'TBD'

def format_date(datetime_str: str) -> str:
    """Format datetime string to readable date."""
    try:
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d')
    except:
        return str(date.today())

def get_confidence_emoji(confidence: float) -> str:
    """Get emoji based on confidence level."""
    if confidence >= 0.95:
        return '🔥🔥'  # Ultra high
    elif confidence >= 0.90:
        return '🔥'    # Very high
    elif confidence >= 0.85:
        return '✅'    # High
    elif confidence >= 0.75:
        return '⚠️'    # Medium
    else:
        return '❓'    # Low

def format_readable_prediction(pred_type: str, prediction: str, home_team: str, away_team: str) -> str:
    """Format prediction into readable text."""
    if pred_type == 'match_result':
        if prediction == '0':
            return f'{home_team} to Win'
        elif prediction == '1':
            return f'{away_team} to Win'
        else:
            return 'Draw'
    elif pred_type == 'over_under' or pred_type == 'over_2_5':
        return 'Over 2.5 Goals' if prediction == '1' else 'Under 2.5 Goals'
    elif pred_type == 'btts':
        return 'Both Teams to Score' if prediction == '1' else 'Both Teams NOT to Score'
    elif pred_type == 'clean_sheet_home':
        return f'{home_team} Clean Sheet' if prediction == '1' else f'{home_team} NOT Clean Sheet'
    elif pred_type == 'clean_sheet_away':
        return f'{away_team} Clean Sheet' if prediction == '1' else f'{away_team} NOT Clean Sheet'
    elif pred_type == 'win_to_nil_home':
        return f'{home_team} to Win to Nil' if prediction == '1' else f'{home_team} NOT to Win to Nil'
    elif pred_type == 'win_to_nil_away':
        return f'{away_team} to Win to Nil' if prediction == '1' else f'{away_team} NOT to Win to Nil'
    else:
        return f'{pred_type}: {prediction}'

def get_enhanced_predictions(target_date: str = None) -> List[Dict[str, Any]]:
    """Get enhanced predictions with comprehensive fixture information."""
    if not target_date:
        target_date = str(date.today())
    
    conn = sqlite3.connect('./football.db')
    cursor = conn.cursor()
    
    # Join daily_predictions with cached_fixtures for complete information
    # CRITICAL: ONLY show predictions for upcoming games (not finished)
    query = '''
        SELECT
            dp.home_team, dp.away_team, dp.league_name, dp.fixture_date, dp.ml_predictions,
            cf.fixture_id, cf.country, cf.status, cf.home_odds, cf.draw_odds, cf.away_odds,
            cf.home_score, cf.away_score, cf.match_result
        FROM daily_predictions dp
        LEFT JOIN cached_fixtures cf ON (
            dp.home_team = cf.home_team AND
            dp.away_team = cf.away_team AND
            DATE(dp.fixture_date) = DATE(cf.fixture_date)
        )
        WHERE dp.prediction_date = ?
        AND (cf.status IS NULL OR cf.status NOT IN ('Finished', 'FT', 'finished', 'completed', 'Full Time', 'After Pen.'))
        AND dp.fixture_date > datetime('now')
        ORDER BY dp.fixture_date
    '''
    
    cursor.execute(query, (target_date,))
    results = cursor.fetchall()
    
    enhanced_predictions = []
    
    for row in results:
        (home_team, away_team, league, fixture_date, ml_predictions_json,
         fixture_id, country, status, home_odds, draw_odds, away_odds,
         home_score, away_score, match_result) = row
        
        try:
            ml_predictions = json.loads(ml_predictions_json) if ml_predictions_json else {}
            
            # Create enhanced fixture info
            fixture_info = {
                'fixture_id': fixture_id or 'N/A',
                'home_team': home_team,
                'away_team': away_team,
                'league': league,
                'country': country or 'Unknown',
                'date': format_date(fixture_date),
                'time': format_time(fixture_date),
                'status': status or 'upcoming',
                'odds': {
                    'home': home_odds or 2.0,
                    'draw': draw_odds or 3.0,
                    'away': away_odds or 2.0
                },
                'score': {
                    'home': home_score,
                    'away': away_score
                } if home_score is not None else None,
                'result': match_result
            }
            
            # Process predictions
            predictions_by_category = {}
            for pred_type, pred_data in ml_predictions.items():
                confidence = pred_data.get('confidence', 0.0)
                prediction = pred_data.get('prediction', 'N/A')
                model_type = pred_data.get('model_type', 'unknown')
                
                readable_prediction = format_readable_prediction(pred_type, str(prediction), home_team, away_team)
                
                predictions_by_category[pred_type] = {
                    'prediction': prediction,
                    'readable_prediction': readable_prediction,
                    'confidence': confidence,
                    'confidence_emoji': get_confidence_emoji(confidence),
                    'model_type': model_type
                }
            
            enhanced_predictions.append({
                'fixture_info': fixture_info,
                'predictions': predictions_by_category
            })
            
        except Exception as e:
            print(f"Error processing {home_team} vs {away_team}: {str(e)}")
            continue
    
    conn.close()
    return enhanced_predictions

def display_predictions_by_category(predictions: List[Dict[str, Any]], category: str = None):
    """Display predictions organized by category."""
    
    if not predictions:
        print("❌ No predictions found.")
        return
    
    print(f'🎯 ENHANCED PREDICTIONS WITH COMPREHENSIVE INFORMATION')
    print('=' * 80)
    print(f'📅 Date: {predictions[0]["fixture_info"]["date"]}')
    print(f'📊 Total Fixtures: {len(predictions)}')
    print('=' * 80)
    
    if category:
        # Display specific category
        print(f'\n🎯 {category.upper().replace("_", " ")} PREDICTIONS')
        print('-' * 60)
        
        category_predictions = []
        for pred in predictions:
            if category in pred['predictions']:
                category_predictions.append((pred, pred['predictions'][category]))
        
        # Sort by confidence
        category_predictions.sort(key=lambda x: x[1]['confidence'], reverse=True)
        
        for i, (pred, pred_data) in enumerate(category_predictions, 1):
            fixture = pred['fixture_info']
            display_single_prediction(i, fixture, pred_data, category)
    
    else:
        # Display all predictions with all categories
        for i, pred in enumerate(predictions, 1):
            fixture = pred['fixture_info']
            print(f'\n{i:2d}. 🏟️  {fixture["home_team"]} vs {fixture["away_team"]}')
            print(f'    🏆 {fixture["league"]} ({fixture["country"]})')
            print(f'    📅 {fixture["date"]} at {fixture["time"]}')
            print(f'    🎲 Odds: Home {fixture["odds"]["home"]:.2f} | Draw {fixture["odds"]["draw"]:.2f} | Away {fixture["odds"]["away"]:.2f}')
            print(f'    🆔 Fixture ID: {fixture["fixture_id"]}')
            print(f'    📊 Status: {fixture["status"].title()}')
            
            if fixture['score']:
                print(f'    ⚽ Score: {fixture["home_team"]} {fixture["score"]["home"]} - {fixture["score"]["away"]} {fixture["away_team"]}')
            
            print(f'    🤖 Predictions:')
            
            # Sort predictions by confidence
            sorted_preds = sorted(pred['predictions'].items(), key=lambda x: x[1]['confidence'], reverse=True)
            
            for pred_type, pred_data in sorted_preds:
                emoji = pred_data['confidence_emoji']
                readable = pred_data['readable_prediction']
                confidence = pred_data['confidence']
                model = pred_data['model_type']
                
                print(f'       {emoji} {readable} ({confidence:.1%} - {model})')
            
            print()

def display_single_prediction(index: int, fixture: Dict, pred_data: Dict, category: str):
    """Display a single prediction with full details."""
    print(f'\n{index:2d}. {pred_data["confidence_emoji"]} {fixture["home_team"]} vs {fixture["away_team"]}')
    print(f'    🏆 {fixture["league"]} ({fixture["country"]})')
    print(f'    📅 {fixture["date"]} at {fixture["time"]}')
    print(f'    🎲 Odds: Home {fixture["odds"]["home"]:.2f} | Draw {fixture["odds"]["draw"]:.2f} | Away {fixture["odds"]["away"]:.2f}')
    print(f'    📊 {pred_data["readable_prediction"]} ({pred_data["confidence"]:.1%} confidence)')
    print(f'    🤖 Model: {pred_data["model_type"].title()}')
    print(f'    🆔 Fixture ID: {fixture["fixture_id"]}')
    
    if fixture['score']:
        print(f'    ⚽ Final Score: {fixture["home_team"]} {fixture["score"]["home"]} - {fixture["score"]["away"]} {fixture["away_team"]}')

def display_high_confidence_summary(predictions: List[Dict[str, Any]]):
    """Display summary of high confidence predictions."""
    high_confidence = []
    
    for pred in predictions:
        fixture = pred['fixture_info']
        for pred_type, pred_data in pred['predictions'].items():
            if pred_data['confidence'] >= 0.85:
                high_confidence.append({
                    'fixture': f"{fixture['home_team']} vs {fixture['away_team']}",
                    'league': fixture['league'],
                    'time': fixture['time'],
                    'prediction': pred_data['readable_prediction'],
                    'confidence': pred_data['confidence'],
                    'emoji': pred_data['confidence_emoji']
                })
    
    if high_confidence:
        print(f'\n🔥 HIGH CONFIDENCE PREDICTIONS (≥85%)')
        print('=' * 60)
        
        # Sort by confidence
        high_confidence.sort(key=lambda x: x['confidence'], reverse=True)
        
        for i, pred in enumerate(high_confidence, 1):
            print(f'{i:2d}. {pred["emoji"]} {pred["fixture"]} ({pred["time"]})')
            print(f'    📊 {pred["prediction"]} ({pred["confidence"]:.1%})')
            print(f'    🏆 {pred["league"]}')
            print()

def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description='Display Enhanced Predictions')
    parser.add_argument('--date', type=str, help='Date in YYYY-MM-DD format')
    parser.add_argument('--category', type=str, choices=['match_result', 'over_under', 'over_2_5', 'btts', 'clean_sheet_home', 'clean_sheet_away', 'win_to_nil_home', 'win_to_nil_away'], help='Specific prediction category')
    parser.add_argument('--high-confidence', action='store_true', help='Show only high confidence predictions')
    
    args = parser.parse_args()
    
    target_date = args.date or str(date.today())
    predictions = get_enhanced_predictions(target_date)
    
    if args.high_confidence:
        display_high_confidence_summary(predictions)
    else:
        display_predictions_by_category(predictions, args.category)

if __name__ == "__main__":
    main()
