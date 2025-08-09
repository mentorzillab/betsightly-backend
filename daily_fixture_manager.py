#!/usr/bin/env python3
"""
Daily Fixture Manager
====================

This module manages daily fixtures with persistent caching:
- Fetches fixtures once per day and caches them
- Provides access to cached fixtures for multiple prediction runs
- Handles fixture updates and expiration
- Supports manual refresh when needed
"""

import os
import json
import pickle
import logging
import requests
import time
from datetime import datetime as dt, timedelta
from typing import Dict, List, Any, Optional

# Add current directory to path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config import settings
from utils.common import setup_logging

# Set up logging
logger = setup_logging(__name__)

class DailyFixtureManager:
    """Manages daily fixtures with persistent caching."""
    
    def __init__(self):
        """Initialize the fixture manager."""
        self.api_key = settings.APIFOOTBALL_API_KEY
        self.base_url = "https://apiv3.apifootball.com"
        self.cache_dir = "cache/fixtures"
        self.data_dir = "data/fixtures"
        
        # Ensure directories exist
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Rate limiting
        self.request_delay = 2.0
        self.last_request_time = 0
        
    def get_cache_file_path(self, date: str) -> str:
        """Get the cache file path for a specific date."""
        return os.path.join(self.cache_dir, f"fixtures_{date}.json")
    
    def get_data_file_path(self, date: str) -> str:
        """Get the data file path for a specific date."""
        return os.path.join(self.data_dir, f"fixtures_{date}.pkl")
    
    def is_cache_valid(self, date: str) -> bool:
        """Check if cached fixtures for a date are still valid."""
        cache_file = self.get_cache_file_path(date)
        
        if not os.path.exists(cache_file):
            return False
        
        # Check if cache is from today and not too old
        cache_time = dt.fromtimestamp(os.path.getmtime(cache_file))
        now = dt.now()
        
        # Cache is valid if:
        # 1. It's from today and less than 6 hours old, OR
        # 2. It's from a past date (historical data)
        cache_date = dt.strptime(date, "%Y-%m-%d").date()
        today = now.date()
        
        if cache_date < today:
            # Historical data - always valid
            return True
        elif cache_date == today:
            # Today's data - valid if less than 6 hours old
            age_hours = (now - cache_time).total_seconds() / 3600
            return age_hours < 6
        else:
            # Future date - valid if less than 24 hours old
            age_hours = (now - cache_time).total_seconds() / 3600
            return age_hours < 24
    
    def rate_limit_request(self):
        """Implement rate limiting for API requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            logger.info(f"⏳ Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def fetch_fixtures_for_date(self, date: str, force_refresh: bool = False) -> Optional[List[Dict]]:
        """Fetch fixtures for a specific date."""
        logger.info(f"📅 Fetching fixtures for {date}...")
        
        # Check cache first
        if not force_refresh and self.is_cache_valid(date):
            logger.info(f"📁 Using cached fixtures for {date}")
            return self.load_cached_fixtures(date)
        
        # Fetch from API
        try:
            self.rate_limit_request()
            
            url = f"{self.base_url}/"
            params = {
                'action': 'get_events',
                'from': date,
                'to': date,
                'APIkey': self.api_key
            }
            
            logger.info(f"🌐 Fetching from API: {date}")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    fixtures = data
                else:
                    fixtures = data.get('data', []) if isinstance(data, dict) else []
                
                # Filter for upcoming fixtures (not finished)
                upcoming_fixtures = []
                for fixture in fixtures:
                    match_status = fixture.get('match_status', '')
                    match_time = fixture.get('match_time', '')
                    
                    # Include fixtures that haven't started yet
                    if match_status == '' or match_status in ['', 'NS', 'Not Started'] or match_time != 'Finished':
                        upcoming_fixtures.append(fixture)
                
                logger.info(f"✅ Fetched {len(upcoming_fixtures)} upcoming fixtures for {date}")
                
                # Cache the results
                self.cache_fixtures(date, upcoming_fixtures)
                
                return upcoming_fixtures
                
            else:
                logger.error(f"❌ API error for {date}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error fetching fixtures for {date}: {str(e)}")
            return None
    
    def cache_fixtures(self, date: str, fixtures: List[Dict]):
        """Cache fixtures for a specific date."""
        try:
            # Save as JSON for easy inspection
            cache_file = self.get_cache_file_path(date)
            with open(cache_file, 'w') as f:
                json.dump({
                    'date': date,
                    'cached_at': dt.now().isoformat(),
                    'fixture_count': len(fixtures),
                    'fixtures': fixtures
                }, f, indent=2)
            
            # Save as pickle for fast loading
            data_file = self.get_data_file_path(date)
            with open(data_file, 'wb') as f:
                pickle.dump(fixtures, f)
            
            logger.info(f"💾 Cached {len(fixtures)} fixtures for {date}")
            
        except Exception as e:
            logger.error(f"❌ Error caching fixtures for {date}: {str(e)}")
    
    def load_cached_fixtures(self, date: str) -> Optional[List[Dict]]:
        """Load cached fixtures for a specific date."""
        try:
            # Try pickle first (faster)
            data_file = self.get_data_file_path(date)
            if os.path.exists(data_file):
                with open(data_file, 'rb') as f:
                    return pickle.load(f)
            
            # Fallback to JSON
            cache_file = self.get_cache_file_path(date)
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    return data.get('fixtures', [])
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error loading cached fixtures for {date}: {str(e)}")
            return None
    
    def get_daily_fixtures(self, date: Optional[str] = None, force_refresh: bool = False) -> Dict[str, Any]:
        """Get fixtures for a specific date (defaults to today)."""
        if date is None:
            date = dt.now().strftime("%Y-%m-%d")
        
        logger.info(f"🏈 Getting daily fixtures for {date}")
        
        fixtures = self.fetch_fixtures_for_date(date, force_refresh)
        
        if fixtures is None:
            return {
                'status': 'failed',
                'date': date,
                'error': 'Failed to fetch fixtures'
            }
        
        return {
            'status': 'success',
            'date': date,
            'fixture_count': len(fixtures),
            'fixtures': fixtures,
            'cached': not force_refresh and self.is_cache_valid(date)
        }
    
    def get_multi_day_fixtures(self, days: int = 2, start_date: Optional[str] = None) -> Dict[str, Any]:
        """Get fixtures for multiple days."""
        if start_date is None:
            start_date = dt.now().strftime("%Y-%m-%d")
        
        logger.info(f"📅 Getting fixtures for {days} days starting from {start_date}")
        
        start_dt = dt.strptime(start_date, "%Y-%m-%d")
        all_fixtures = []
        dates_processed = []
        
        for i in range(days):
            current_date = (start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
            fixtures = self.fetch_fixtures_for_date(current_date)
            
            if fixtures:
                all_fixtures.extend(fixtures)
                dates_processed.append(current_date)
        
        return {
            'status': 'success',
            'dates_processed': dates_processed,
            'total_fixtures': len(all_fixtures),
            'fixtures': all_fixtures
        }
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get status of cached fixtures."""
        cache_files = []
        total_fixtures = 0
        
        if os.path.exists(self.cache_dir):
            for filename in os.listdir(self.cache_dir):
                if filename.startswith('fixtures_') and filename.endswith('.json'):
                    filepath = os.path.join(self.cache_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                            cache_files.append({
                                'date': data.get('date'),
                                'fixture_count': data.get('fixture_count', 0),
                                'cached_at': data.get('cached_at'),
                                'file_size_kb': os.path.getsize(filepath) / 1024
                            })
                            total_fixtures += data.get('fixture_count', 0)
                    except Exception as e:
                        logger.warning(f"Error reading cache file {filename}: {e}")
        
        return {
            'total_cache_files': len(cache_files),
            'total_cached_fixtures': total_fixtures,
            'cache_files': sorted(cache_files, key=lambda x: x['date'], reverse=True)
        }
    
    def cleanup_old_cache(self, days_to_keep: int = 7):
        """Clean up old cache files."""
        logger.info(f"🧹 Cleaning up cache files older than {days_to_keep} days")
        
        cutoff_date = dt.now() - timedelta(days=days_to_keep)
        removed_count = 0
        
        for directory in [self.cache_dir, self.data_dir]:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    if filename.startswith('fixtures_'):
                        filepath = os.path.join(directory, filename)
                        file_time = dt.fromtimestamp(os.path.getmtime(filepath))
                        
                        if file_time < cutoff_date:
                            try:
                                os.remove(filepath)
                                removed_count += 1
                                logger.info(f"🗑️  Removed old cache file: {filename}")
                            except Exception as e:
                                logger.warning(f"Error removing {filename}: {e}")
        
        logger.info(f"✅ Cleanup complete: {removed_count} files removed")


def main():
    """Main execution function for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Daily Fixture Manager')
    parser.add_argument('--date', help='Date to fetch fixtures for (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=1, help='Number of days to fetch')
    parser.add_argument('--force-refresh', action='store_true', help='Force refresh from API')
    parser.add_argument('--status', action='store_true', help='Show cache status')
    parser.add_argument('--cleanup', action='store_true', help='Clean up old cache files')
    
    args = parser.parse_args()
    
    manager = DailyFixtureManager()
    
    if args.status:
        print("📊 FIXTURE CACHE STATUS")
        print("=" * 40)
        status = manager.get_cache_status()
        
        print(f"📁 Total Cache Files: {status['total_cache_files']}")
        print(f"🏈 Total Cached Fixtures: {status['total_cached_fixtures']}")
        
        print("\n📅 Recent Cache Files:")
        for cache_file in status['cache_files'][:10]:
            print(f"  {cache_file['date']}: {cache_file['fixture_count']} fixtures ({cache_file['file_size_kb']:.1f} KB)")
        
        return
    
    if args.cleanup:
        manager.cleanup_old_cache()
        return
    
    if args.days > 1:
        result = manager.get_multi_day_fixtures(days=args.days, start_date=args.date)
    else:
        result = manager.get_daily_fixtures(date=args.date, force_refresh=args.force_refresh)
    
    print("🏈 DAILY FIXTURE RESULTS")
    print("=" * 40)
    
    if result['status'] == 'success':
        if 'dates_processed' in result:
            print(f"📅 Dates: {', '.join(result['dates_processed'])}")
            print(f"🏈 Total Fixtures: {result['total_fixtures']}")
        else:
            print(f"📅 Date: {result['date']}")
            print(f"🏈 Fixtures: {result['fixture_count']}")
            print(f"📁 From Cache: {result['cached']}")
    else:
        print(f"❌ Status: {result['status']}")
        print(f"📝 Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
