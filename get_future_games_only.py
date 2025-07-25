#!/usr/bin/env python3
"""
Get Future Games Only - Real-time timezone aware
"""

import sqlite3
from datetime import datetime, timedelta
import json

def get_future_games_only():
    """Get games that are actually in the future."""
    
    print('🕐 REAL-TIME FUTURE GAMES CHECK')
    print('=' * 50)
    
    # Get current time
    now = datetime.now()
    print(f'Current system time: {now.strftime("%Y-%m-%d %H:%M:%S")}')
    
    # Add buffer for betting
    buffer_time = now + timedelta(minutes=10)
    print(f'Looking for games after: {buffer_time.strftime("%Y-%m-%d %H:%M:%S")}')
    
    # Connect to database
    conn = sqlite3.connect('football.db')
    cursor = conn.cursor()
    
    # Get games that are genuinely in the future
    query = '''
    SELECT 
        fixture_date,
        home_team,
        away_team,
        league_name,
        fixture_id
    FROM cached_fixtures 
    WHERE fixture_date > ?
    AND (status IS NULL OR status NOT IN ('LIVE', 'FINISHED', 'FT'))
    AND fixture_date != '2025-07-25 00:00:00.000000'
    ORDER BY fixture_date ASC
    LIMIT 20
    '''
    
    cursor.execute(query, (buffer_time.strftime('%Y-%m-%d %H:%M:%S'),))
    results = cursor.fetchall()
    
    print(f'\n🎯 FOUND {len(results)} FUTURE GAMES:')
    print('-' * 50)
    
    if results:
        for i, (fixture_date, home, away, league, fixture_id) in enumerate(results, 1):
            # Parse fixture time
            try:
                game_time = datetime.strptime(fixture_date, '%Y-%m-%d %H:%M:%S.%f')
            except:
                try:
                    game_time = datetime.strptime(fixture_date, '%Y-%m-%d %H:%M:%S')
                except:
                    game_time = None
            
            if game_time:
                time_until = game_time - now
                hours = int(time_until.total_seconds() // 3600)
                minutes = int((time_until.total_seconds() % 3600) // 60)
                
                print(f'{i:2d}. {home} vs {away}')
                print(f'    🏆 {league}')
                print(f'    ⏰ {game_time.strftime("%H:%M")} ({hours}h {minutes}m from now)')
                print(f'    🆔 {fixture_id}')
                print()
    else:
        print('❌ No future games found')
        
        # Check what games exist today
        cursor.execute('''
        SELECT fixture_date, home_team, away_team 
        FROM cached_fixtures 
        WHERE DATE(fixture_date) = DATE('now')
        ORDER BY fixture_date DESC
        LIMIT 5
        ''')
        
        recent_games = cursor.fetchall()
        print('\n📊 Recent games from today:')
        for fixture_date, home, away in recent_games:
            print(f'   {fixture_date} - {home} vs {away}')
    
    conn.close()
    return results

if __name__ == "__main__":
    get_future_games_only()
