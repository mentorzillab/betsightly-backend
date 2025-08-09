#!/usr/bin/env python3
"""
Comprehensive Model Trainer
===========================

This script trains all ML models using extensive historical data from 2010-2025.
Models are saved and only retrained when necessary.

Features:
- Fetches historical data from 2010 to present
- Trains multiple model types: XGBoost, LightGBM, Neural Networks, Random Forest
- Implements model persistence and versioning
- Only retrains when models are missing or data is updated
- Comprehensive feature engineering
"""

import os
import sys
import json
import pickle
import logging
import numpy as np
import pandas as pd
from datetime import datetime as dt, timedelta
from typing import Dict, List, Any, Tuple
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
    from sklearn.metrics import accuracy_score, classification_report
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

class ComprehensiveModelTrainer:
    """Comprehensive ML model trainer with historical data."""
    
    def __init__(self):
        """Initialize the trainer."""
        self.api_key = settings.APIFOOTBALL_API_KEY
        self.base_url = "https://apiv3.apifootball.com"
        self.models_dir = "models"
        self.data_dir = "data"
        self.model_registry_file = f"{self.models_dir}/model_registry.pkl"
        
        # Ensure directories exist
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Model configurations
        self.model_types = {
            'xgboost': {
                'match_result': xgb.XGBClassifier(random_state=42),
                'btts': xgb.XGBClassifier(random_state=42),
                'over_1_5': xgb.XGBClassifier(random_state=42),
                'over_2_5': xgb.XGBClassifier(random_state=42),
                'over_3_5': xgb.XGBClassifier(random_state=42),
                'clean_sheet_home': xgb.XGBClassifier(random_state=42),
                'clean_sheet_away': xgb.XGBClassifier(random_state=42),
                'win_to_nil_home': xgb.XGBClassifier(random_state=42),
                'win_to_nil_away': xgb.XGBClassifier(random_state=42)
            },
            'lightgbm': {
                'match_result': lgb.LGBMClassifier(random_state=42, verbose=-1),
                'btts': lgb.LGBMClassifier(random_state=42, verbose=-1),
                'over_2_5': lgb.LGBMClassifier(random_state=42, verbose=-1),
                'over_3_5': lgb.LGBMClassifier(random_state=42, verbose=-1),
                'clean_sheet_home': lgb.LGBMClassifier(random_state=42, verbose=-1),
                'clean_sheet_away': lgb.LGBMClassifier(random_state=42, verbose=-1)
            },
            'neural_network': {
                'match_result': MLPClassifier(hidden_layer_sizes=(100, 50), random_state=42, max_iter=500),
                'btts': MLPClassifier(hidden_layer_sizes=(100, 50), random_state=42, max_iter=500),
                'over_2_5': MLPClassifier(hidden_layer_sizes=(100, 50), random_state=42, max_iter=500)
            },
            'random_forest': {
                'match_result': RandomForestClassifier(n_estimators=100, random_state=42),
                'btts': RandomForestClassifier(n_estimators=100, random_state=42),
                'over_2_5': RandomForestClassifier(n_estimators=100, random_state=42)
            }
        }
        
        self.trained_models = {}
        self.encoders = {}
        self.scalers = {}
        
    def check_existing_models(self) -> Dict[str, Any]:
        """Check which models already exist and their metadata."""
        logger.info("🔍 Checking existing models...")
        
        existing_models = {}
        model_registry = {}
        
        # Load model registry if exists
        if os.path.exists(self.model_registry_file):
            try:
                with open(self.model_registry_file, 'rb') as f:
                    model_registry = pickle.load(f)
            except Exception as e:
                logger.warning(f"Could not load model registry: {e}")
        
        # Check for existing model files
        for model_type in self.model_types.keys():
            existing_models[model_type] = {}
            
            for prediction_type in self.model_types[model_type].keys():
                model_file = f"{self.models_dir}/{model_type}_{prediction_type}.pkl"
                
                if os.path.exists(model_file):
                    try:
                        # Get file modification time
                        mod_time = os.path.getmtime(model_file)
                        mod_date = dt.fromtimestamp(mod_time)
                        
                        existing_models[model_type][prediction_type] = {
                            'file': model_file,
                            'modified': mod_date,
                            'size_kb': os.path.getsize(model_file) / 1024
                        }
                    except Exception as e:
                        logger.warning(f"Error checking {model_file}: {e}")
        
        return existing_models, model_registry
    
    def fetch_historical_data(self, start_year: int = 2010, end_year: int = None) -> pd.DataFrame:
        """Fetch comprehensive historical data from APIFootball."""
        if end_year is None:
            end_year = dt.now().year
        
        logger.info(f"📊 Fetching historical data from {start_year} to {end_year}...")
        
        # Check if cached data exists
        cache_file = f"{self.data_dir}/historical_data_{start_year}_{end_year}.pkl"
        
        if os.path.exists(cache_file):
            cache_age = dt.now() - dt.fromtimestamp(os.path.getmtime(cache_file))
            if cache_age.days < 7:  # Use cache if less than 7 days old
                logger.info("📁 Loading cached historical data...")
                return pd.read_pickle(cache_file)
        
        all_matches = []
        total_requests = 0
        
        # Fetch data year by year to manage API limits
        for year in range(start_year, end_year + 1):
            logger.info(f"📅 Fetching data for {year}...")
            
            # Fetch data in 3-month chunks to avoid timeouts
            for quarter in range(4):
                start_month = quarter * 3 + 1
                end_month = min(start_month + 2, 12)
                
                from_date = f"{year}-{start_month:02d}-01"
                
                # Calculate end date
                if end_month == 12:
                    to_date = f"{year}-12-31"
                else:
                    to_date = f"{year}-{end_month:02d}-{[31,28,31,30,31,30,31,31,30,31,30,31][end_month-1]:02d}"
                
                try:
                    url = f"{self.base_url}/"
                    params = {
                        'action': 'get_events',
                        'from': from_date,
                        'to': to_date,
                        'APIkey': self.api_key
                    }
                    
                    response = requests.get(url, params=params, timeout=30)
                    total_requests += 1
                    
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
                        logger.info(f"  ✅ {from_date} to {to_date}: {len(finished_matches)} finished matches")
                        
                    else:
                        logger.warning(f"  ⚠️  API error for {from_date}: {response.status_code}")
                    
                    # Rate limiting
                    time.sleep(0.2)
                    
                except Exception as e:
                    logger.error(f"  ❌ Error fetching {from_date}: {str(e)}")
                    continue
        
        logger.info(f"📈 Total historical matches collected: {len(all_matches)}")
        logger.info(f"🌐 Total API requests made: {total_requests}")
        
        # Convert to DataFrame
        df = pd.DataFrame(all_matches)
        
        # Cache the data
        df.to_pickle(cache_file)
        logger.info(f"💾 Cached data to {cache_file}")
        
        return df

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer features from raw match data."""
        logger.info("🔧 Engineering features...")

        # Convert scores to integers
        df['home_score'] = pd.to_numeric(df['match_hometeam_score'], errors='coerce')
        df['away_score'] = pd.to_numeric(df['match_awayteam_score'], errors='coerce')

        # Remove rows with invalid scores
        df = df.dropna(subset=['home_score', 'away_score'])

        # Basic match features
        df['total_goals'] = df['home_score'] + df['away_score']
        df['goal_difference'] = df['home_score'] - df['away_score']

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

        # League encoding
        if 'league_name' in df.columns:
            le_league = LabelEncoder()
            df['league_encoded'] = le_league.fit_transform(df['league_name'].fillna('Unknown'))
            self.encoders['league'] = le_league

        # Team encoding
        if 'match_hometeam_name' in df.columns and 'match_awayteam_name' in df.columns:
            # Combine all team names for consistent encoding
            all_teams = pd.concat([df['match_hometeam_name'], df['match_awayteam_name']]).unique()
            le_teams = LabelEncoder()
            le_teams.fit(all_teams)

            df['home_team_encoded'] = le_teams.transform(df['match_hometeam_name'])
            df['away_team_encoded'] = le_teams.transform(df['match_awayteam_name'])
            self.encoders['teams'] = le_teams

        # Date features
        if 'match_date' in df.columns:
            df['match_date'] = pd.to_datetime(df['match_date'], errors='coerce')
            df['month'] = df['match_date'].dt.month
            df['day_of_week'] = df['match_date'].dt.dayofweek
            df['year'] = df['match_date'].dt.year

        # Select feature columns
        feature_columns = [
            'league_encoded', 'home_team_encoded', 'away_team_encoded',
            'month', 'day_of_week', 'year'
        ]

        # Add any additional numeric features
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        additional_features = [col for col in numeric_columns if col not in feature_columns and
                             not col.startswith(('home_score', 'away_score', 'total_goals', 'goal_difference'))]

        feature_columns.extend(additional_features[:10])  # Limit additional features

        # Keep only available columns
        feature_columns = [col for col in feature_columns if col in df.columns]

        logger.info(f"✅ Engineered {len(feature_columns)} features")
        return df, feature_columns

    def train_model_type(self, df: pd.DataFrame, feature_columns: List[str],
                        model_type: str, prediction_type: str) -> Dict[str, Any]:
        """Train a specific model type for a specific prediction."""
        logger.info(f"🤖 Training {model_type} model for {prediction_type}...")

        # Prepare data
        X = df[feature_columns].fillna(0)
        y = df[prediction_type]

        # Remove any remaining NaN values
        mask = ~(X.isnull().any(axis=1) | y.isnull())
        X = X[mask]
        y = y[mask]

        if len(X) == 0:
            logger.error(f"No valid data for {model_type} {prediction_type}")
            return {'status': 'failed', 'error': 'No valid data'}

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
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

        # Get model
        model = self.model_types[model_type][prediction_type]

        # Train model
        try:
            model.fit(X_train_scaled, y_train)

            # Evaluate
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)

            # Save model
            model_file = f"{self.models_dir}/{model_type}_{prediction_type}.pkl"
            joblib.dump(model, model_file)

            # Save scaler if used
            if model_type == 'neural_network':
                scaler_file = f"{self.models_dir}/{model_type}_{prediction_type}_scaler.pkl"
                joblib.dump(self.scalers[f"{model_type}_{prediction_type}"], scaler_file)

            logger.info(f"✅ {model_type} {prediction_type}: {accuracy:.3f} accuracy")

            return {
                'status': 'success',
                'accuracy': accuracy,
                'model_file': model_file,
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }

        except Exception as e:
            logger.error(f"❌ Error training {model_type} {prediction_type}: {str(e)}")
            return {'status': 'failed', 'error': str(e)}

    def train_all_models(self, force_retrain: bool = False) -> Dict[str, Any]:
        """Train all models with comprehensive historical data."""
        logger.info("🚀 Starting comprehensive model training...")

        # Check existing models
        existing_models, model_registry = self.check_existing_models()

        if not force_retrain:
            total_existing = sum(len(models) for models in existing_models.values())
            total_possible = sum(len(models) for models in self.model_types.values())

            if total_existing >= total_possible * 0.8:  # 80% of models exist
                logger.info(f"✅ {total_existing}/{total_possible} models already exist")
                logger.info("Use --force-retrain to retrain all models")
                return {
                    'status': 'skipped',
                    'reason': 'Models already exist',
                    'existing_models': total_existing,
                    'total_models': total_possible
                }

        # Fetch historical data
        start_time = dt.now()
        df = self.fetch_historical_data(start_year=2010)

        if df.empty:
            logger.error("❌ No historical data available")
            return {'status': 'failed', 'error': 'No historical data'}

        logger.info(f"📊 Loaded {len(df)} historical matches")

        # Engineer features
        df_processed, feature_columns = self.engineer_features(df)

        # Save feature columns for future use
        feature_file = f"{self.models_dir}/feature_columns.pkl"
        with open(feature_file, 'wb') as f:
            pickle.dump(feature_columns, f)

        # Save encoders
        encoders_file = f"{self.models_dir}/encoders.pkl"
        with open(encoders_file, 'wb') as f:
            pickle.dump(self.encoders, f)

        # Train all models
        training_results = {}
        total_models = 0
        successful_models = 0

        for model_type, prediction_types in self.model_types.items():
            training_results[model_type] = {}

            for prediction_type in prediction_types.keys():
                total_models += 1

                # Check if we should skip this model
                if (not force_retrain and
                    model_type in existing_models and
                    prediction_type in existing_models[model_type]):

                    logger.info(f"⏭️  Skipping {model_type} {prediction_type} (already exists)")
                    training_results[model_type][prediction_type] = {
                        'status': 'skipped',
                        'reason': 'Already exists'
                    }
                    successful_models += 1
                    continue

                # Train the model
                result = self.train_model_type(df_processed, feature_columns, model_type, prediction_type)
                training_results[model_type][prediction_type] = result

                if result['status'] == 'success':
                    successful_models += 1

        # Update model registry
        model_registry.update({
            'last_training': dt.now().isoformat(),
            'data_period': f"2010-{dt.now().year}",
            'total_matches': len(df_processed),
            'feature_columns': feature_columns,
            'training_results': training_results
        })

        # Save model registry
        with open(self.model_registry_file, 'wb') as f:
            pickle.dump(model_registry, f)

        training_time = (dt.now() - start_time).total_seconds()

        logger.info(f"✅ Training completed in {training_time:.1f} seconds")
        logger.info(f"📊 Successfully trained: {successful_models}/{total_models} models")

        return {
            'status': 'completed',
            'total_models': total_models,
            'successful_models': successful_models,
            'training_time_seconds': training_time,
            'data_matches': len(df_processed),
            'feature_count': len(feature_columns),
            'results': training_results
        }

    def get_model_summary(self) -> Dict[str, Any]:
        """Get summary of all available models."""
        existing_models, model_registry = self.check_existing_models()

        summary = {
            'model_types': list(self.model_types.keys()),
            'prediction_types': {},
            'total_models_possible': 0,
            'total_models_available': 0,
            'model_details': existing_models,
            'last_training': model_registry.get('last_training', 'Never'),
            'data_period': model_registry.get('data_period', 'Unknown')
        }

        # Count models by prediction type
        for model_type, predictions in self.model_types.items():
            for pred_type in predictions.keys():
                if pred_type not in summary['prediction_types']:
                    summary['prediction_types'][pred_type] = {
                        'available_models': [],
                        'total_possible': 0
                    }

                summary['prediction_types'][pred_type]['total_possible'] += 1
                summary['total_models_possible'] += 1

                if (model_type in existing_models and
                    pred_type in existing_models[model_type]):
                    summary['prediction_types'][pred_type]['available_models'].append(model_type)
                    summary['total_models_available'] += 1

        return summary


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description='Comprehensive Model Trainer')
    parser.add_argument('--force-retrain', action='store_true',
                       help='Force retrain all models even if they exist')
    parser.add_argument('--summary', action='store_true',
                       help='Show model summary only')
    parser.add_argument('--start-year', type=int, default=2010,
                       help='Start year for historical data (default: 2010)')

    args = parser.parse_args()

    trainer = ComprehensiveModelTrainer()

    if args.summary:
        print("📊 MODEL SUMMARY")
        print("=" * 50)
        summary = trainer.get_model_summary()

        print(f"🤖 Model Types: {', '.join(summary['model_types'])}")
        print(f"📈 Total Models: {summary['total_models_available']}/{summary['total_models_possible']}")
        print(f"📅 Last Training: {summary['last_training']}")
        print(f"📊 Data Period: {summary['data_period']}")
        print()

        print("🎯 PREDICTION TYPES:")
        for pred_type, details in summary['prediction_types'].items():
            available = len(details['available_models'])
            total = details['total_possible']
            models = ', '.join(details['available_models']) if details['available_models'] else 'None'
            print(f"  {pred_type}: {available}/{total} models ({models})")

        return

    # Train models
    print("🚀 COMPREHENSIVE MODEL TRAINER")
    print("=" * 50)
    print("This will train ML models using historical data from 2010-2025")
    print("Models: XGBoost, LightGBM, Neural Networks, Random Forest")
    print("Predictions: Match Result, BTTS, Over/Under, Clean Sheets, Win to Nil")
    print()

    result = trainer.train_all_models(force_retrain=args.force_retrain)

    print("\n" + "=" * 50)
    print("📊 TRAINING RESULTS")
    print("=" * 50)

    if result['status'] == 'completed':
        print(f"✅ Status: {result['status'].upper()}")
        print(f"🤖 Models Trained: {result['successful_models']}/{result['total_models']}")
        print(f"⏱️  Training Time: {result['training_time_seconds']:.1f} seconds")
        print(f"📊 Training Data: {result['data_matches']:,} matches")
        print(f"🔧 Features: {result['feature_count']} features")

        print("\n🎯 Model Performance:")
        for model_type, predictions in result['results'].items():
            print(f"\n  {model_type.upper()}:")
            for pred_type, pred_result in predictions.items():
                if pred_result['status'] == 'success':
                    acc = pred_result['accuracy']
                    samples = pred_result['training_samples']
                    print(f"    {pred_type}: {acc:.3f} accuracy ({samples:,} samples)")
                else:
                    status = pred_result.get('status', 'unknown')
                    print(f"    {pred_type}: {status}")

    elif result['status'] == 'skipped':
        print(f"⏭️  Status: {result['status'].upper()}")
        print(f"📝 Reason: {result['reason']}")
        print(f"🤖 Existing Models: {result['existing_models']}/{result['total_models']}")
        print("\n💡 Use --force-retrain to retrain all models")

    else:
        print(f"❌ Status: {result['status'].upper()}")
        print(f"📝 Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
