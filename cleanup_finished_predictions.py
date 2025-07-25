#!/usr/bin/env python3
"""
Cleanup Script: Remove Predictions for Finished Games
This script removes predictions for games that have already finished.
"""

import sqlite3
from datetime import datetime, date

def cleanup_finished_predictions():
    """Remove predictions for finished games from the database."""
    
    print('🧹 CLEANING UP PREDICTIONS FOR FINISHED GAMES')
    print('=' * 60)
    print(f'📅 Current Date: {date.today()}')
    print(f'🕐 Current Time: {datetime.now().strftime("%H:%M:%S")}')
    print('=' * 60)
    
    conn = sqlite3.connect('./football.db')
    cursor = conn.cursor()
    
    # First, check how many predictions exist for finished games
    print('\n🔍 CHECKING PREDICTIONS FOR FINISHED GAMES:')
    cursor.execute('''
        SELECT COUNT(*) as count
        FROM daily_predictions dp
        LEFT JOIN cached_fixtures cf ON (
            dp.home_team = cf.home_team AND 
            dp.away_team = cf.away_team AND
            DATE(dp.fixture_date) = DATE(cf.fixture_date)
        )
        WHERE dp.prediction_date = ?
        AND cf.status IN ('Finished', 'FT', 'finished', 'completed', 'Full Time', 'After Pen.', 'AET', 'Postponed', 'Cancelled', 'Abandoned')
    ''', (str(date.today()),))
    
    finished_count = cursor.fetchone()[0]
    print(f'❌ Found {finished_count} predictions for finished games')
    
    if finished_count == 0:
        print('✅ No cleanup needed - no predictions for finished games found')
        conn.close()
        return
    
    # Show which games will be cleaned up
    print('\n📋 PREDICTIONS TO BE REMOVED:')
    cursor.execute('''
        SELECT dp.home_team, dp.away_team, cf.status, dp.fixture_date
        FROM daily_predictions dp
        LEFT JOIN cached_fixtures cf ON (
            dp.home_team = cf.home_team AND 
            dp.away_team = cf.away_team AND
            DATE(dp.fixture_date) = DATE(cf.fixture_date)
        )
        WHERE dp.prediction_date = ?
        AND cf.status IN ('Finished', 'FT', 'finished', 'completed', 'Full Time', 'After Pen.', 'AET', 'Postponed', 'Cancelled', 'Abandoned')
    ''', (str(date.today()),))
    
    finished_predictions = cursor.fetchall()
    for i, (home, away, status, fixture_date) in enumerate(finished_predictions, 1):
        try:
            dt = datetime.fromisoformat(fixture_date.replace('Z', '+00:00'))
            time_str = dt.strftime('%H:%M')
        except:
            time_str = 'Unknown'
        print(f'{i:2d}. ❌ {home} vs {away} ({time_str}) - Status: {status}')
    
    # Confirm cleanup
    print(f'\n⚠️  ABOUT TO REMOVE {finished_count} PREDICTIONS FOR FINISHED GAMES')
    response = input('Continue? (y/N): ').lower().strip()
    
    if response != 'y':
        print('❌ Cleanup cancelled by user')
        conn.close()
        return
    
    # Perform cleanup
    print('\n🧹 PERFORMING CLEANUP...')
    
    # Delete predictions for finished games
    cursor.execute('''
        DELETE FROM daily_predictions 
        WHERE id IN (
            SELECT dp.id
            FROM daily_predictions dp
            LEFT JOIN cached_fixtures cf ON (
                dp.home_team = cf.home_team AND 
                dp.away_team = cf.away_team AND
                DATE(dp.fixture_date) = DATE(cf.fixture_date)
            )
            WHERE dp.prediction_date = ?
            AND cf.status IN ('Finished', 'FT', 'finished', 'completed', 'Full Time', 'After Pen.', 'AET', 'Postponed', 'Cancelled', 'Abandoned')
        )
    ''', (str(date.today()),))
    
    deleted_count = cursor.rowcount
    conn.commit()
    
    print(f'✅ Successfully removed {deleted_count} predictions for finished games')
    
    # Verify cleanup
    print('\n🔍 VERIFYING CLEANUP:')
    cursor.execute('''
        SELECT COUNT(*) as count
        FROM daily_predictions dp
        LEFT JOIN cached_fixtures cf ON (
            dp.home_team = cf.home_team AND 
            dp.away_team = cf.away_team AND
            DATE(dp.fixture_date) = DATE(cf.fixture_date)
        )
        WHERE dp.prediction_date = ?
        AND cf.status IN ('Finished', 'FT', 'finished', 'completed', 'Full Time', 'After Pen.', 'AET', 'Postponed', 'Cancelled', 'Abandoned')
    ''', (str(date.today()),))
    
    remaining_finished = cursor.fetchone()[0]
    
    # Check remaining predictions
    cursor.execute('''
        SELECT COUNT(*) as count
        FROM daily_predictions dp
        LEFT JOIN cached_fixtures cf ON (
            dp.home_team = cf.home_team AND 
            dp.away_team = cf.away_team AND
            DATE(dp.fixture_date) = DATE(cf.fixture_date)
        )
        WHERE dp.prediction_date = ?
        AND (cf.status IS NULL OR cf.status NOT IN ('Finished', 'FT', 'finished', 'completed', 'Full Time', 'After Pen.', 'AET', 'Postponed', 'Cancelled', 'Abandoned'))
    ''', (str(date.today()),))
    
    remaining_upcoming = cursor.fetchone()[0]
    
    print(f'✅ Remaining predictions for finished games: {remaining_finished}')
    print(f'✅ Remaining predictions for upcoming games: {remaining_upcoming}')
    
    if remaining_finished == 0:
        print('\n🎉 SUCCESS: All predictions for finished games have been removed!')
        print('✅ System now only shows predictions for upcoming games')
    else:
        print('\n⚠️  WARNING: Some predictions for finished games still remain')
        print('🔧 Manual review may be needed')
    
    conn.close()
    
    print('\n' + '=' * 60)
    print('🧹 CLEANUP COMPLETED')
    print('=' * 60)

if __name__ == "__main__":
    cleanup_finished_predictions()
