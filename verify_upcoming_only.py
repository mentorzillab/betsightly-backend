#!/usr/bin/env python3
"""
Verification Script: Ensure Only Upcoming Games Show Predictions
This script verifies that the system only shows predictions for upcoming games.
"""

import sqlite3
from datetime import datetime, date

def verify_upcoming_only():
    """Verify that only upcoming games have predictions shown."""
    
    print('🔍 VERIFYING: ONLY UPCOMING GAMES HAVE PREDICTIONS')
    print('=' * 60)
    print(f'📅 Current Date: {date.today()}')
    print(f'🕐 Current Time: {datetime.now().strftime("%H:%M:%S")}')
    print('=' * 60)
    
    conn = sqlite3.connect('./football.db')
    cursor = conn.cursor()
    
    # Check all fixtures for today
    print('\n📋 ALL FIXTURES FOR TODAY:')
    cursor.execute('''
        SELECT fixture_id, home_team, away_team, fixture_date, status
        FROM cached_fixtures 
        WHERE DATE(fixture_date) = ?
        ORDER BY fixture_date
    ''', (str(date.today()),))
    
    all_fixtures = cursor.fetchall()
    finished_count = 0
    upcoming_count = 0
    
    for fixture_id, home, away, fixture_date, status in all_fixtures:
        try:
            dt = datetime.fromisoformat(fixture_date.replace('Z', '+00:00'))
            time_str = dt.strftime('%H:%M')
        except:
            time_str = 'Unknown'
        
        status_emoji = '✅' if status in ['Finished', 'FT', 'finished', 'completed', 'Full Time', 'After Pen.', 'AET', 'Postponed', 'Cancelled', 'Abandoned'] else '⏳'
        print(f'{status_emoji} {home} vs {away} ({time_str}) - Status: {status or "Unknown"}')
        
        if status in ['Finished', 'FT', 'finished', 'completed', 'Full Time', 'After Pen.', 'AET', 'Postponed', 'Cancelled', 'Abandoned']:
            finished_count += 1
        else:
            upcoming_count += 1
    
    print(f'\n📊 FIXTURE SUMMARY:')
    print(f'   ✅ Finished Games: {finished_count}')
    print(f'   ⏳ Upcoming Games: {upcoming_count}')
    print(f'   📋 Total Games: {len(all_fixtures)}')
    
    # Check predictions using the updated query
    print('\n🎯 PREDICTIONS AFTER FILTERING:')
    cursor.execute('''
        SELECT 
            dp.home_team, dp.away_team, dp.fixture_date,
            cf.status
        FROM daily_predictions dp
        LEFT JOIN cached_fixtures cf ON (
            dp.home_team = cf.home_team AND 
            dp.away_team = cf.away_team AND
            DATE(dp.fixture_date) = DATE(cf.fixture_date)
        )
        WHERE dp.prediction_date = ?
        AND (cf.status IS NULL OR cf.status NOT IN ('Finished', 'FT', 'finished', 'completed', 'Full Time', 'After Pen.', 'AET', 'Postponed', 'Cancelled', 'Abandoned'))
        AND dp.fixture_date > datetime('now')
        ORDER BY dp.fixture_date
    ''', (str(date.today()),))
    
    filtered_predictions = cursor.fetchall()
    
    if filtered_predictions:
        print(f'✅ Found {len(filtered_predictions)} predictions for upcoming games:')
        for home, away, fixture_date, status in filtered_predictions:
            try:
                dt = datetime.fromisoformat(fixture_date.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M')
            except:
                time_str = 'Unknown'
            print(f'   ⏳ {home} vs {away} ({time_str}) - Status: {status or "Upcoming"}')
    else:
        print('❌ No predictions found for upcoming games')
    
    # Verify no finished games have predictions
    print('\n🚫 VERIFYING NO FINISHED GAMES HAVE PREDICTIONS:')
    cursor.execute('''
        SELECT 
            dp.home_team, dp.away_team, dp.fixture_date,
            cf.status
        FROM daily_predictions dp
        LEFT JOIN cached_fixtures cf ON (
            dp.home_team = cf.home_team AND 
            dp.away_team = cf.away_team AND
            DATE(dp.fixture_date) = DATE(cf.fixture_date)
        )
        WHERE dp.prediction_date = ?
        AND cf.status IN ('Finished', 'FT', 'finished', 'completed', 'Full Time', 'After Pen.', 'AET', 'Postponed', 'Cancelled', 'Abandoned')
    ''', (str(date.today()),))
    
    finished_with_predictions = cursor.fetchall()
    
    if finished_with_predictions:
        print(f'❌ ERROR: Found {len(finished_with_predictions)} finished games with predictions:')
        for home, away, fixture_date, status in finished_with_predictions:
            print(f'   ❌ {home} vs {away} - Status: {status}')
        print('🔧 These should be filtered out!')
    else:
        print('✅ GOOD: No finished games have predictions showing')
    
    # Summary
    print(f'\n📊 VERIFICATION SUMMARY:')
    print(f'   📋 Total Fixtures Today: {len(all_fixtures)}')
    print(f'   ✅ Finished Games: {finished_count}')
    print(f'   ⏳ Upcoming Games: {upcoming_count}')
    print(f'   🎯 Predictions Shown: {len(filtered_predictions)}')
    print(f'   🚫 Finished Games with Predictions: {len(finished_with_predictions)}')
    
    if len(finished_with_predictions) == 0 and len(filtered_predictions) > 0:
        print('\n🎉 SUCCESS: System correctly shows only upcoming games!')
        print('✅ No predictions shown for finished games')
        print('✅ Predictions available for upcoming games')
    elif len(finished_with_predictions) > 0:
        print('\n❌ ISSUE: System showing predictions for finished games')
        print('🔧 Filter needs to be applied more strictly')
    else:
        print('\n⚠️  WARNING: No predictions found for any games')
        print('🔧 Check if prediction generation is working')
    
    conn.close()
    
    print('\n' + '=' * 60)
    print('🔍 VERIFICATION COMPLETED')
    print('=' * 60)

if __name__ == "__main__":
    verify_upcoming_only()
