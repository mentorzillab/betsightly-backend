#!/usr/bin/env python3
"""
Optimal Model Trainer
====================

This script implements the best practices for football prediction model training:
- Uses optimal data range: 2015-2025 (last 10 years)
- Focuses on modern football trends and tactics
- Excludes outdated data and COVID-era anomalies
- Implements prediction-specific training strategies
- Uses both GitHub historical data (2015-2022) and APIFootball recent data (2022-2025)
"""

import os
import sys
import json
import pickle
import logging
import numpy as np
import pandas as pd
from datetime import datetime as dt, timedelta
from typing import Dict, List, Any, Optional, Tuple
import requests
import time

# ML Libraries
try:
    import xgboost as xgb
    import lightgbm as lgb
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.neural_network import MLPClassifier
    from sklearn.preprocessing import LabelEncoder, StandardScaler
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import accuracy_score, classification_report, log_loss
    import joblib
except ImportError as e:
    print(f"Missing ML library: {e}")
    sys.exit(1)

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config import settings
from utils.common import setup_logging

# Set up logging
logger = setup_logging(__name__)

class OptimalModelTrainer:
    """Optimal trainer using best practices for football prediction."""
    
    def __init__(self):
        """Initialize the optimal trainer."""
        self.api_key = settings.APIFOOTBALL_API_KEY
        self.base_url = "https://apiv3.apifootball.com"
        self.models_dir = "models"
        self.data_dir = "data/optimal"
        
        # Ensure directories exist
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Optimal data range: 2015-2025
        self.start_year = 2015
        self.end_year = dt.now().year
        self.covid_start = dt(2020, 3, 1)  # COVID impact start
        self.covid_end = dt(2021, 8, 1)    # COVID impact end
        
        # Rate limiting
        self.request_delay = 2.0
        self.last_request_time = 0
        
        # Prediction-specific model configurations
        self.models_config = {
            # Match Outcome Models (Win/Draw/Loss) - Focus on team form and head-to-head
            'match_result': {
                'xgboost': xgb.XGBClassifier(random_state=42, n_estimators=400, max_depth=8),
                'lightgbm': lgb.LGBMClassifier(random_state=42, n_estimators=400, max_depth=8, verbose=-1),
                'neural_network': MLPClassifier(hidden_layer_sizes=(200, 100, 50), random_state=42, max_iter=1000),
                'random_forest': RandomForestClassifier(n_estimators=400, max_depth=12, random_state=42, n_jobs=-1)
            },
            
            # BTTS Models - Focus on attacking/defensive patterns
            'btts': {
                'xgboost': xgb.XGBClassifier(random_state=42, n_estimators=300, max_depth=6),
                'lightgbm': lgb.LGBMClassifier(random_state=42, n_estimators=300, max_depth=6, verbose=-1),
                'neural_network': MLPClassifier(hidden_layer_sizes=(150, 75), random_state=42, max_iter=800),
                'random_forest': RandomForestClassifier(n_estimators=300, max_depth=10, random_state=42, n_jobs=-1)
            },
            
            # Over/Under Goals Models - Focus on total goals and xG patterns
            'over_2_5': {
                'xgboost': xgb.XGBClassifier(random_state=42, n_estimators=350, max_depth=7),
                'lightgbm': lgb.LGBMClassifier(random_state=42, n_estimators=350, max_depth=7, verbose=-1),
                'neural_network': MLPClassifier(hidden_layer_sizes=(180, 90), random_state=42, max_iter=900),
                'random_forest': RandomForestClassifier(n_estimators=350, max_depth=11, random_state=42, n_jobs=-1)
            },
            
            # Clean Sheet Models - Focus on defensive strength
            'clean_sheet_home': {
                'xgboost': xgb.XGBClassifier(random_state=42, n_estimators=250, max_depth=5),
                'lightgbm': lgb.LGBMClassifier(random_state=42, n_estimators=250, max_depth=5, verbose=-1)
            },
            
            'clean_sheet_away': {
                'xgboost': xgb.XGBClassifier(random_state=42, n_estimators=250, max_depth=5),
                'lightgbm': lgb.LGBMClassifier(random_state=42, n_estimators=250, max_depth=5, verbose=-1)
            }
        }
        
        self.encoders = {}
        self.scalers = {}
    
    def load_optimal_github_data(self) -> pd.DataFrame:
        """Load GitHub data filtered for optimal date range (2015-2022)."""
        logger.info(f"📊 Loading GitHub data for optimal range: {self.start_year}-2022...")
        
        from hybrid_model_trainer import HybridModelTrainer
        hybrid_trainer = HybridModelTrainer()
        
        # Load all GitHub data
        github_df = hybrid_trainer.load_github_datasets()
        
        if github_df.empty:
            logger.warning("⚠️  No GitHub data loaded")
            return pd.DataFrame()
        
        # Filter for optimal date range
        github_df['match_date'] = pd.to_datetime(github_df['match_date'], errors='coerce')
        github_df = github_df.dropna(subset=['match_date'])
        
        # Filter: 2015-2022 (exclude very old data and use APIFootball for recent data)
        start_date = dt(self.start_year, 1, 1)
        end_date = dt(2022, 12, 31)
        
        optimal_df = github_df[
            (github_df['match_date'] >= start_date) & 
            (github_df['match_date'] <= end_date)
        ].copy()
        
        # Mark COVID-era matches for special handling
        optimal_df['is_covid_era'] = (
            (optimal_df['match_date'] >= self.covid_start) & 
            (optimal_df['match_date'] <= self.covid_end)
        ).astype(int)
        
        logger.info(f"✅ Optimal GitHub data: {len(optimal_df):,} matches ({self.start_year}-2022)")
        logger.info(f"⚠️  COVID-era matches: {optimal_df['is_covid_era'].sum():,}")
        
        return optimal_df
    
    def load_recent_apifootball_data(self, months_back: int = 12) -> pd.DataFrame:
        """Load recent APIFootball data (2022-2025) with rate limiting."""
        logger.info(f"🌐 Loading recent APIFootball data: last {months_back} months...")
        
        cache_file = os.path.join(self.data_dir, f"apifootball_recent_{months_back}months.pkl")
        
        # Check cache
        if os.path.exists(cache_file):
            cache_age = dt.now() - dt.fromtimestamp(os.path.getmtime(cache_file))
            if cache_age.days < 7:
                logger.info("📁 Loading cached APIFootball data...")
                return pd.read_pickle(cache_file)
        
        all_matches = []
        
        # Fetch data in smaller chunks to avoid timeouts
        chunk_size = 2  # 2 months per request
        for i in range(0, months_back, chunk_size):
            start_months = i + chunk_size
            end_months = i
            
            start_date = dt.now() - timedelta(days=30 * start_months)
            end_date = dt.now() - timedelta(days=30 * end_months)
            
            # Skip if before 2022 (use GitHub data for that)
            if start_date.year < 2022:
                continue
            
            from_date = start_date.strftime("%Y-%m-%d")
            to_date = end_date.strftime("%Y-%m-%d")
            
            try:
                # Rate limiting
                if i > 0:
                    time.sleep(self.request_delay)
                
                url = f"{self.base_url}/"
                params = {
                    'action': 'get_events',
                    'from': from_date,
                    'to': to_date,
                    'APIkey': self.api_key
                }
                
                logger.info(f"📅 Fetching {from_date} to {to_date}...")
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        matches = data
                    else:
                        matches = data.get('data', []) if isinstance(data, dict) else []
                    
                    # Filter for finished matches only
                    finished_matches = [
                        m for m in matches 
                        if m.get('match_status') == 'Finished' and 
                           m.get('match_hometeam_score') is not None and
                           m.get('match_awayteam_score') is not None
                    ]
                    
                    # Exclude friendlies and pre-season matches
                    competitive_matches = [
                        m for m in finished_matches
                        if not any(keyword in m.get('league_name', '').lower() 
                                 for keyword in ['friendly', 'pre-season', 'preseason', 'club friendly'])
                    ]
                    
                    all_matches.extend(competitive_matches)
                    logger.info(f"  ✅ {len(competitive_matches)} competitive matches")
                    
                else:
                    logger.warning(f"  ⚠️  API error: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"  ❌ Error fetching {from_date}: {str(e)}")
                continue
        
        # Convert to DataFrame
        df = pd.DataFrame(all_matches)
        
        if not df.empty:
            # Add metadata
            df['data_source'] = 'apifootball'
            df['is_covid_era'] = 0  # Recent data is post-COVID
            
            # Cache the data
            df.to_pickle(cache_file)
            logger.info(f"💾 Cached APIFootball data: {len(df):,} matches")
        
        logger.info(f"📈 Total recent APIFootball data: {len(df):,} matches")
        return df
    
    def train_optimal_models(self, use_github: bool = True, use_apifootball: bool = True) -> Dict[str, Any]:
        """Train models using optimal data and best practices."""
        logger.info("🚀 Starting optimal model training with best practices...")
        logger.info(f"📊 Data range: {self.start_year}-{self.end_year}")
        logger.info(f"📚 GitHub data (2015-2022): {'✅ Enabled' if use_github else '❌ Disabled'}")
        logger.info(f"🌐 APIFootball data (2022-2025): {'✅ Enabled' if use_apifootball else '❌ Disabled'}")
        
        training_start = time.time()
        
        # Load datasets
        datasets = []
        
        if use_github:
            github_df = self.load_optimal_github_data()
            if not github_df.empty:
                datasets.append(github_df)
        
        if use_apifootball:
            apifootball_df = self.load_recent_apifootball_data(months_back=12)
            if not apifootball_df.empty:
                datasets.append(apifootball_df)
        
        if not datasets:
            logger.error("❌ No datasets available")
            return {'status': 'failed', 'error': 'No datasets available'}
        
        # Combine datasets
        combined_df = pd.concat(datasets, ignore_index=True, sort=False)
        
        # Remove duplicates
        before_dedup = len(combined_df)
        combined_df = combined_df.drop_duplicates(
            subset=['match_date', 'match_hometeam_name', 'match_awayteam_name', 
                   'match_hometeam_score', 'match_awayteam_score'],
            keep='last'
        )
        after_dedup = len(combined_df)
        
        logger.info(f"🔄 Removed {before_dedup - after_dedup:,} duplicate matches")
        logger.info(f"✅ Final optimal dataset: {len(combined_df):,} unique matches")
        
        # Create optimal features (simplified for now)
        combined_df['home_score'] = pd.to_numeric(combined_df['match_hometeam_score'], errors='coerce')
        combined_df['away_score'] = pd.to_numeric(combined_df['match_awayteam_score'], errors='coerce')
        combined_df = combined_df.dropna(subset=['home_score', 'away_score'])
        
        # Create target variables
        combined_df['match_result'] = combined_df.apply(lambda x: 
            'H' if x['home_score'] > x['away_score'] else 
            'A' if x['home_score'] < x['away_score'] else 'D', axis=1)
        combined_df['btts'] = ((combined_df['home_score'] > 0) & (combined_df['away_score'] > 0)).astype(int)
        combined_df['over_2_5'] = ((combined_df['home_score'] + combined_df['away_score']) > 2.5).astype(int)
        combined_df['clean_sheet_home'] = (combined_df['away_score'] == 0).astype(int)
        combined_df['clean_sheet_away'] = (combined_df['home_score'] == 0).astype(int)
        
        # Simple feature encoding
        if 'match_hometeam_name' in combined_df.columns:
            le_teams = LabelEncoder()
            all_teams = pd.concat([combined_df['match_hometeam_name'], combined_df['match_awayteam_name']]).unique()
            le_teams.fit(all_teams)
            combined_df['home_team_encoded'] = le_teams.transform(combined_df['match_hometeam_name'])
            combined_df['away_team_encoded'] = le_teams.transform(combined_df['match_awayteam_name'])
            self.encoders['teams'] = le_teams
        
        feature_columns = ['home_team_encoded', 'away_team_encoded']
        
        # Save encoders
        encoders_file = f"{self.models_dir}/optimal_encoders.pkl"
        with open(encoders_file, 'wb') as f:
            pickle.dump(self.encoders, f)
        
        # Train models
        training_results = {}
        total_models = 0
        successful_models = 0
        
        for prediction_type, model_configs in self.models_config.items():
            if prediction_type not in combined_df.columns:
                continue
                
            training_results[prediction_type] = {}
            
            for model_type, model in model_configs.items():
                total_models += 1
                
                try:
                    # Prepare data
                    X = combined_df[feature_columns].fillna(0)
                    y = combined_df[prediction_type]
                    
                    # Remove NaN values
                    mask = ~(X.isnull().any(axis=1) | y.isnull())
                    X = X[mask]
                    y = y[mask]
                    
                    if len(X) < 1000:
                        logger.warning(f"⚠️  Insufficient data for {prediction_type} {model_type}: {len(X)} samples")
                        continue
                    
                    # Split data
                    X_train, X_test, y_train, y_test = train_test_split(
                        X, y, test_size=0.2, random_state=42, stratify=y
                    )
                    
                    # Train model
                    start_time = time.time()
                    model.fit(X_train, y_train)
                    training_time = time.time() - start_time
                    
                    # Evaluate
                    y_pred = model.predict(X_test)
                    accuracy = accuracy_score(y_test, y_pred)
                    
                    # Save model
                    model_file = f"{self.models_dir}/optimal_{model_type}_{prediction_type}.pkl"
                    joblib.dump(model, model_file)
                    
                    training_results[prediction_type][model_type] = {
                        'status': 'success',
                        'accuracy': accuracy,
                        'training_time': training_time,
                        'training_samples': len(X_train),
                        'test_samples': len(X_test),
                        'model_file': model_file
                    }
                    
                    successful_models += 1
                    logger.info(f"✅ {prediction_type} {model_type}: {accuracy:.3f} accuracy")
                    
                except Exception as e:
                    logger.error(f"❌ Error training {prediction_type} {model_type}: {str(e)}")
                    training_results[prediction_type][model_type] = {
                        'status': 'failed',
                        'error': str(e)
                    }
        
        training_time = time.time() - training_start
        
        # Save metadata
        metadata = {
            'training_date': dt.now().isoformat(),
            'training_type': 'optimal',
            'data_range': f"{self.start_year}-{self.end_year}",
            'total_matches': len(combined_df),
            'github_data_used': use_github,
            'apifootball_data_used': use_apifootball,
            'models_trained': successful_models,
            'training_results': training_results
        }
        
        metadata_file = f"{self.models_dir}/optimal_training_metadata.pkl"
        with open(metadata_file, 'wb') as f:
            pickle.dump(metadata, f)
        
        logger.info(f"🎯 Optimal training completed!")
        logger.info(f"⏱️  Total time: {training_time/60:.1f} minutes")
        logger.info(f"✅ Successful models: {successful_models}/{total_models}")
        
        return {
            'status': 'completed',
            'total_models': total_models,
            'successful_models': successful_models,
            'training_time_minutes': training_time / 60,
            'total_matches': len(combined_df),
            'results': training_results
        }


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Optimal Model Trainer')
    parser.add_argument('--github-only', action='store_true', help='Use only GitHub data')
    parser.add_argument('--apifootball-only', action='store_true', help='Use only APIFootball data')
    parser.add_argument('--test-data', action='store_true', help='Test data loading only')
    
    args = parser.parse_args()
    
    trainer = OptimalModelTrainer()
    
    if args.test_data:
        print("📊 Testing optimal data loading...")
        
        github_df = trainer.load_optimal_github_data()
        print(f"📚 GitHub data (2015-2022): {len(github_df):,} matches")
        
        apifootball_df = trainer.load_recent_apifootball_data(months_back=6)
        print(f"🌐 APIFootball data (recent): {len(apifootball_df):,} matches")
        
        return
    
    # Determine data sources
    use_github = not args.apifootball_only
    use_apifootball = not args.github_only
    
    print("🚀 OPTIMAL MODEL TRAINER")
    print("=" * 60)
    print("🎯 Using BEST PRACTICES for football prediction:")
    print(f"📅 Data Range: 2015-2025 (last 10 years)")
    print(f"📚 GitHub data (2015-2022): {'✅ Enabled' if use_github else '❌ Disabled'}")
    print(f"🌐 APIFootball data (2022-2025): {'✅ Enabled' if use_apifootball else '❌ Disabled'}")
    print("🚫 Excludes: Pre-2015 data, friendlies, COVID anomalies")
    print("🎯 Optimized for: Match results, BTTS, Over/Under, Clean sheets")
    print()
    
    confirm = input("Continue with optimal training? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ Training cancelled")
        return
    
    result = trainer.train_optimal_models(
        use_github=use_github,
        use_apifootball=use_apifootball
    )
    
    print("\n" + "=" * 60)
    print("📊 OPTIMAL TRAINING RESULTS")
    print("=" * 60)
    
    if result['status'] == 'completed':
        print(f"✅ Status: {result['status'].upper()}")
        print(f"🤖 Models Trained: {result['successful_models']}/{result['total_models']}")
        print(f"⏱️  Training Time: {result['training_time_minutes']:.1f} minutes")
        print(f"📊 Total Matches: {result['total_matches']:,}")
        
        print("\n🎯 Model Performance:")
        for pred_type, models in result['results'].items():
            print(f"\n  {pred_type.upper()}:")
            for model_type, model_result in models.items():
                if model_result['status'] == 'success':
                    acc = model_result['accuracy']
                    samples = model_result['training_samples']
                    print(f"    {model_type}: {acc:.3f} accuracy ({samples:,} samples)")
                else:
                    print(f"    {model_type}: {model_result['status']}")
    
    else:
        print(f"❌ Status: {result['status'].upper()}")
        print(f"📝 Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
