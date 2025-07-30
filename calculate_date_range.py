#!/usr/bin/env python3
"""
Calculate date range from tomorrow through Sunday for prediction generation.
Uses Nigeria timezone (WAT - UTC+1).
"""

import pytz
from datetime import datetime, timedelta

def calculate_prediction_dates():
    """Calculate the date range from tomorrow through Sunday in Nigeria timezone."""
    
    # Get current time in Nigeria (WAT - UTC+1)
    utc_now = datetime.now(pytz.UTC)
    nigeria_tz = pytz.timezone('Africa/Lagos')
    nigeria_time = utc_now.astimezone(nigeria_tz)
    
    print(f"🇳🇬 Current Nigeria Time: {nigeria_time.strftime('%Y-%m-%d %H:%M:%S WAT')}")
    print(f"📅 Current Day: {nigeria_time.strftime('%A')}")
    
    # Calculate tomorrow
    tomorrow = nigeria_time + timedelta(days=1)
    tomorrow_date = tomorrow.date()
    
    print(f"🌅 Tomorrow: {tomorrow_date.strftime('%Y-%m-%d')} ({tomorrow.strftime('%A')})")
    
    # Find the next Sunday
    days_until_sunday = (6 - tomorrow.weekday()) % 7  # Sunday is 6
    if days_until_sunday == 0 and tomorrow.weekday() != 6:  # If tomorrow is not Sunday
        days_until_sunday = 7  # Go to next Sunday
    
    sunday_date = tomorrow_date + timedelta(days=days_until_sunday)
    
    print(f"📅 Target Sunday: {sunday_date.strftime('%Y-%m-%d')}")
    
    # Generate all dates from tomorrow through Sunday
    prediction_dates = []
    current_date = tomorrow_date
    
    while current_date <= sunday_date:
        day_name = (nigeria_time.replace(year=current_date.year, month=current_date.month, day=current_date.day)).strftime('%A')
        prediction_dates.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'day_name': day_name,
            'date_obj': current_date
        })
        current_date += timedelta(days=1)
    
    print(f"\n📋 Prediction Dates ({len(prediction_dates)} days):")
    for i, date_info in enumerate(prediction_dates, 1):
        print(f"   {i}. {date_info['date']} ({date_info['day_name']})")
    
    return prediction_dates, nigeria_time

if __name__ == "__main__":
    dates, current_time = calculate_prediction_dates()
    
    # Create filename for the output
    start_date = dates[0]['date']
    end_date = dates[-1]['date']
    filename = f"predictions_{start_date}_to_{end_date}.txt"
    
    print(f"\n📄 Output filename: {filename}")
