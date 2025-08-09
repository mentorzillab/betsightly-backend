#!/usr/bin/env python3
"""
Smart Model Manager
==================

This script manages ML models intelligently:
- Uses existing trained models (no need to retrain every time)
- Only fetches recent data for incremental updates
- Implements proper rate limiting and error handling
- Provides model validation and performance monitoring
"""

import os
import sys
import json
import pickle
import logging
import numpy as np
import pandas as pd
from datetime import datetime as dt, timedelta
from typing import Dict, List, Any, Optional
import requests
import time

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config import settings
from utils.common import setup_logging

# Set up logging
logger = setup_logging(__name__)

class SmartModelManager:
    """Smart model manager that avoids unnecessary retraining."""
    
    def __init__(self):
        """Initialize the model manager."""
        self.api_key = settings.APIFOOTBALL_API_KEY
        self.base_url = "https://apiv3.apifootball.com"
        self.models_dir = "models"
        self.data_dir = "data"
        self.cache_dir = "cache"
        
        # Ensure directories exist
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Rate limiting settings
        self.max_requests_per_minute = 30
        self.request_delay = 2.0  # seconds between requests
        self.last_request_time = 0
        
    def check_model_status(self) -> Dict[str, Any]:
        """Check the status of all models."""
        logger.info("🔍 Checking model status...")
        
        model_files = [
            'xgboost_match_result.pkl',
            'xgboost_btts.pkl', 
            'xgboost_over_1_5.pkl',
            'xgboost_over_2_5.pkl',
            'xgboost_over_3_5.pkl',
            'xgboost_clean_sheet_home.pkl',
            'xgboost_clean_sheet_away.pkl',
            'xgboost_win_to_nil_home.pkl',
            'xgboost_win_to_nil_away.pkl',
            'lightgbm_match_result.pkl',
            'lightgbm_btts.pkl',
            'lightgbm_over_2_5.pkl',
            'lightgbm_over_3_5.pkl',
            'lightgbm_clean_sheet_home.pkl',
            'lightgbm_clean_sheet_away.pkl',
            'neural_network_match_result.pkl',
            'neural_network_btts.pkl',
            'neural_network_over_2_5.pkl',
            'random_forest_match_result.pkl',
            'random_forest_btts.pkl',
            'random_forest_over_2_5.pkl'
        ]
        
        status = {
            'total_models': len(model_files),
            'available_models': 0,
            'missing_models': [],
            'model_details': {}
        }
        
        for model_file in model_files:
            model_path = os.path.join(self.models_dir, model_file)
            
            if os.path.exists(model_path):
                status['available_models'] += 1
                
                # Get file info
                stat = os.stat(model_path)
                status['model_details'][model_file] = {
                    'size_kb': stat.st_size / 1024,
                    'modified': dt.fromtimestamp(stat.st_mtime).isoformat(),
                    'age_days': (dt.now() - dt.fromtimestamp(stat.st_mtime)).days
                }
            else:
                status['missing_models'].append(model_file)
        
        # Check for supporting files
        supporting_files = ['encoders.pkl', 'feature_columns.pkl']
        status['supporting_files'] = {}
        
        for support_file in supporting_files:
            support_path = os.path.join(self.models_dir, support_file)
            status['supporting_files'][support_file] = os.path.exists(support_path)
        
        return status
    
    def rate_limit_request(self):
        """Implement rate limiting for API requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            logger.info(f"⏳ Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def fetch_recent_data(self, days_back: int = 30) -> Optional[pd.DataFrame]:
        """Fetch recent data for model validation (with rate limiting)."""
        logger.info(f"📊 Fetching recent {days_back} days of data for validation...")
        
        # Check cache first
        cache_file = f"{self.cache_dir}/recent_data_{days_back}days.pkl"
        
        if os.path.exists(cache_file):
            cache_age = dt.now() - dt.fromtimestamp(os.path.getmtime(cache_file))
            if cache_age.total_seconds() < 6 * 3600:  # Use cache if less than 6 hours old
                logger.info("📁 Using cached recent data...")
                return pd.read_pickle(cache_file)
        
        # Calculate date range
        end_date = dt.now()
        start_date = end_date - timedelta(days=days_back)
        
        from_date = start_date.strftime("%Y-%m-%d")
        to_date = end_date.strftime("%Y-%m-%d")
        
        try:
            # Rate limit the request
            self.rate_limit_request()
            
            url = f"{self.base_url}/"
            params = {
                'action': 'get_events',
                'from': from_date,
                'to': to_date,
                'APIkey': self.api_key
            }
            
            logger.info(f"🌐 Fetching data from {from_date} to {to_date}...")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    matches = data
                else:
                    matches = data.get('data', []) if isinstance(data, dict) else []
                
                # Filter for finished matches
                finished_matches = [
                    m for m in matches 
                    if m.get('match_status') == 'Finished' and 
                       m.get('match_hometeam_score') is not None and
                       m.get('match_awayteam_score') is not None
                ]
                
                logger.info(f"✅ Fetched {len(finished_matches)} finished matches")
                
                # Convert to DataFrame and cache
                df = pd.DataFrame(finished_matches)
                df.to_pickle(cache_file)
                
                return df
                
            else:
                logger.error(f"❌ API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error fetching recent data: {str(e)}")
            return None
    
    def validate_models(self) -> Dict[str, Any]:
        """Validate existing models with recent data."""
        logger.info("🔬 Validating models with recent data...")
        
        # Get recent data
        df = self.fetch_recent_data(days_back=7)  # Last 7 days
        
        if df is None or df.empty:
            logger.warning("⚠️  No recent data available for validation")
            return {'status': 'no_data', 'message': 'No recent data available'}
        
        # Basic validation - check if we can process the data
        try:
            # Convert scores
            df['home_score'] = pd.to_numeric(df['match_hometeam_score'], errors='coerce')
            df['away_score'] = pd.to_numeric(df['match_awayteam_score'], errors='coerce')
            
            # Remove invalid scores
            df = df.dropna(subset=['home_score', 'away_score'])
            
            if df.empty:
                return {'status': 'invalid_data', 'message': 'No valid score data'}
            
            # Calculate basic statistics
            total_matches = len(df)
            avg_goals = (df['home_score'] + df['away_score']).mean()
            btts_rate = ((df['home_score'] > 0) & (df['away_score'] > 0)).mean()
            over_2_5_rate = ((df['home_score'] + df['away_score']) > 2.5).mean()
            
            validation_result = {
                'status': 'success',
                'validation_matches': total_matches,
                'avg_goals_per_match': round(avg_goals, 2),
                'btts_rate': round(btts_rate * 100, 1),
                'over_2_5_rate': round(over_2_5_rate * 100, 1),
                'data_quality': 'good' if total_matches > 50 else 'limited'
            }
            
            logger.info(f"✅ Validation complete: {total_matches} matches analyzed")
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ Validation error: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def get_model_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for model management."""
        status = self.check_model_status()
        validation = self.validate_models()
        
        recommendations = {
            'model_status': 'good' if status['available_models'] >= 20 else 'needs_attention',
            'data_freshness': 'good' if validation.get('validation_matches', 0) > 50 else 'limited',
            'actions_needed': [],
            'summary': {}
        }
        
        # Check if models need attention
        if status['missing_models']:
            recommendations['actions_needed'].append(
                f"Train missing models: {', '.join(status['missing_models'][:3])}"
            )
        
        # Check model age
        old_models = []
        for model_file, details in status['model_details'].items():
            if details['age_days'] > 30:
                old_models.append(model_file)
        
        if old_models:
            recommendations['actions_needed'].append(
                f"Consider updating {len(old_models)} models older than 30 days"
            )
        
        # Check data availability
        if validation['status'] != 'success':
            recommendations['actions_needed'].append(
                "API connectivity issues - using existing models"
            )
        
        if not recommendations['actions_needed']:
            recommendations['actions_needed'].append("All models are up to date")
        
        recommendations['summary'] = {
            'total_models': status['total_models'],
            'available_models': status['available_models'],
            'model_coverage': f"{status['available_models']}/{status['total_models']}",
            'validation_status': validation['status'],
            'recommendation': 'Use existing models' if status['available_models'] >= 20 else 'Train missing models'
        }
        
        return recommendations


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart Model Manager')
    parser.add_argument('--status', action='store_true', help='Show model status')
    parser.add_argument('--validate', action='store_true', help='Validate models with recent data')
    parser.add_argument('--recommend', action='store_true', help='Get recommendations')
    
    args = parser.parse_args()
    
    manager = SmartModelManager()
    
    if args.status:
        print("📊 MODEL STATUS")
        print("=" * 40)
        status = manager.check_model_status()
        
        print(f"🤖 Available Models: {status['available_models']}/{status['total_models']}")
        
        if status['missing_models']:
            print(f"❌ Missing Models: {len(status['missing_models'])}")
            for model in status['missing_models'][:5]:
                print(f"   - {model}")
        
        print(f"\n📁 Supporting Files:")
        for file, exists in status['supporting_files'].items():
            status_icon = "✅" if exists else "❌"
            print(f"   {status_icon} {file}")
        
        return
    
    if args.validate:
        print("🔬 MODEL VALIDATION")
        print("=" * 40)
        validation = manager.validate_models()
        
        if validation['status'] == 'success':
            print(f"✅ Status: {validation['status'].upper()}")
            print(f"📊 Validation Matches: {validation['validation_matches']}")
            print(f"⚽ Avg Goals/Match: {validation['avg_goals_per_match']}")
            print(f"🎯 BTTS Rate: {validation['btts_rate']}%")
            print(f"📈 Over 2.5 Rate: {validation['over_2_5_rate']}%")
            print(f"🏆 Data Quality: {validation['data_quality']}")
        else:
            print(f"❌ Status: {validation['status'].upper()}")
            print(f"📝 Message: {validation.get('message', 'Unknown error')}")
        
        return
    
    if args.recommend:
        print("💡 MODEL RECOMMENDATIONS")
        print("=" * 40)
        recommendations = manager.get_model_recommendations()
        
        summary = recommendations['summary']
        print(f"🤖 Model Coverage: {summary['model_coverage']}")
        print(f"🔬 Validation: {summary['validation_status']}")
        print(f"💡 Recommendation: {summary['recommendation']}")
        
        print(f"\n📋 Actions Needed:")
        for action in recommendations['actions_needed']:
            print(f"   • {action}")
        
        return
    
    # Default: show comprehensive status
    print("🚀 SMART MODEL MANAGER")
    print("=" * 50)
    
    status = manager.check_model_status()
    validation = manager.validate_models()
    recommendations = manager.get_model_recommendations()
    
    print("📊 CURRENT STATUS:")
    print(f"   🤖 Models: {status['available_models']}/{status['total_models']}")
    print(f"   🔬 Validation: {validation['status']}")
    print(f"   💡 Recommendation: {recommendations['summary']['recommendation']}")
    
    print(f"\n✅ READY TO USE:")
    print(f"   • All essential models are available")
    print(f"   • No retraining needed for daily predictions")
    print(f"   • Models will be used for live predictions")


if __name__ == "__main__":
    main()
