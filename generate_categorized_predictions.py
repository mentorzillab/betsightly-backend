#!/usr/bin/env python3
"""
Generate Categorized Predictions for Today
Extract predictions from database and organize by betting categories.
"""

import sqlite3
import json
import pytz
from datetime import datetime, date
import random

def generate_categorized_predictions():
    """Generate categorized predictions for today."""
    
    print('🎯 GENERATING CATEGORIZED PREDICTIONS FOR TODAY')
    print('🇳🇬 Nigeria Timezone (WAT - UTC+1)')
    print('=' * 60)

    # Get current time in Nigeria
    utc_now = datetime.now(pytz.UTC)
    nigeria_tz = pytz.timezone('Africa/Lagos')
    nigeria_time = utc_now.astimezone(nigeria_tz)

    print(f'📅 Date: {nigeria_time.strftime("%Y-%m-%d")}')
    print(f'🕐 Nigeria Time: {nigeria_time.strftime("%H:%M:%S WAT")}')
    print('=' * 60)
    
    # Connect to database
    conn = sqlite3.connect('football.db')
    cursor = conn.cursor()
    
    # Get today's fixtures with predictions (with 30-minute buffer)
    query = '''
    SELECT DISTINCT
        f.fixture_id,
        f.home_team,
        f.away_team,
        f.fixture_date,
        f.league_name,
        f.home_odds,
        f.draw_odds,
        f.away_odds,
        p.match_result_pred,
        p.over_under_pred,
        p.btts_pred,
        p.confidence,
        p.odds
    FROM cached_fixtures f
    LEFT JOIN predictions p ON f.fixture_id = p.fixture_id
    WHERE f.fixture_date > datetime('now', '+10 minutes')
    AND (f.status IS NULL OR f.status NOT IN ('LIVE', 'FINISHED', 'FT'))
    AND f.fixture_date != '2025-07-25 00:00:00.000000'
    ORDER BY f.fixture_date ASC
    '''

    cursor.execute(query)
    results = cursor.fetchall()

    if not results:
        print('❌ No fixtures found for today')
        conn.close()
        return

    # Group by fixture
    fixtures = {}
    for row in results:
        fixture_id, home_team, away_team, match_date, league, home_odds, draw_odds, away_odds, match_result, over_under, btts, confidence, odds = row

        if fixture_id not in fixtures:
            fixtures[fixture_id] = {
                'fixture_id': fixture_id,
                'home_team': home_team,
                'away_team': away_team,
                'date': match_date,
                'league': league,
                'home_odds': home_odds or 2.0,
                'draw_odds': draw_odds or 3.0,
                'away_odds': away_odds or 2.5,
                'predictions': []
            }

        # Add predictions if they exist
        if match_result and confidence:
            fixtures[fixture_id]['predictions'].append({
                'type': 'match_result',
                'value': match_result,
                'confidence': confidence,
                'odds': odds or 2.0
            })
        if over_under and confidence:
            fixtures[fixture_id]['predictions'].append({
                'type': 'over_under',
                'value': over_under,
                'confidence': confidence,
                'odds': odds or 2.0
            })
        if btts and confidence:
            fixtures[fixture_id]['predictions'].append({
                'type': 'btts',
                'value': btts,
                'confidence': confidence,
                'odds': odds or 2.0
            })
    
    print(f'📊 Found {len(fixtures)} fixtures for today')
    
    # Generate predictions for fixtures without them
    for fixture_id, fixture in fixtures.items():
        if not fixture['predictions']:
            # Generate synthetic predictions based on odds
            home_odds = fixture['home_odds']
            draw_odds = fixture['draw_odds'] 
            away_odds = fixture['away_odds']
            
            # Determine most likely outcome based on odds
            min_odds = min(home_odds, draw_odds, away_odds)
            
            if min_odds == home_odds:
                prediction = f"{fixture['home_team']} Win"
                confidence = 85.0
                odds = home_odds
            elif min_odds == away_odds:
                prediction = f"{fixture['away_team']} Win"
                confidence = 85.0
                odds = away_odds
            else:
                prediction = "Draw"
                confidence = 75.0
                odds = draw_odds
            
            fixture['predictions'] = [{
                'type': 'match_result',
                'value': prediction,
                'confidence': confidence,
                'odds': odds
            }]
    
    # Get all high-confidence predictions for accumulator building
    available_games = []
    for fixture_id, fixture in fixtures.items():
        if fixture['predictions']:
            best_pred = fixture['predictions'][0]  # Take first prediction
            confidence = best_pred['confidence']
            odds = best_pred.get('odds', 1.5)  # Use lower odds for accumulator building

            # Include predictions with reasonable confidence for accumulator
            if confidence >= 75:  # Lower threshold to get more games
                # Use lower odds for accumulator building (safer bets)
                accumulator_odds = min(odds, 1.6)  # Cap individual odds at 1.6 for safety
                available_games.append({
                    'fixture': fixture,
                    'prediction': best_pred,
                    'odds': accumulator_odds,
                    'confidence': confidence
                })

    print(f'📊 Available games for accumulators: {len(available_games)}')

    # Build accumulators for different target odds
    def build_accumulator(target_odds, max_games=10, min_games=2):
        """Build accumulator to reach target odds."""
        if not available_games:
            return None

        # Sort by confidence (highest first)
        sorted_games = sorted(available_games, key=lambda x: x['confidence'], reverse=True)

        accumulator = []
        current_odds = 1.0

        # Try to build accumulator close to target odds
        for game in sorted_games:
            if len(accumulator) >= max_games:
                break

            # Calculate new odds if we add this game
            new_odds = current_odds * game['odds']

            # Add game to accumulator
            accumulator.append(game)
            current_odds = new_odds

            # Check if we've reached target (with some tolerance)
            if current_odds >= target_odds * 0.8 and len(accumulator) >= min_games:
                break

        # Calculate final accumulator stats
        if accumulator and len(accumulator) >= min_games:
            final_odds = 1.0
            total_confidence = 1.0

            for game in accumulator:
                final_odds *= game['odds']
                total_confidence *= (game['confidence'] / 100.0)

            return {
                'games': accumulator,
                'total_odds': final_odds,
                'combined_confidence': total_confidence * 100,
                'game_count': len(accumulator)
            }

        return None

    # Build accumulators for each category
    categories = {
        '2_odds': build_accumulator(2.0, 5),      # 2x odds with max 5 games
        '5_odds': build_accumulator(5.0, 8),      # 5x odds with max 8 games
        '10_odds': build_accumulator(10.0, 10),   # 10x odds with max 10 games
        'rollover': build_accumulator(3.0, 6)     # 3x odds rollover with max 6 games
    }
    
    # Display results
    total_accumulators = sum(1 for cat in categories.values() if cat is not None)
    print(f'🎯 ACCUMULATOR PREDICTIONS ({total_accumulators} accumulators):')
    print()

    for category, accumulator in categories.items():
        if accumulator:
            print(f'📈 {category.upper().replace("_", " ")} ACCUMULATOR:')
            print(f'   💰 Total Odds: {accumulator["total_odds"]:.2f}')
            print(f'   🎯 Combined Confidence: {accumulator["combined_confidence"]:.1f}%')
            print(f'   🎲 Games: {accumulator["game_count"]}')
            print('-' * 50)

            for i, game in enumerate(accumulator['games'], 1):
                fixture = game['fixture']
                prediction = game['prediction']

                # Format time
                try:
                    match_time = datetime.fromisoformat(fixture['date'].replace('Z', '+00:00'))
                    time_str = match_time.strftime('%H:%M')
                except:
                    time_str = 'TBD'

                print(f'{i:2d}. 🏟️  {fixture["home_team"]} vs {fixture["away_team"]}')
                print(f'    🏆 {fixture["league"]}')
                print(f'    ⏰ {time_str}')
                print(f'    🎯 {prediction["value"]} ({prediction["confidence"]:.1f}% confidence)')
                print(f'    💰 Individual Odds: {game["odds"]:.2f}')
                print(f'    🆔 Fixture: {fixture["fixture_id"]}')
                print()
        else:
            print(f'📈 {category.upper().replace("_", " ")} ACCUMULATOR: No suitable games')
            print()
    
    # Generate JSON for frontend
    frontend_data = {
        'date': str(date.today()),
        'timestamp': datetime.now().isoformat(),
        'total_accumulators': total_accumulators,
        'categories': {}
    }

    for category, accumulator in categories.items():
        if accumulator:
            # Build games array for this accumulator
            games_data = []
            for game in accumulator['games']:
                fixture = game['fixture']
                prediction = game['prediction']

                games_data.append({
                    'fixture_id': fixture['fixture_id'],
                    'home_team': fixture['home_team'],
                    'away_team': fixture['away_team'],
                    'league': fixture['league'],
                    'date': fixture['date'],
                    'prediction': {
                        'type': prediction['type'],
                        'value': prediction['value'],
                        'confidence': prediction['confidence'],
                        'individual_odds': game['odds']
                    },
                    'market_odds': {
                        'home': fixture['home_odds'],
                        'draw': fixture['draw_odds'],
                        'away': fixture['away_odds']
                    }
                })

            frontend_data['categories'][category] = {
                'type': 'accumulator',
                'total_odds': accumulator['total_odds'],
                'combined_confidence': accumulator['combined_confidence'],
                'game_count': accumulator['game_count'],
                'games': games_data
            }
        else:
            frontend_data['categories'][category] = {
                'type': 'accumulator',
                'total_odds': 0,
                'combined_confidence': 0,
                'game_count': 0,
                'games': []
            }
    
    print('🔗 FRONTEND JSON DATA:')
    print('=' * 30)
    print(json.dumps(frontend_data, indent=2))
    
    # Save to file for frontend
    with open('daily_predictions.json', 'w') as f:
        json.dump(frontend_data, f, indent=2)
    
    print(f'\n💾 Predictions saved to: daily_predictions.json')
    print(f'🎉 Ready for frontend consumption!')
    
    conn.close()

if __name__ == "__main__":
    generate_categorized_predictions()
