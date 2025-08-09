#!/usr/bin/env python3
"""
Extensive Model Trainer
=======================

This script trains ML models with comprehensive historical data from 2010-2025.
Features robust error handling, smart caching, and progressive data collection.

Key Features:
- Fetches historical data from 2010-2025 progressively
- Implements smart caching to avoid repeated API calls
- Robust error handling and retry logic
- Progressive training with data validation
- Comprehensive model evaluation and saving
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
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
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

class ExtensiveModelTrainer:
    """Extensive model trainer with 2010-2025 historical data."""
    
    def __init__(self):
        """Initialize the trainer."""
        self.api_key = settings.APIFOOTBALL_API_KEY
        self.base_url = "https://apiv3.apifootball.com"
        self.models_dir = "models"
        self.data_dir = "data/historical"
        self.cache_dir = "cache/training"
        
        # Ensure directories exist
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Rate limiting and retry settings
        self.request_delay = 3.0  # Increased delay
        self.max_retries = 3
        self.retry_delay = 5.0
        self.last_request_time = 0
        
        # Training configuration
        self.models_config = {
            'xgboost': {
                'match_result': xgb.XGBClassifier(random_state=42, n_estimators=200),
                'btts': xgb.XGBClassifier(random_state=42, n_estimators=200),
                'over_1_5': xgb.XGBClassifier(random_state=42, n_estimators=200),
                'over_2_5': xgb.XGBClassifier(random_state=42, n_estimators=200),
                'over_3_5': xgb.XGBClassifier(random_state=42, n_estimators=200),
                'clean_sheet_home': xgb.XGBClassifier(random_state=42, n_estimators=200),
                'clean_sheet_away': xgb.XGBClassifier(random_state=42, n_estimators=200),
                'win_to_nil_home': xgb.XGBClassifier(random_state=42, n_estimators=200),
                'win_to_nil_away': xgb.XGBClassifier(random_state=42, n_estimators=200)
            },
            'lightgbm': {
                'match_result': lgb.LGBMClassifier(random_state=42, n_estimators=200, verbose=-1),
                'btts': lgb.LGBMClassifier(random_state=42, n_estimators=200, verbose=-1),
                'over_2_5': lgb.LGBMClassifier(random_state=42, n_estimators=200, verbose=-1),
                'over_3_5': lgb.LGBMClassifier(random_state=42, n_estimators=200, verbose=-1),
                'clean_sheet_home': lgb.LGBMClassifier(random_state=42, n_estimators=200, verbose=-1),
                'clean_sheet_away': lgb.LGBMClassifier(random_state=42, n_estimators=200, verbose=-1)
            },
            'neural_network': {
                'match_result': MLPClassifier(hidden_layer_sizes=(150, 100, 50), random_state=42, max_iter=1000),
                'btts': MLPClassifier(hidden_layer_sizes=(150, 100, 50), random_state=42, max_iter=1000),
                'over_2_5': MLPClassifier(hidden_layer_sizes=(150, 100, 50), random_state=42, max_iter=1000)
            },
            'random_forest': {
                'match_result': RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1),
                'btts': RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1),
                'over_2_5': RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
            }
        }
        
        self.encoders = {}
        self.scalers = {}
        
    def rate_limit_request(self):
        """Implement strict rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            logger.info(f"⏳ Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def fetch_year_data_with_retry(self, year: int) -> List[Dict]:
        """Fetch data for a specific year with retry logic."""
        logger.info(f"📅 Fetching data for {year}...")
        
        # Check cache first
        cache_file = os.path.join(self.cache_dir, f"year_{year}.pkl")
        if os.path.exists(cache_file):
            logger.info(f"📁 Loading cached data for {year}")
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        
        all_matches = []
        
        # Fetch data in quarterly chunks to avoid timeouts
        quarters = [
            (f"{year}-01-01", f"{year}-03-31", "Q1"),
            (f"{year}-04-01", f"{year}-06-30", "Q2"),
            (f"{year}-07-01", f"{year}-09-30", "Q3"),
            (f"{year}-10-01", f"{year}-12-31", "Q4")
        ]
        
        for from_date, to_date, quarter in quarters:
            logger.info(f"  📊 Fetching {year} {quarter}: {from_date} to {to_date}")
            
            for attempt in range(self.max_retries):
                try:
                    self.rate_limit_request()
                    
                    url = f"{self.base_url}/"
                    params = {
                        'action': 'get_events',
                        'from': from_date,
                        'to': to_date,
                        'APIkey': self.api_key
                    }
                    
                    response = requests.get(url, params=params, timeout=45)
                    
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
                        
                        all_matches.extend(finished_matches)
                        logger.info(f"    ✅ {quarter}: {len(finished_matches)} finished matches")
                        break  # Success, exit retry loop
                        
                    else:
                        logger.warning(f"    ⚠️  API error {response.status_code} for {year} {quarter}")
                        if attempt < self.max_retries - 1:
                            logger.info(f"    🔄 Retrying in {self.retry_delay}s...")
                            time.sleep(self.retry_delay)
                        
                except Exception as e:
                    logger.error(f"    ❌ Error fetching {year} {quarter}: {str(e)}")
                    if attempt < self.max_retries - 1:
                        logger.info(f"    🔄 Retrying in {self.retry_delay}s...")
                        time.sleep(self.retry_delay)
                    else:
                        logger.error(f"    💥 Failed after {self.max_retries} attempts")
        
        # Cache the results
        if all_matches:
            with open(cache_file, 'wb') as f:
                pickle.dump(all_matches, f)
            logger.info(f"💾 Cached {len(all_matches)} matches for {year}")
        
        logger.info(f"📈 Total matches for {year}: {len(all_matches)}")
        return all_matches
    
    def collect_historical_data(self, start_year: int = 2010, end_year: int = None) -> pd.DataFrame:
        """Collect comprehensive historical data from start_year to end_year."""
        if end_year is None:
            end_year = dt.now().year
        
        logger.info(f"🌍 Collecting historical data from {start_year} to {end_year}")
        
        # Check if we have a complete dataset cached
        complete_cache_file = os.path.join(self.data_dir, f"complete_{start_year}_{end_year}.pkl")
        
        if os.path.exists(complete_cache_file):
            cache_age = dt.now() - dt.fromtimestamp(os.path.getmtime(complete_cache_file))
            if cache_age.days < 30:  # Use cache if less than 30 days old
                logger.info(f"📁 Loading complete cached dataset ({start_year}-{end_year})")
                return pd.read_pickle(complete_cache_file)
        
        all_historical_data = []
        years_processed = []
        total_api_calls = 0
        
        # Process years in reverse order (most recent first)
        for year in range(end_year, start_year - 1, -1):
            try:
                year_data = self.fetch_year_data_with_retry(year)
                
                if year_data:
                    all_historical_data.extend(year_data)
                    years_processed.append(year)
                    total_api_calls += 4  # 4 quarters per year
                    
                    logger.info(f"✅ {year}: {len(year_data)} matches collected")
                else:
                    logger.warning(f"⚠️  {year}: No data collected")
                
                # Progress update every 5 years
                if len(years_processed) % 5 == 0:
                    total_matches = len(all_historical_data)
                    logger.info(f"📊 Progress: {len(years_processed)} years, {total_matches:,} total matches")
                
            except Exception as e:
                logger.error(f"❌ Failed to process year {year}: {str(e)}")
                continue
        
        logger.info(f"🎯 Data collection complete!")
        logger.info(f"📊 Years processed: {len(years_processed)}")
        logger.info(f"📈 Total matches: {len(all_historical_data):,}")
        logger.info(f"🌐 Total API calls: {total_api_calls}")
        
        # Convert to DataFrame
        df = pd.DataFrame(all_historical_data)
        
        # Cache the complete dataset
        df.to_pickle(complete_cache_file)
        logger.info(f"💾 Cached complete dataset to {complete_cache_file}")
        
        return df

    def engineer_comprehensive_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Engineer comprehensive features from historical data."""
        logger.info("🔧 Engineering comprehensive features...")

        # Convert scores to numeric
        df['home_score'] = pd.to_numeric(df['match_hometeam_score'], errors='coerce')
        df['away_score'] = pd.to_numeric(df['match_awayteam_score'], errors='coerce')

        # Remove invalid data
        df = df.dropna(subset=['home_score', 'away_score'])
        df = df[df['home_score'] >= 0]
        df = df[df['away_score'] >= 0]

        logger.info(f"📊 Valid matches after cleaning: {len(df):,}")

        # Basic match statistics
        df['total_goals'] = df['home_score'] + df['away_score']
        df['goal_difference'] = df['home_score'] - df['away_score']
        df['home_advantage'] = (df['home_score'] > df['away_score']).astype(int)

        # Target variables
        df['match_result'] = df.apply(lambda x:
            'H' if x['home_score'] > x['away_score'] else
            'A' if x['home_score'] < x['away_score'] else 'D', axis=1)

        df['btts'] = ((df['home_score'] > 0) & (df['away_score'] > 0)).astype(int)
        df['over_1_5'] = (df['total_goals'] > 1.5).astype(int)
        df['over_2_5'] = (df['total_goals'] > 2.5).astype(int)
        df['over_3_5'] = (df['total_goals'] > 3.5).astype(int)
        df['clean_sheet_home'] = (df['away_score'] == 0).astype(int)
        df['clean_sheet_away'] = (df['home_score'] == 0).astype(int)
        df['win_to_nil_home'] = ((df['home_score'] > df['away_score']) & (df['away_score'] == 0)).astype(int)
        df['win_to_nil_away'] = ((df['away_score'] > df['home_score']) & (df['home_score'] == 0)).astype(int)

        # Encode categorical variables
        logger.info("🏷️  Encoding categorical variables...")

        # League encoding
        if 'league_name' in df.columns:
            le_league = LabelEncoder()
            df['league_encoded'] = le_league.fit_transform(df['league_name'].fillna('Unknown'))
            self.encoders['league'] = le_league

        # Country encoding
        if 'country_name' in df.columns:
            le_country = LabelEncoder()
            df['country_encoded'] = le_country.fit_transform(df['country_name'].fillna('Unknown'))
            self.encoders['country'] = le_country

        # Team encoding
        if 'match_hometeam_name' in df.columns and 'match_awayteam_name' in df.columns:
            all_teams = pd.concat([df['match_hometeam_name'], df['match_awayteam_name']]).unique()
            le_teams = LabelEncoder()
            le_teams.fit(all_teams)

            df['home_team_encoded'] = le_teams.transform(df['match_hometeam_name'])
            df['away_team_encoded'] = le_teams.transform(df['match_awayteam_name'])
            self.encoders['teams'] = le_teams

        # Date features
        if 'match_date' in df.columns:
            df['match_date'] = pd.to_datetime(df['match_date'], errors='coerce')
            df['year'] = df['match_date'].dt.year
            df['month'] = df['match_date'].dt.month
            df['day_of_week'] = df['match_date'].dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

        # Time features
        if 'match_time' in df.columns:
            # Extract hour from match time
            df['match_hour'] = df['match_time'].str.extract(r'(\d+)').astype(float)
            df['is_evening'] = (df['match_hour'] >= 18).astype(int)

        # Select feature columns
        feature_columns = []

        # Categorical features
        categorical_features = ['league_encoded', 'country_encoded', 'home_team_encoded', 'away_team_encoded']
        feature_columns.extend([col for col in categorical_features if col in df.columns])

        # Temporal features
        temporal_features = ['year', 'month', 'day_of_week', 'is_weekend', 'match_hour', 'is_evening']
        feature_columns.extend([col for col in temporal_features if col in df.columns])

        # Derived features
        derived_features = ['home_advantage']
        feature_columns.extend([col for col in derived_features if col in df.columns])

        logger.info(f"✅ Engineered {len(feature_columns)} features")
        logger.info(f"📊 Feature categories: {len([c for c in categorical_features if c in df.columns])} categorical, "
                   f"{len([c for c in temporal_features if c in df.columns])} temporal, "
                   f"{len([c for c in derived_features if c in df.columns])} derived")

        return df, feature_columns

    def train_single_model(self, df: pd.DataFrame, feature_columns: List[str],
                          model_type: str, prediction_type: str) -> Dict[str, Any]:
        """Train a single model with comprehensive evaluation."""
        logger.info(f"🤖 Training {model_type} model for {prediction_type}...")

        # Prepare data
        X = df[feature_columns].fillna(0)
        y = df[prediction_type]

        # Remove any remaining NaN values
        mask = ~(X.isnull().any(axis=1) | y.isnull())
        X = X[mask]
        y = y[mask]

        if len(X) < 1000:
            logger.warning(f"⚠️  Insufficient data for {model_type} {prediction_type}: {len(X)} samples")
            return {'status': 'insufficient_data', 'samples': len(X)}

        # Split data with stratification
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
        except ValueError:
            # Fallback without stratification if classes are imbalanced
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

        # Scale features for neural networks
        if model_type == 'neural_network':
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            self.scalers[f"{model_type}_{prediction_type}"] = scaler
        else:
            X_train_scaled = X_train
            X_test_scaled = X_test

        # Get and train model
        try:
            model = self.models_config[model_type][prediction_type]

            # Train with progress logging
            start_time = time.time()
            model.fit(X_train_scaled, y_train)
            training_time = time.time() - start_time

            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)

            # Additional metrics for classification
            if hasattr(model, 'predict_proba'):
                y_proba = model.predict_proba(X_test_scaled)
                confidence_scores = np.max(y_proba, axis=1)
                avg_confidence = np.mean(confidence_scores)
            else:
                avg_confidence = None

            # Save model and associated files
            model_file = f"{self.models_dir}/{model_type}_{prediction_type}.pkl"
            joblib.dump(model, model_file)

            # Save scaler if used
            if model_type == 'neural_network':
                scaler_file = f"{self.models_dir}/{model_type}_{prediction_type}_scaler.pkl"
                joblib.dump(self.scalers[f"{model_type}_{prediction_type}"], scaler_file)

            logger.info(f"✅ {model_type} {prediction_type}: {accuracy:.3f} accuracy, {training_time:.1f}s training")

            return {
                'status': 'success',
                'accuracy': accuracy,
                'avg_confidence': avg_confidence,
                'training_time': training_time,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'model_file': model_file
            }

        except Exception as e:
            logger.error(f"❌ Error training {model_type} {prediction_type}: {str(e)}")
            return {'status': 'failed', 'error': str(e)}

    def train_all_models_extensively(self, start_year: int = 2010, force_retrain: bool = False) -> Dict[str, Any]:
        """Train all models with extensive historical data."""
        logger.info("🚀 Starting extensive model training with 2010-2025 data...")

        training_start = time.time()

        # Collect historical data
        logger.info("📊 Collecting comprehensive historical data...")
        df = self.collect_historical_data(start_year=start_year)

        if df.empty:
            logger.error("❌ No historical data collected")
            return {'status': 'failed', 'error': 'No historical data available'}

        logger.info(f"📈 Loaded {len(df):,} historical matches")

        # Engineer features
        df_processed, feature_columns = self.engineer_comprehensive_features(df)

        if df_processed.empty:
            logger.error("❌ No valid data after feature engineering")
            return {'status': 'failed', 'error': 'No valid data after processing'}

        logger.info(f"✅ Processed {len(df_processed):,} matches with {len(feature_columns)} features")

        # Save feature columns and encoders
        feature_file = f"{self.models_dir}/feature_columns.pkl"
        with open(feature_file, 'wb') as f:
            pickle.dump(feature_columns, f)

        encoders_file = f"{self.models_dir}/encoders.pkl"
        with open(encoders_file, 'wb') as f:
            pickle.dump(self.encoders, f)

        # Train all models
        training_results = {}
        total_models = 0
        successful_models = 0
        failed_models = 0

        for model_type, prediction_configs in self.models_config.items():
            training_results[model_type] = {}
            logger.info(f"🔄 Training {model_type} models...")

            for prediction_type in prediction_configs.keys():
                total_models += 1

                # Check if target variable exists
                if prediction_type not in df_processed.columns:
                    logger.warning(f"⚠️  Target variable {prediction_type} not found, skipping")
                    training_results[model_type][prediction_type] = {
                        'status': 'skipped',
                        'reason': 'Target variable not found'
                    }
                    continue

                # Train the model
                result = self.train_single_model(df_processed, feature_columns, model_type, prediction_type)
                training_results[model_type][prediction_type] = result

                if result['status'] == 'success':
                    successful_models += 1
                else:
                    failed_models += 1

        # Save training metadata
        training_metadata = {
            'training_date': dt.now().isoformat(),
            'data_period': f"{start_year}-{dt.now().year}",
            'total_matches': len(df_processed),
            'feature_count': len(feature_columns),
            'feature_columns': feature_columns,
            'models_trained': successful_models,
            'models_failed': failed_models,
            'training_results': training_results
        }

        metadata_file = f"{self.models_dir}/training_metadata.pkl"
        with open(metadata_file, 'wb') as f:
            pickle.dump(training_metadata, f)

        training_time = time.time() - training_start

        logger.info(f"🎯 Extensive training completed!")
        logger.info(f"⏱️  Total training time: {training_time/60:.1f} minutes")
        logger.info(f"✅ Successful models: {successful_models}/{total_models}")
        logger.info(f"❌ Failed models: {failed_models}/{total_models}")

        return {
            'status': 'completed',
            'total_models': total_models,
            'successful_models': successful_models,
            'failed_models': failed_models,
            'training_time_minutes': training_time / 60,
            'data_matches': len(df_processed),
            'feature_count': len(feature_columns),
            'data_period': f"{start_year}-{dt.now().year}",
            'results': training_results
        }

    def get_training_summary(self) -> Dict[str, Any]:
        """Get summary of training status and results."""
        metadata_file = f"{self.models_dir}/training_metadata.pkl"

        if not os.path.exists(metadata_file):
            return {'status': 'no_training_data', 'message': 'No training metadata found'}

        try:
            with open(metadata_file, 'rb') as f:
                metadata = pickle.load(f)

            # Count available model files
            available_models = 0
            for model_type, predictions in self.models_config.items():
                for prediction_type in predictions.keys():
                    model_file = f"{self.models_dir}/{model_type}_{prediction_type}.pkl"
                    if os.path.exists(model_file):
                        available_models += 1

            return {
                'status': 'available',
                'training_date': metadata.get('training_date'),
                'data_period': metadata.get('data_period'),
                'total_matches': metadata.get('total_matches'),
                'feature_count': metadata.get('feature_count'),
                'models_trained': metadata.get('models_trained'),
                'models_available': available_models,
                'training_results': metadata.get('training_results', {})
            }

        except Exception as e:
            logger.error(f"Error reading training metadata: {e}")
            return {'status': 'error', 'message': str(e)}


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description='Extensive Model Trainer')
    parser.add_argument('--start-year', type=int, default=2010,
                       help='Start year for historical data (default: 2010)')
    parser.add_argument('--force-retrain', action='store_true',
                       help='Force retrain all models')
    parser.add_argument('--summary', action='store_true',
                       help='Show training summary')
    parser.add_argument('--test-connection', action='store_true',
                       help='Test API connection only')

    args = parser.parse_args()

    trainer = ExtensiveModelTrainer()

    if args.summary:
        print("📊 EXTENSIVE TRAINING SUMMARY")
        print("=" * 50)
        summary = trainer.get_training_summary()

        if summary['status'] == 'available':
            print(f"📅 Training Date: {summary['training_date']}")
            print(f"📊 Data Period: {summary['data_period']}")
            print(f"🏈 Total Matches: {summary['total_matches']:,}")
            print(f"🔧 Features: {summary['feature_count']}")
            print(f"🤖 Models Trained: {summary['models_trained']}")
            print(f"📁 Models Available: {summary['models_available']}")

            print("\n🎯 Model Performance:")
            for model_type, predictions in summary['training_results'].items():
                print(f"\n  {model_type.upper()}:")
                for pred_type, result in predictions.items():
                    if result['status'] == 'success':
                        acc = result['accuracy']
                        samples = result['training_samples']
                        print(f"    {pred_type}: {acc:.3f} accuracy ({samples:,} samples)")
                    else:
                        print(f"    {pred_type}: {result['status']}")
        else:
            print(f"Status: {summary['status']}")
            print(f"Message: {summary.get('message', 'Unknown')}")

        return

    if args.test_connection:
        print("🌐 Testing API connection...")
        try:
            test_data = trainer.fetch_year_data_with_retry(2024)
            print(f"✅ Connection successful: {len(test_data)} matches from 2024")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
        return

    # Main training execution
    print("🚀 EXTENSIVE MODEL TRAINER")
    print("=" * 60)
    print(f"📊 Training with historical data from {args.start_year}-2025")
    print("🤖 Models: XGBoost, LightGBM, Neural Networks, Random Forest")
    print("🎯 Predictions: Match Result, BTTS, Over/Under, Clean Sheets, Win to Nil")
    print("⚠️  This will take 30-60 minutes and make many API calls")
    print()

    if not args.force_retrain:
        confirm = input("Continue? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Training cancelled")
            return

    result = trainer.train_all_models_extensively(start_year=args.start_year, force_retrain=args.force_retrain)

    print("\n" + "=" * 60)
    print("📊 EXTENSIVE TRAINING RESULTS")
    print("=" * 60)

    if result['status'] == 'completed':
        print(f"✅ Status: {result['status'].upper()}")
        print(f"🤖 Models Trained: {result['successful_models']}/{result['total_models']}")
        print(f"⏱️  Training Time: {result['training_time_minutes']:.1f} minutes")
        print(f"📊 Training Data: {result['data_matches']:,} matches")
        print(f"🔧 Features: {result['feature_count']} features")
        print(f"📅 Data Period: {result['data_period']}")

        if result['failed_models'] > 0:
            print(f"⚠️  Failed Models: {result['failed_models']}")

        print("\n🎯 Model Performance Summary:")
        for model_type, predictions in result['results'].items():
            successful = sum(1 for r in predictions.values() if r.get('status') == 'success')
            total = len(predictions)
            print(f"  {model_type.upper()}: {successful}/{total} models trained")

    else:
        print(f"❌ Status: {result['status'].upper()}")
        print(f"📝 Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
