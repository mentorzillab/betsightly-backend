#!/usr/bin/env python3
"""
Hybrid Model Trainer
===================

This script trains ML models using BOTH GitHub datasets and APIFootball.com data:
- GitHub datasets: Extensive historical data (2010-2020+)
- APIFootball.com: Recent real-world data (2022-2025)
- Combines both sources for comprehensive training
- Handles different data formats and merges them intelligently
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

class HybridModelTrainer:
    """Hybrid trainer using both GitHub and APIFootball data."""
    
    def __init__(self):
        """Initialize the hybrid trainer."""
        self.api_key = settings.APIFOOTBALL_API_KEY
        self.base_url = "https://apiv3.apifootball.com"
        self.models_dir = "models"
        self.data_dir = "data/hybrid"
        self.github_data_dir = "data/github"
        
        # Ensure directories exist
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.github_data_dir, exist_ok=True)
        
        # Rate limiting
        self.request_delay = 2.0
        self.last_request_time = 0
        
        # Model configurations
        self.models_config = {
            'xgboost': {
                'match_result': xgb.XGBClassifier(random_state=42, n_estimators=300),
                'btts': xgb.XGBClassifier(random_state=42, n_estimators=300),
                'over_1_5': xgb.XGBClassifier(random_state=42, n_estimators=300),
                'over_2_5': xgb.XGBClassifier(random_state=42, n_estimators=300),
                'over_3_5': xgb.XGBClassifier(random_state=42, n_estimators=300),
                'clean_sheet_home': xgb.XGBClassifier(random_state=42, n_estimators=300),
                'clean_sheet_away': xgb.XGBClassifier(random_state=42, n_estimators=300),
                'win_to_nil_home': xgb.XGBClassifier(random_state=42, n_estimators=300),
                'win_to_nil_away': xgb.XGBClassifier(random_state=42, n_estimators=300)
            },
            'lightgbm': {
                'match_result': lgb.LGBMClassifier(random_state=42, n_estimators=300, verbose=-1),
                'btts': lgb.LGBMClassifier(random_state=42, n_estimators=300, verbose=-1),
                'over_2_5': lgb.LGBMClassifier(random_state=42, n_estimators=300, verbose=-1),
                'over_3_5': lgb.LGBMClassifier(random_state=42, n_estimators=300, verbose=-1),
                'clean_sheet_home': lgb.LGBMClassifier(random_state=42, n_estimators=300, verbose=-1),
                'clean_sheet_away': lgb.LGBMClassifier(random_state=42, n_estimators=300, verbose=-1)
            },
            'neural_network': {
                'match_result': MLPClassifier(hidden_layer_sizes=(200, 100, 50), random_state=42, max_iter=1000),
                'btts': MLPClassifier(hidden_layer_sizes=(200, 100, 50), random_state=42, max_iter=1000),
                'over_2_5': MLPClassifier(hidden_layer_sizes=(200, 100, 50), random_state=42, max_iter=1000)
            },
            'random_forest': {
                'match_result': RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1),
                'btts': RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1),
                'over_2_5': RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1)
            }
        }
        
        self.encoders = {}
        self.scalers = {}
    
    def load_github_datasets(self) -> pd.DataFrame:
        """Load and combine GitHub football datasets."""
        logger.info("📊 Loading GitHub football datasets...")
        
        github_datasets = [
            {
                'url': 'https://raw.githubusercontent.com/jalapic/engsoccerdata/master/data-raw/england.csv',
                'name': 'England Historical',
                'leagues': ['Premier League', 'Championship', 'League One', 'League Two']
            },
            {
                'url': 'https://raw.githubusercontent.com/jalapic/engsoccerdata/master/data-raw/spain.csv',
                'name': 'Spain Historical',
                'leagues': ['La Liga', 'Segunda Division']
            },
            {
                'url': 'https://raw.githubusercontent.com/jalapic/engsoccerdata/master/data-raw/germany.csv',
                'name': 'Germany Historical',
                'leagues': ['Bundesliga', '2. Bundesliga']
            },
            {
                'url': 'https://raw.githubusercontent.com/jalapic/engsoccerdata/master/data-raw/italy.csv',
                'name': 'Italy Historical',
                'leagues': ['Serie A', 'Serie B']
            },
            {
                'url': 'https://raw.githubusercontent.com/jalapic/engsoccerdata/master/data-raw/france.csv',
                'name': 'France Historical',
                'leagues': ['Ligue 1', 'Ligue 2']
            }
        ]
        
        all_github_data = []
        
        for dataset in github_datasets:
            try:
                cache_file = os.path.join(self.github_data_dir, f"{dataset['name'].replace(' ', '_').lower()}.csv")
                
                # Try to load from cache first
                if os.path.exists(cache_file):
                    logger.info(f"📁 Loading cached {dataset['name']}")
                    df = pd.read_csv(cache_file)
                else:
                    logger.info(f"🌐 Downloading {dataset['name']} from GitHub...")
                    df = pd.read_csv(dataset['url'])
                    
                    # Cache the dataset
                    df.to_csv(cache_file, index=False)
                    logger.info(f"💾 Cached {dataset['name']} to {cache_file}")
                
                # Standardize column names
                df = self.standardize_github_data(df, dataset['name'])
                
                if not df.empty:
                    all_github_data.append(df)
                    logger.info(f"✅ {dataset['name']}: {len(df):,} matches loaded")
                
            except Exception as e:
                logger.error(f"❌ Failed to load {dataset['name']}: {str(e)}")
                continue
        
        if all_github_data:
            combined_df = pd.concat(all_github_data, ignore_index=True)
            logger.info(f"📈 Total GitHub data: {len(combined_df):,} matches")
            return combined_df
        else:
            logger.warning("⚠️  No GitHub data loaded")
            return pd.DataFrame()
    
    def standardize_github_data(self, df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
        """Standardize GitHub dataset format."""
        try:
            # Common column mappings for different GitHub datasets
            column_mappings = {
                'Date': 'match_date',
                'date': 'match_date',
                'Season': 'season',
                'season': 'season',
                'home': 'match_hometeam_name',
                'Home': 'match_hometeam_name',
                'HomeTeam': 'match_hometeam_name',
                'visitor': 'match_awayteam_name',
                'Visitor': 'match_awayteam_name',
                'AwayTeam': 'match_awayteam_name',
                'away': 'match_awayteam_name',
                'hgoal': 'match_hometeam_score',
                'vgoal': 'match_awayteam_score',
                'FTHG': 'match_hometeam_score',
                'FTAG': 'match_awayteam_score',
                'HomeGoals': 'match_hometeam_score',
                'AwayGoals': 'match_awayteam_score',
                'Division': 'league_name',
                'Div': 'league_name',
                'tier': 'league_tier'
            }
            
            # Rename columns
            df = df.rename(columns=column_mappings)
            
            # Add metadata
            df['data_source'] = 'github'
            df['dataset_name'] = dataset_name
            df['match_status'] = 'Finished'
            df['country_name'] = dataset_name.split()[0]
            
            # Ensure required columns exist
            required_columns = ['match_date', 'match_hometeam_name', 'match_awayteam_name', 
                              'match_hometeam_score', 'match_awayteam_score']
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.warning(f"⚠️  {dataset_name} missing columns: {missing_columns}")
                return pd.DataFrame()
            
            # Convert scores to numeric
            df['match_hometeam_score'] = pd.to_numeric(df['match_hometeam_score'], errors='coerce')
            df['match_awayteam_score'] = pd.to_numeric(df['match_awayteam_score'], errors='coerce')
            
            # Remove invalid data
            df = df.dropna(subset=['match_hometeam_score', 'match_awayteam_score'])
            
            # Convert date
            if 'match_date' in df.columns:
                df['match_date'] = pd.to_datetime(df['match_date'], errors='coerce')
                df = df.dropna(subset=['match_date'])
            
            logger.info(f"🔧 Standardized {dataset_name}: {len(df):,} valid matches")
            return df

        except Exception as e:
            logger.error(f"❌ Error standardizing {dataset_name}: {str(e)}")
            return pd.DataFrame()

    def merge_datasets(self, github_df: pd.DataFrame, apifootball_df: pd.DataFrame) -> pd.DataFrame:
        """Merge GitHub and APIFootball datasets intelligently."""
        logger.info("🔗 Merging GitHub and APIFootball datasets...")

        datasets = []

        # Process GitHub data
        if not github_df.empty:
            logger.info(f"📊 Processing GitHub data: {len(github_df):,} matches")

            # Ensure required columns exist
            if 'league_name' not in github_df.columns:
                github_df['league_name'] = github_df.get('dataset_name', 'Unknown League')

            datasets.append(github_df)

        # Process APIFootball data
        if not apifootball_df.empty:
            logger.info(f"🌐 Processing APIFootball data: {len(apifootball_df):,} matches")
            datasets.append(apifootball_df)

        if not datasets:
            logger.error("❌ No datasets to merge")
            return pd.DataFrame()

        # Combine datasets
        combined_df = pd.concat(datasets, ignore_index=True, sort=False)

        # Remove duplicates based on key fields
        before_dedup = len(combined_df)
        combined_df = combined_df.drop_duplicates(
            subset=['match_date', 'match_hometeam_name', 'match_awayteam_name',
                   'match_hometeam_score', 'match_awayteam_score'],
            keep='last'  # Keep APIFootball data over GitHub data
        )
        after_dedup = len(combined_df)

        logger.info(f"🔄 Removed {before_dedup - after_dedup:,} duplicate matches")
        logger.info(f"✅ Final merged dataset: {len(combined_df):,} unique matches")

        return combined_df

    def engineer_hybrid_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Engineer features from the merged dataset."""
        logger.info("🔧 Engineering features from hybrid dataset...")

        # Convert scores to numeric
        df['home_score'] = pd.to_numeric(df['match_hometeam_score'], errors='coerce')
        df['away_score'] = pd.to_numeric(df['match_awayteam_score'], errors='coerce')

        # Remove invalid data
        df = df.dropna(subset=['home_score', 'away_score'])
        df = df[(df['home_score'] >= 0) & (df['away_score'] >= 0)]

        logger.info(f"📊 Valid matches after cleaning: {len(df):,}")

        # Basic match statistics
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

        # Team encoding (crucial for predictions)
        if 'match_hometeam_name' in df.columns and 'match_awayteam_name' in df.columns:
            all_teams = pd.concat([df['match_hometeam_name'], df['match_awayteam_name']]).unique()
            le_teams = LabelEncoder()
            le_teams.fit(all_teams)

            df['home_team_encoded'] = le_teams.transform(df['match_hometeam_name'])
            df['away_team_encoded'] = le_teams.transform(df['match_awayteam_name'])
            self.encoders['teams'] = le_teams

        # Data source encoding
        if 'data_source' in df.columns:
            le_source = LabelEncoder()
            df['data_source_encoded'] = le_source.fit_transform(df['data_source'].fillna('unknown'))
            self.encoders['data_source'] = le_source

        # Date features
        if 'match_date' in df.columns:
            df['match_date'] = pd.to_datetime(df['match_date'], errors='coerce')
            df = df.dropna(subset=['match_date'])

            df['year'] = df['match_date'].dt.year
            df['month'] = df['match_date'].dt.month
            df['day_of_week'] = df['match_date'].dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

        # Select feature columns
        feature_columns = []

        # Categorical features
        categorical_features = ['league_encoded', 'country_encoded', 'home_team_encoded',
                              'away_team_encoded', 'data_source_encoded']
        feature_columns.extend([col for col in categorical_features if col in df.columns])

        # Temporal features
        temporal_features = ['year', 'month', 'day_of_week', 'is_weekend']
        feature_columns.extend([col for col in temporal_features if col in df.columns])

        logger.info(f"✅ Engineered {len(feature_columns)} features")
        logger.info(f"📊 Data sources: {df['data_source'].value_counts().to_dict()}")

        return df, feature_columns

    def train_hybrid_model(self, df: pd.DataFrame, feature_columns: List[str],
                          model_type: str, prediction_type: str) -> Dict[str, Any]:
        """Train a model with hybrid data."""
        logger.info(f"🤖 Training {model_type} model for {prediction_type} with hybrid data...")

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

        # Train model
        try:
            model = self.models_config[model_type][prediction_type]

            start_time = time.time()
            model.fit(X_train_scaled, y_train)
            training_time = time.time() - start_time

            # Evaluate
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)

            # Calculate confidence if available
            if hasattr(model, 'predict_proba'):
                y_proba = model.predict_proba(X_test_scaled)
                avg_confidence = np.mean(np.max(y_proba, axis=1))
            else:
                avg_confidence = None

            # Save model
            model_file = f"{self.models_dir}/{model_type}_{prediction_type}.pkl"
            joblib.dump(model, model_file)

            # Save scaler if used
            if model_type == 'neural_network':
                scaler_file = f"{self.models_dir}/{model_type}_{prediction_type}_scaler.pkl"
                joblib.dump(self.scalers[f"{model_type}_{prediction_type}"], scaler_file)

            logger.info(f"✅ {model_type} {prediction_type}: {accuracy:.3f} accuracy, {training_time:.1f}s")

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

    def train_all_hybrid_models(self, use_github: bool = True, use_apifootball: bool = True,
                               apifootball_months: int = 24) -> Dict[str, Any]:
        """Train all models using hybrid data sources."""
        logger.info("🚀 Starting hybrid model training...")
        logger.info(f"📊 GitHub data: {'✅ Enabled' if use_github else '❌ Disabled'}")
        logger.info(f"🌐 APIFootball data: {'✅ Enabled' if use_apifootball else '❌ Disabled'}")

        training_start = time.time()

        # Load datasets
        github_df = pd.DataFrame()
        apifootball_df = pd.DataFrame()

        if use_github:
            github_df = self.load_github_datasets()

        if use_apifootball:
            apifootball_df = self.fetch_recent_apifootball_data(months_back=apifootball_months)

        if github_df.empty and apifootball_df.empty:
            logger.error("❌ No data sources available")
            return {'status': 'failed', 'error': 'No data sources available'}

        # Merge datasets
        combined_df = self.merge_datasets(github_df, apifootball_df)

        if combined_df.empty:
            logger.error("❌ No data after merging")
            return {'status': 'failed', 'error': 'No data after merging'}

        # Engineer features
        df_processed, feature_columns = self.engineer_hybrid_features(combined_df)

        if df_processed.empty:
            logger.error("❌ No data after feature engineering")
            return {'status': 'failed', 'error': 'No data after feature engineering'}

        logger.info(f"✅ Final training dataset: {len(df_processed):,} matches with {len(feature_columns)} features")

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

        for model_type, prediction_configs in self.models_config.items():
            training_results[model_type] = {}
            logger.info(f"🔄 Training {model_type} models...")

            for prediction_type in prediction_configs.keys():
                total_models += 1

                if prediction_type not in df_processed.columns:
                    logger.warning(f"⚠️  Target {prediction_type} not found, skipping")
                    training_results[model_type][prediction_type] = {
                        'status': 'skipped',
                        'reason': 'Target not found'
                    }
                    continue

                # Train the model
                result = self.train_hybrid_model(df_processed, feature_columns, model_type, prediction_type)
                training_results[model_type][prediction_type] = result

                if result['status'] == 'success':
                    successful_models += 1

        # Save training metadata
        training_metadata = {
            'training_date': dt.now().isoformat(),
            'training_type': 'hybrid',
            'github_data_used': use_github,
            'apifootball_data_used': use_apifootball,
            'apifootball_months': apifootball_months if use_apifootball else 0,
            'total_matches': len(df_processed),
            'github_matches': len(github_df) if use_github else 0,
            'apifootball_matches': len(apifootball_df) if use_apifootball else 0,
            'feature_count': len(feature_columns),
            'models_trained': successful_models,
            'training_results': training_results
        }

        metadata_file = f"{self.models_dir}/hybrid_training_metadata.pkl"
        with open(metadata_file, 'wb') as f:
            pickle.dump(training_metadata, f)

        training_time = time.time() - training_start

        logger.info(f"🎯 Hybrid training completed!")
        logger.info(f"⏱️  Total time: {training_time/60:.1f} minutes")
        logger.info(f"✅ Successful models: {successful_models}/{total_models}")

        return {
            'status': 'completed',
            'total_models': total_models,
            'successful_models': successful_models,
            'training_time_minutes': training_time / 60,
            'total_matches': len(df_processed),
            'github_matches': len(github_df) if use_github else 0,
            'apifootball_matches': len(apifootball_df) if use_apifootball else 0,
            'feature_count': len(feature_columns),
            'results': training_results
        }


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description='Hybrid Model Trainer')
    parser.add_argument('--github-only', action='store_true', help='Use only GitHub data')
    parser.add_argument('--apifootball-only', action='store_true', help='Use only APIFootball data')
    parser.add_argument('--apifootball-months', type=int, default=24,
                       help='Months of APIFootball data to fetch (default: 24)')
    parser.add_argument('--summary', action='store_true', help='Show training summary')
    parser.add_argument('--test-github', action='store_true', help='Test GitHub data loading')

    args = parser.parse_args()

    trainer = HybridModelTrainer()

    if args.summary:
        print("📊 HYBRID TRAINING SUMMARY")
        print("=" * 50)

        metadata_file = f"{trainer.models_dir}/hybrid_training_metadata.pkl"
        if os.path.exists(metadata_file):
            with open(metadata_file, 'rb') as f:
                metadata = pickle.load(f)

            print(f"📅 Training Date: {metadata['training_date']}")
            print(f"🔗 Training Type: {metadata['training_type']}")
            print(f"📊 Total Matches: {metadata['total_matches']:,}")
            print(f"📚 GitHub Matches: {metadata['github_matches']:,}")
            print(f"🌐 APIFootball Matches: {metadata['apifootball_matches']:,}")
            print(f"🔧 Features: {metadata['feature_count']}")
            print(f"🤖 Models Trained: {metadata['models_trained']}")

            print("\n🎯 Model Performance:")
            for model_type, predictions in metadata['training_results'].items():
                print(f"\n  {model_type.upper()}:")
                for pred_type, result in predictions.items():
                    if result['status'] == 'success':
                        acc = result['accuracy']
                        samples = result['training_samples']
                        print(f"    {pred_type}: {acc:.3f} accuracy ({samples:,} samples)")
                    else:
                        print(f"    {pred_type}: {result['status']}")
        else:
            print("❌ No hybrid training metadata found")

        return

    if args.test_github:
        print("📊 Testing GitHub data loading...")
        github_df = trainer.load_github_datasets()
        if not github_df.empty:
            print(f"✅ Successfully loaded {len(github_df):,} matches from GitHub")
            print(f"📅 Date range: {github_df['match_date'].min()} to {github_df['match_date'].max()}")

            if 'league_name' in github_df.columns:
                print(f"🏆 Leagues: {github_df['league_name'].nunique()} unique leagues")
            elif 'dataset_name' in github_df.columns:
                print(f"🏆 Datasets: {github_df['dataset_name'].nunique()} unique datasets")

            if 'match_hometeam_name' in github_df.columns and 'match_awayteam_name' in github_df.columns:
                print(f"⚽ Teams: {pd.concat([github_df['match_hometeam_name'], github_df['match_awayteam_name']]).nunique()} unique teams")
        else:
            print("❌ Failed to load GitHub data")
        return

    # Determine data sources
    use_github = not args.apifootball_only
    use_apifootball = not args.github_only

    print("🚀 HYBRID MODEL TRAINER")
    print("=" * 60)
    print("🔗 Training with BOTH GitHub and APIFootball data")
    print(f"📊 GitHub datasets: {'✅ Enabled' if use_github else '❌ Disabled'}")
    print(f"🌐 APIFootball data: {'✅ Enabled' if use_apifootball else '❌ Disabled'}")
    if use_apifootball:
        print(f"📅 APIFootball months: {args.apifootball_months}")
    print("🤖 Models: XGBoost, LightGBM, Neural Networks, Random Forest")
    print("🎯 Predictions: Match Result, BTTS, Over/Under, Clean Sheets, Win to Nil")
    print()

    confirm = input("Continue with hybrid training? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ Training cancelled")
        return

    result = trainer.train_all_hybrid_models(
        use_github=use_github,
        use_apifootball=use_apifootball,
        apifootball_months=args.apifootball_months
    )

    print("\n" + "=" * 60)
    print("📊 HYBRID TRAINING RESULTS")
    print("=" * 60)

    if result['status'] == 'completed':
        print(f"✅ Status: {result['status'].upper()}")
        print(f"🤖 Models Trained: {result['successful_models']}/{result['total_models']}")
        print(f"⏱️  Training Time: {result['training_time_minutes']:.1f} minutes")
        print(f"📊 Total Matches: {result['total_matches']:,}")
        print(f"📚 GitHub Matches: {result['github_matches']:,}")
        print(f"🌐 APIFootball Matches: {result['apifootball_matches']:,}")
        print(f"🔧 Features: {result['feature_count']}")

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
