#!/usr/bin/env python3
"""
Fixture Cache Service
Caches fixtures locally to avoid repeated API calls and reduce API usage.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import hashlib

# Set up logging
logger = logging.getLogger(__name__)

class FixtureCacheService:
    """
    Service for caching fixtures to reduce API calls.
    
    Features:
    - Saves fixtures to local JSON files
    - Automatic cache expiration
    - Cache validation and cleanup
    - Multiple cache strategies (by date, by league, etc.)
    """
    
    def __init__(self, cache_dir: str = "cache/fixtures"):
        """
        Initialize fixture cache service.
        
        Args:
            cache_dir: Directory to store cached fixtures
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache settings
        self.cache_expiry_hours = 6  # Cache expires after 6 hours
        self.max_cache_files = 100   # Maximum number of cache files to keep
        
        logger.info(f"🗄️  Fixture cache initialized: {self.cache_dir}")
    
    def get_cache_key(self, date: str, source: str = "apifootball") -> str:
        """
        Generate cache key for fixtures.
        
        Args:
            date: Date in YYYY-MM-DD format
            source: Data source (apifootball, football-data, etc.)
            
        Returns:
            Cache key string
        """
        key_data = f"{source}_{date}"
        return hashlib.md5(key_data.encode()).hexdigest()[:12]
    
    def get_cache_file_path(self, date: str, source: str = "apifootball") -> Path:
        """
        Get cache file path for fixtures.
        
        Args:
            date: Date in YYYY-MM-DD format
            source: Data source
            
        Returns:
            Path to cache file
        """
        cache_key = self.get_cache_key(date, source)
        return self.cache_dir / f"fixtures_{date}_{cache_key}.json"
    
    def is_cache_valid(self, cache_file: Path) -> bool:
        """
        Check if cache file is still valid (not expired).
        
        Args:
            cache_file: Path to cache file
            
        Returns:
            True if cache is valid, False if expired
        """
        if not cache_file.exists():
            return False
        
        try:
            # Check file modification time
            file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            expiry_time = file_time + timedelta(hours=self.cache_expiry_hours)
            
            is_valid = datetime.now() < expiry_time
            
            if not is_valid:
                logger.info(f"🕒 Cache expired: {cache_file.name}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"❌ Error checking cache validity: {str(e)}")
            return False
    
    def save_fixtures_to_cache(self, fixtures: List[Dict[str, Any]], date: str, 
                              source: str = "apifootball") -> bool:
        """
        Save fixtures to cache.
        
        Args:
            fixtures: List of fixture dictionaries
            date: Date in YYYY-MM-DD format
            source: Data source
            
        Returns:
            True if saved successfully
        """
        try:
            cache_file = self.get_cache_file_path(date, source)
            
            cache_data = {
                "date": date,
                "source": source,
                "cached_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=self.cache_expiry_hours)).isoformat(),
                "fixture_count": len(fixtures),
                "fixtures": fixtures
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"💾 Cached {len(fixtures)} fixtures for {date} ({source})")
            logger.info(f"📁 Cache file: {cache_file.name}")
            
            # Clean up old cache files
            self._cleanup_old_cache_files()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving fixtures to cache: {str(e)}")
            return False
    
    def load_fixtures_from_cache(self, date: str, source: str = "apifootball") -> Optional[List[Dict[str, Any]]]:
        """
        Load fixtures from cache.
        
        Args:
            date: Date in YYYY-MM-DD format
            source: Data source
            
        Returns:
            List of fixtures if cache is valid, None otherwise
        """
        try:
            cache_file = self.get_cache_file_path(date, source)
            
            if not self.is_cache_valid(cache_file):
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            fixtures = cache_data.get('fixtures', [])
            cached_at = cache_data.get('cached_at', 'unknown')
            
            logger.info(f"📂 Loaded {len(fixtures)} fixtures from cache for {date}")
            logger.info(f"🕒 Cached at: {cached_at}")
            
            return fixtures
            
        except Exception as e:
            logger.error(f"❌ Error loading fixtures from cache: {str(e)}")
            return None
    
    def get_cached_fixtures_info(self, date: str, source: str = "apifootball") -> Optional[Dict[str, Any]]:
        """
        Get information about cached fixtures without loading them.
        
        Args:
            date: Date in YYYY-MM-DD format
            source: Data source
            
        Returns:
            Cache info dictionary or None
        """
        try:
            cache_file = self.get_cache_file_path(date, source)
            
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            return {
                "date": cache_data.get('date'),
                "source": cache_data.get('source'),
                "cached_at": cache_data.get('cached_at'),
                "expires_at": cache_data.get('expires_at'),
                "fixture_count": cache_data.get('fixture_count', 0),
                "is_valid": self.is_cache_valid(cache_file),
                "file_size": cache_file.stat().st_size,
                "cache_file": cache_file.name
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting cache info: {str(e)}")
            return None
    
    def _cleanup_old_cache_files(self):
        """Clean up old cache files to prevent disk space issues."""
        try:
            cache_files = list(self.cache_dir.glob("fixtures_*.json"))
            
            if len(cache_files) <= self.max_cache_files:
                return
            
            # Sort by modification time (oldest first)
            cache_files.sort(key=lambda f: f.stat().st_mtime)
            
            # Remove oldest files
            files_to_remove = len(cache_files) - self.max_cache_files
            
            for cache_file in cache_files[:files_to_remove]:
                try:
                    cache_file.unlink()
                    logger.info(f"🗑️  Removed old cache file: {cache_file.name}")
                except Exception as e:
                    logger.error(f"❌ Error removing cache file {cache_file.name}: {str(e)}")
            
        except Exception as e:
            logger.error(f"❌ Error during cache cleanup: {str(e)}")
    
    def clear_cache(self, date: Optional[str] = None, source: Optional[str] = None):
        """
        Clear cache files.
        
        Args:
            date: Specific date to clear (optional)
            source: Specific source to clear (optional)
        """
        try:
            if date and source:
                # Clear specific cache file
                cache_file = self.get_cache_file_path(date, source)
                if cache_file.exists():
                    cache_file.unlink()
                    logger.info(f"🗑️  Cleared cache for {date} ({source})")
            else:
                # Clear all cache files
                cache_files = list(self.cache_dir.glob("fixtures_*.json"))
                
                for cache_file in cache_files:
                    cache_file.unlink()
                
                logger.info(f"🗑️  Cleared {len(cache_files)} cache files")
                
        except Exception as e:
            logger.error(f"❌ Error clearing cache: {str(e)}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            cache_files = list(self.cache_dir.glob("fixtures_*.json"))
            
            total_size = sum(f.stat().st_size for f in cache_files)
            valid_files = sum(1 for f in cache_files if self.is_cache_valid(f))
            
            return {
                "total_files": len(cache_files),
                "valid_files": valid_files,
                "expired_files": len(cache_files) - valid_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "cache_dir": str(self.cache_dir),
                "expiry_hours": self.cache_expiry_hours,
                "max_files": self.max_cache_files
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting cache stats: {str(e)}")
            return {}
    
    def list_cached_dates(self) -> List[str]:
        """
        List all dates that have cached fixtures.
        
        Returns:
            List of dates in YYYY-MM-DD format
        """
        try:
            cache_files = list(self.cache_dir.glob("fixtures_*.json"))
            dates = set()
            
            for cache_file in cache_files:
                try:
                    # Extract date from filename: fixtures_YYYY-MM-DD_hash.json
                    parts = cache_file.stem.split('_')
                    if len(parts) >= 2:
                        date_part = parts[1]
                        if len(date_part) == 10 and date_part.count('-') == 2:
                            dates.add(date_part)
                except:
                    continue
            
            return sorted(list(dates))
            
        except Exception as e:
            logger.error(f"❌ Error listing cached dates: {str(e)}")
            return []
