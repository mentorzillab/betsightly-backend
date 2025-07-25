#!/usr/bin/env python3
"""
Streamlined ML Prediction Pipeline

Production-ready workflow for football match predictions:
1. Train advanced ML models using GitHub historical data
2. Fetch live fixtures using API keys
3. Generate high-quality predictions
4. Return best results based on confidence and accuracy

This replaces all redundant scripts with a single, focused pipeline.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import joblib
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from utils.config import settings
from utils.common import setup_logging, ensure_directory_exists
from ml.advanced_feature_engineering import AdvancedFootballFeatureEngineer
from services.api_client import FootballDataClient, APIClient
from services.enhanced_feature_extractor import EnhancedFeatureExtractor

# Set up logging
logger = setup_logging("ml_pipeline_streamlined")

class StreamlinedMLPipeline:
    """
    Streamlined ML prediction pipeline for production use.
    
    Focuses on:
    - Advanced ML models (XGBoost, LightGBM, Neural Networks, LSTM)
    - GitHub dataset for training
    - Live API data for predictions
    - High-quality, filtered results
    """
    
    def __init__(self):
        """Initialize the streamlined pipeline."""
        self.models = {}
        self.feature_engineer = AdvancedFootballFeatureEngineer()
        self.enhanced_feature_extractor = EnhancedFeatureExtractor()
        self.api_client = None
        
        # Ensure directories exist
        ensure_directory_exists(settings.ml.MODEL_DIR)
        ensure_directory_exists(settings.ml.DATA_DIR)
        ensure_directory_exists(settings.ml.CACHE_DIR)
        
        logger.info("Streamlined ML Pipeline initialized")
    
    def download_github_dataset(self) -> pd.DataFrame:
        """
        Download and cache the GitHub football dataset for training.
        
        Returns:
            DataFrame with historical football data
        """
        cache_file = os.path.join(settings.ml.CACHE_DIR, "github_football_dataset.parquet")
        
        # Check if cached version exists and is recent
        if os.path.exists(cache_file):
            file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
            if file_age.days < 7:  # Use cache if less than 7 days old
                logger.info("Loading cached GitHub dataset")
                return pd.read_parquet(cache_file)
        
        logger.info("Downloading GitHub football dataset...")
        try:
            # Download from GitHub
            response = requests.get(settings.data_source.GITHUB_DATASET_URL, timeout=60)
            response.raise_for_status()
            
            # Parse CSV
            df = pd.read_csv(response.content.decode('utf-8'))
            
            # Cache as parquet for faster loading
            df.to_parquet(cache_file)
            logger.info(f"Downloaded and cached {len(df)} matches from GitHub dataset")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to download GitHub dataset: {str(e)}")
            raise
    
    def prepare_training_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, pd.Series]]:
        """
        Prepare training data from GitHub dataset.
        
        Args:
            df: Raw GitHub dataset
            
        Returns:
            Tuple of (features_df, targets_dict)
        """
        logger.info("Preparing training data from GitHub dataset...")
        
        # Use feature engineer to create advanced features
        features_df = self.feature_engineer.engineer_features(df)
        
        # Create target variables
        targets = {}
        
        # Match result (home win, draw, away win)
        targets['match_result'] = self._create_match_result_target(df)
        
        # Over/Under 2.5 goals
        targets['over_under'] = self._create_over_under_target(df)
        
        # Both teams to score
        targets['btts'] = self._create_btts_target(df)
        
        logger.info(f"Prepared {len(features_df)} training samples with {len(features_df.columns)} features")
        
        return features_df, targets
    
    def _create_match_result_target(self, df: pd.DataFrame) -> pd.Series:
        """Create match result target variable."""
        def get_result(row):
            home_goals = row.get('home_goals', row.get('FTHG', 0))
            away_goals = row.get('away_goals', row.get('FTAG', 0))
            
            if home_goals > away_goals:
                return 'home'
            elif away_goals > home_goals:
                return 'away'
            else:
                return 'draw'
        
        return df.apply(get_result, axis=1)
    
    def _create_over_under_target(self, df: pd.DataFrame) -> pd.Series:
        """Create over/under 2.5 goals target."""
        def get_over_under(row):
            home_goals = row.get('home_goals', row.get('FTHG', 0))
            away_goals = row.get('away_goals', row.get('FTAG', 0))
            total_goals = home_goals + away_goals
            return 'over' if total_goals > 2.5 else 'under'
        
        return df.apply(get_over_under, axis=1)
    
    def _create_btts_target(self, df: pd.DataFrame) -> pd.Series:
        """Create both teams to score target."""
        def get_btts(row):
            home_goals = row.get('home_goals', row.get('FTHG', 0))
            away_goals = row.get('away_goals', row.get('FTAG', 0))
            return 'yes' if home_goals > 0 and away_goals > 0 else 'no'
        
        return df.apply(get_btts, axis=1)
    
    def train_advanced_models(self, features_df: pd.DataFrame, targets: Dict[str, pd.Series]) -> Dict[str, Any]:
        """
        Train advanced ML models in priority order.
        
        Args:
            features_df: Feature matrix
            targets: Target variables
            
        Returns:
            Training results
        """
        logger.info("Training advanced ML models...")
        
        # Get preferred models in order
        preferred_models = settings.ml.PREFERRED_MODELS.split(',')
        results = {}
        
        for model_name in preferred_models:
            model_name = model_name.strip()
            
            try:
                if model_name == 'xgboost':
                    results[model_name] = self._train_xgboost_models(features_df, targets)
                elif model_name == 'lightgbm':
                    results[model_name] = self._train_lightgbm_models(features_df, targets)
                elif model_name == 'neural_network':
                    results[model_name] = self._train_neural_network_models(features_df, targets)
                elif model_name == 'lstm':
                    results[model_name] = self._train_lstm_models(features_df, targets)
                elif model_name == 'ensemble':
                    results[model_name] = self._train_ensemble_models(features_df, targets)
                else:
                    logger.warning(f"Unknown model type: {model_name}")
                    
            except Exception as e:
                logger.error(f"Failed to train {model_name}: {str(e)}")
                continue
        
        return results
    
    def _train_xgboost_models(self, features_df: pd.DataFrame, targets: Dict[str, pd.Series]) -> Dict[str, Any]:
        """Train XGBoost models for all prediction types."""
        try:
            import xgboost as xgb
            from sklearn.model_selection import train_test_split
            from sklearn.preprocessing import StandardScaler, LabelEncoder
            from sklearn.metrics import accuracy_score, classification_report
            
            results = {}
            
            for target_name, target_series in targets.items():
                logger.info(f"Training XGBoost model for {target_name}")
                
                # Prepare data
                X = features_df.fillna(0)
                y = target_series
                
                # Encode labels
                le = LabelEncoder()
                y_encoded = le.fit_transform(y)
                
                # Split data
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y_encoded, 
                    test_size=settings.ml.TRAIN_TEST_SPLIT, 
                    random_state=42
                )
                
                # Scale features
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                
                # Train XGBoost model
                if len(le.classes_) > 2:
                    # Multi-class classification
                    model = xgb.XGBClassifier(
                        objective='multi:softprob',
                        num_class=len(le.classes_),
                        n_estimators=200,
                        max_depth=6,
                        learning_rate=0.1,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        random_state=42
                    )
                else:
                    # Binary classification
                    model = xgb.XGBClassifier(
                        objective='binary:logistic',
                        n_estimators=200,
                        max_depth=6,
                        learning_rate=0.1,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        random_state=42
                    )
                
                # Fit model
                model.fit(X_train_scaled, y_train)
                
                # Evaluate
                y_pred = model.predict(X_test_scaled)
                accuracy = accuracy_score(y_test, y_pred)
                
                # Save model
                model_path = os.path.join(settings.ml.MODEL_DIR, f"xgboost_{target_name}_model.joblib")
                scaler_path = os.path.join(settings.ml.MODEL_DIR, f"xgboost_{target_name}_scaler.joblib")
                encoder_path = os.path.join(settings.ml.MODEL_DIR, f"xgboost_{target_name}_encoder.joblib")
                
                joblib.dump(model, model_path)
                joblib.dump(scaler, scaler_path)
                joblib.dump(le, encoder_path)
                
                results[target_name] = {
                    'accuracy': accuracy,
                    'model_path': model_path,
                    'scaler_path': scaler_path,
                    'encoder_path': encoder_path
                }
                
                logger.info(f"XGBoost {target_name} model trained with accuracy: {accuracy:.4f}")
            
            return results
            
        except ImportError:
            logger.warning("XGBoost not available, skipping XGBoost models")
            return {}
        except Exception as e:
            logger.error(f"Error training XGBoost models: {str(e)}")
            return {}

    def _train_lightgbm_models(self, features_df: pd.DataFrame, targets: Dict[str, pd.Series]) -> Dict[str, Any]:
        """Train LightGBM models for all prediction types."""
        try:
            import lightgbm as lgb
            from sklearn.model_selection import train_test_split
            from sklearn.preprocessing import StandardScaler, LabelEncoder
            from sklearn.metrics import accuracy_score

            results = {}

            for target_name, target_series in targets.items():
                logger.info(f"Training LightGBM model for {target_name}")

                # Prepare data
                X = features_df.fillna(0)
                y = target_series

                # Encode labels
                le = LabelEncoder()
                y_encoded = le.fit_transform(y)

                # Split data
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y_encoded,
                    test_size=settings.ml.TRAIN_TEST_SPLIT,
                    random_state=42
                )

                # Train LightGBM model
                if len(le.classes_) > 2:
                    # Multi-class classification
                    model = lgb.LGBMClassifier(
                        objective='multiclass',
                        num_class=len(le.classes_),
                        n_estimators=200,
                        max_depth=6,
                        learning_rate=0.1,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        random_state=42,
                        verbose=-1
                    )
                else:
                    # Binary classification
                    model = lgb.LGBMClassifier(
                        objective='binary',
                        n_estimators=200,
                        max_depth=6,
                        learning_rate=0.1,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        random_state=42,
                        verbose=-1
                    )

                # Fit model
                model.fit(X_train, y_train)

                # Evaluate
                y_pred = model.predict(X_test)
                accuracy = accuracy_score(y_test, y_pred)

                # Save model
                model_path = os.path.join(settings.ml.MODEL_DIR, f"lightgbm_{target_name}_model.joblib")
                encoder_path = os.path.join(settings.ml.MODEL_DIR, f"lightgbm_{target_name}_encoder.joblib")

                joblib.dump(model, model_path)
                joblib.dump(le, encoder_path)

                results[target_name] = {
                    'accuracy': accuracy,
                    'model_path': model_path,
                    'encoder_path': encoder_path
                }

                logger.info(f"LightGBM {target_name} model trained with accuracy: {accuracy:.4f}")

            return results

        except ImportError:
            logger.warning("LightGBM not available, skipping LightGBM models")
            return {}
        except Exception as e:
            logger.error(f"Error training LightGBM models: {str(e)}")
            return {}

    def _train_ensemble_models(self, features_df: pd.DataFrame, targets: Dict[str, pd.Series]) -> Dict[str, Any]:
        """Train ensemble models as fallback."""
        try:
            from sklearn.ensemble import RandomForestClassifier, VotingClassifier
            from sklearn.linear_model import LogisticRegression
            from sklearn.svm import SVC
            from sklearn.model_selection import train_test_split
            from sklearn.preprocessing import StandardScaler, LabelEncoder
            from sklearn.metrics import accuracy_score

            results = {}

            for target_name, target_series in targets.items():
                logger.info(f"Training ensemble model for {target_name}")

                # Prepare data
                X = features_df.fillna(0)
                y = target_series

                # Encode labels
                le = LabelEncoder()
                y_encoded = le.fit_transform(y)

                # Split data
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y_encoded,
                    test_size=settings.ml.TRAIN_TEST_SPLIT,
                    random_state=42
                )

                # Scale features
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)

                # Create ensemble
                rf = RandomForestClassifier(n_estimators=100, random_state=42)
                lr = LogisticRegression(random_state=42, max_iter=1000)
                svm = SVC(probability=True, random_state=42)

                ensemble = VotingClassifier(
                    estimators=[('rf', rf), ('lr', lr), ('svm', svm)],
                    voting='soft'
                )

                # Fit model
                ensemble.fit(X_train_scaled, y_train)

                # Evaluate
                y_pred = ensemble.predict(X_test_scaled)
                accuracy = accuracy_score(y_test, y_pred)

                # Save model
                model_path = os.path.join(settings.ml.MODEL_DIR, f"ensemble_{target_name}_model.joblib")
                scaler_path = os.path.join(settings.ml.MODEL_DIR, f"ensemble_{target_name}_scaler.joblib")
                encoder_path = os.path.join(settings.ml.MODEL_DIR, f"ensemble_{target_name}_encoder.joblib")

                joblib.dump(ensemble, model_path)
                joblib.dump(scaler, scaler_path)
                joblib.dump(le, encoder_path)

                results[target_name] = {
                    'accuracy': accuracy,
                    'model_path': model_path,
                    'scaler_path': scaler_path,
                    'encoder_path': encoder_path
                }

                logger.info(f"Ensemble {target_name} model trained with accuracy: {accuracy:.4f}")

            return results

        except Exception as e:
            logger.error(f"Error training ensemble models: {str(e)}")
            return {}

    def _train_neural_network_models(self, features_df: pd.DataFrame, targets: Dict[str, pd.Series]) -> Dict[str, Any]:
        """Train neural network models (placeholder for now)."""
        logger.info("Neural network models not implemented yet, skipping...")
        return {}

    def _train_lstm_models(self, features_df: pd.DataFrame, targets: Dict[str, pd.Series]) -> Dict[str, Any]:
        """Train LSTM models (placeholder for now)."""
        logger.info("LSTM models not implemented yet, skipping...")
        return {}

    def load_best_models(self) -> Dict[str, Any]:
        """
        Load the best available trained models.

        Priority:
        1. Enhanced models (62 features) from models_enhanced/
        2. Fallback to basic models (14 features) from models/

        Returns:
            Dictionary of loaded models
        """
        logger.info("Loading best available models...")

        models = {}

        # Try enhanced models first (62 features)
        enhanced_models_dir = "models_enhanced"
        if os.path.exists(enhanced_models_dir):
            logger.info("🚀 Loading enhanced models (62 features)...")
            models = self._load_models_from_directory(enhanced_models_dir, "enhanced")

        # Fallback to basic models if enhanced models not available
        if not models:
            logger.info("⚡ Loading basic models (14 features)...")
            models = self._load_models_from_directory(settings.ml.MODEL_DIR, "basic")

        if not models:
            logger.warning("No trained models found. Please run training first.")
        else:
            logger.info(f"✅ Loaded {len(models)} models successfully")

        self.models = models
        return models

    def _load_models_from_directory(self, models_dir: str, model_type_label: str) -> Dict[str, Any]:
        """Load models from a specific directory."""
        import pickle

        models = {}
        model_types = ['xgboost', 'lightgbm', 'ensemble', 'random_forest', 'neural_network']
        prediction_types = ['match_result', 'over_2_5', 'over_1_5', 'over_3_5', 'btts', 'clean_sheet_home', 'clean_sheet_away', 'win_to_nil_home', 'win_to_nil_away']

        for model_type in model_types:
            for pred_type in prediction_types:
                # Try different file extensions and naming patterns
                possible_paths = [
                    os.path.join(models_dir, f"{model_type}_{pred_type}_model.joblib"),
                    os.path.join(models_dir, f"{model_type}_{pred_type}.joblib"),
                    os.path.join(models_dir, f"{model_type}_{pred_type}.pkl"),
                    os.path.join(models_dir, f"{model_type}_{pred_type}_model.pkl")
                ]

                model_loaded = False
                for model_path in possible_paths:
                    if os.path.exists(model_path):
                        try:
                            # Load model based on file extension
                            if model_path.endswith('.pkl'):
                                with open(model_path, 'rb') as f:
                                    model = pickle.load(f)
                            else:
                                model = joblib.load(model_path)

                            # Load associated scaler and encoder if they exist
                            scaler_path = os.path.join(models_dir, f"{model_type}_{pred_type}_scaler.joblib")
                            encoder_path = os.path.join(models_dir, f"{model_type}_{pred_type}_encoder.joblib")

                            # Try pickle versions too
                            if not os.path.exists(scaler_path):
                                scaler_path = os.path.join(models_dir, f"{model_type}_{pred_type}_scaler.pkl")
                            if not os.path.exists(encoder_path):
                                encoder_path = os.path.join(models_dir, f"{model_type}_{pred_type}_encoder.pkl")

                            scaler = None
                            encoder = None

                            if os.path.exists(scaler_path):
                                if scaler_path.endswith('.pkl'):
                                    with open(scaler_path, 'rb') as f:
                                        scaler = pickle.load(f)
                                else:
                                    scaler = joblib.load(scaler_path)

                            if os.path.exists(encoder_path):
                                if encoder_path.endswith('.pkl'):
                                    with open(encoder_path, 'rb') as f:
                                        encoder = pickle.load(f)
                                else:
                                    encoder = joblib.load(encoder_path)

                            models[f"{model_type}_{pred_type}"] = {
                                'model': model,
                                'scaler': scaler,
                                'encoder': encoder,
                                'type': model_type,
                                'prediction_type': pred_type,
                                'model_source': model_type_label
                            }

                            logger.info(f"✅ Loaded {model_type}/{pred_type} ({model_type_label})")
                            model_loaded = True
                            break

                        except Exception as e:
                            logger.error(f"❌ Failed to load {model_path}: {str(e)}")
                            continue

        return models

    def setup_api_client(self) -> bool:
        """
        Setup API client for fetching live fixtures.

        Returns:
            True if API client is configured successfully
        """
        # Try Football-Data.org first
        if settings.football_data.API_KEY:
            try:
                self.api_client = FootballDataClient(
                    api_key=settings.football_data.API_KEY,
                    base_url=settings.football_data.BASE_URL
                )
                logger.info("Configured Football-Data.org API client")
                return True
            except Exception as e:
                logger.error(f"Failed to setup Football-Data.org client: {str(e)}")

        # Try API-Football as fallback (using generic APIClient for now)
        if settings.api_football.API_KEY:
            try:
                headers = {
                    "X-RapidAPI-Key": settings.api_football.API_KEY,
                    "X-RapidAPI-Host": settings.api_football.API_HOST
                }
                self.api_client = APIClient(
                    base_url=settings.api_football.BASE_URL,
                    headers=headers
                )
                logger.info("Configured API-Football client")
                return True
            except Exception as e:
                logger.error(f"Failed to setup API-Football client: {str(e)}")

        logger.error("No API keys configured. Please set FOOTBALL_DATA_KEY or API_FOOTBALL_KEY")
        return False

    def fetch_live_fixtures(self, date: str = None) -> List[Dict[str, Any]]:
        """
        Fetch live fixtures for prediction.

        Args:
            date: Date in YYYY-MM-DD format (default: today)

        Returns:
            List of fixtures
        """
        if not self.api_client:
            if not self.setup_api_client():
                return []

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Fetching live fixtures for {date}")

        try:
            # Fetch fixtures from API
            if hasattr(self.api_client, 'get_daily_matches'):
                # Football-Data.org client
                response = self.api_client.get_daily_matches(date)
                fixtures = response.get('matches', []) if isinstance(response, dict) else []
            else:
                # Generic API client - try fixtures endpoint
                response = self.api_client.get('fixtures', params={'date': date})
                fixtures = response.get('response', []) if isinstance(response, dict) else []

            logger.info(f"Fetched {len(fixtures)} fixtures for {date}")
            return fixtures

        except Exception as e:
            logger.error(f"Failed to fetch fixtures: {str(e)}")
            return []

    def generate_predictions(self, fixtures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate predictions for fixtures using best available models.

        Args:
            fixtures: List of fixtures to predict

        Returns:
            List of predictions with confidence scores
        """
        if not self.models:
            logger.warning("No models loaded. Loading models...")
            self.load_best_models()

        if not self.models:
            logger.error("No models available for prediction")
            return []

        logger.info(f"Generating predictions for {len(fixtures)} fixtures")

        predictions = []

        for fixture in fixtures:
            try:
                # Extract features for this fixture using enhanced extractor
                features = self.enhanced_feature_extractor.extract_fixture_features(fixture)

                if features is None:
                    continue

                # Generate predictions using available models
                fixture_predictions = self._predict_fixture(fixture, features)

                if fixture_predictions:
                    predictions.extend(fixture_predictions)

            except Exception as e:
                logger.error(f"Failed to predict fixture {fixture.get('id', 'unknown')}: {str(e)}")
                continue

        # Filter and rank predictions
        filtered_predictions = self._filter_and_rank_predictions(predictions)

        logger.info(f"Generated {len(filtered_predictions)} high-quality predictions")

        return filtered_predictions

    def _predict_fixture(self, fixture: Dict[str, Any], features: np.ndarray) -> List[Dict[str, Any]]:
        """
        Generate predictions for a single fixture using all available models.

        Args:
            fixture: Fixture data
            features: Extracted features

        Returns:
            List of predictions for this fixture
        """
        predictions = []

        # Get the best model for each prediction type
        best_models = self._get_best_models_by_type()

        for pred_type, model_info in best_models.items():
            try:
                # Prepare features
                if model_info['scaler']:
                    features_scaled = model_info['scaler'].transform(features.reshape(1, -1))
                else:
                    features_scaled = features.reshape(1, -1)

                # Make prediction
                prediction_proba = model_info['model'].predict_proba(features_scaled)[0]
                prediction_class = model_info['model'].predict(features_scaled)[0]

                # Decode prediction
                if model_info['encoder']:
                    prediction_label = model_info['encoder'].inverse_transform([prediction_class])[0]
                else:
                    prediction_label = prediction_class

                # Calculate confidence (max probability)
                confidence = float(np.max(prediction_proba))

                # Only include high-confidence predictions
                if confidence >= settings.ml.MIN_CONFIDENCE_THRESHOLD:
                    prediction = {
                        'fixture_id': fixture.get('id'),
                        'home_team': fixture.get('homeTeam', {}).get('name', 'Unknown'),
                        'away_team': fixture.get('awayTeam', {}).get('name', 'Unknown'),
                        'match_date': fixture.get('utcDate', ''),
                        'prediction_type': pred_type,
                        'prediction': prediction_label,
                        'confidence': confidence,
                        'model_type': model_info['type'],
                        'odds': self._calculate_odds_from_confidence(confidence),
                        'category': self._categorize_prediction(confidence)
                    }

                    predictions.append(prediction)

            except Exception as e:
                logger.error(f"Failed to predict {pred_type} for fixture {fixture.get('id')}: {str(e)}")
                continue

        return predictions

    def _get_best_models_by_type(self) -> Dict[str, Dict[str, Any]]:
        """Get the best model for each prediction type based on priority."""
        best_models = {}

        # Define prediction type mappings
        prediction_mappings = {
            'match_result': ['match_result'],
            'over_under': ['over_2_5', 'over_1_5', 'over_3_5'],
            'btts': ['btts'],
            'clean_sheet_home': ['clean_sheet_home'],
            'clean_sheet_away': ['clean_sheet_away'],
            'win_to_nil_home': ['win_to_nil_home'],
            'win_to_nil_away': ['win_to_nil_away']
        }

        # Model priority order (enhanced models first)
        model_priority = ['xgboost', 'lightgbm', 'random_forest', 'neural_network', 'ensemble']

        for pred_category, pred_types in prediction_mappings.items():
            for pred_type in pred_types:
                for model_type in model_priority:
                    model_key = f"{model_type}_{pred_type}"
                    if model_key in self.models:
                        best_models[pred_category] = self.models[model_key]
                        logger.debug(f"Selected {model_key} for {pred_category}")
                        break
                if pred_category in best_models:
                    break

        logger.info(f"Selected {len(best_models)} best models for prediction")
        return best_models

    def _calculate_odds_from_confidence(self, confidence: float) -> float:
        """Calculate betting odds from confidence score."""
        if confidence <= 0:
            return 1.0

        # Convert confidence to decimal odds
        odds = 1.0 / confidence

        # Add bookmaker margin (typically 5-10%)
        odds *= 1.05

        return round(odds, 2)

    def _categorize_prediction(self, confidence: float) -> str:
        """Categorize prediction based on confidence and calculated odds."""
        odds = self._calculate_odds_from_confidence(confidence)

        if odds <= 2.5:
            return "2_odds"  # Safe bets
        elif odds <= 6.0:
            return "5_odds"  # Balanced risk
        elif odds <= 12.0:
            return "10_odds"  # High reward
        else:
            return "rollover"  # Very high risk

    def _filter_and_rank_predictions(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter and rank predictions to return only the best ones.

        Args:
            predictions: Raw predictions

        Returns:
            Filtered and ranked predictions
        """
        if not predictions:
            return []

        # Sort by confidence (highest first)
        sorted_predictions = sorted(predictions, key=lambda x: x['confidence'], reverse=True)

        # Group by category
        categorized = {}
        for pred in sorted_predictions:
            category = pred['category']
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(pred)

        # Limit predictions per category
        filtered_predictions = []
        for category, category_predictions in categorized.items():
            limited = category_predictions[:settings.ml.MAX_PREDICTIONS_PER_CATEGORY]
            filtered_predictions.extend(limited)

        # Final sort by confidence
        filtered_predictions.sort(key=lambda x: x['confidence'], reverse=True)

        return filtered_predictions

    def run_full_pipeline(self, date: str = None, force_retrain: bool = False) -> Dict[str, Any]:
        """
        Run the complete streamlined ML prediction pipeline.

        Args:
            date: Date for predictions (YYYY-MM-DD format)
            force_retrain: Whether to retrain models

        Returns:
            Pipeline results
        """
        logger.info("Starting streamlined ML prediction pipeline...")

        results = {
            'date': date or datetime.now().strftime("%Y-%m-%d"),
            'training_results': {},
            'predictions': [],
            'summary': {}
        }

        try:
            # Step 1: Train models if needed
            if force_retrain or not self._models_exist():
                logger.info("Training models using GitHub dataset...")

                # Download GitHub dataset
                df = self.download_github_dataset()

                # Prepare training data
                features_df, targets = self.prepare_training_data(df)

                # Train advanced models
                training_results = self.train_advanced_models(features_df, targets)
                results['training_results'] = training_results

                logger.info("Model training completed")

            # Step 2: Load best models
            self.load_best_models()

            # Step 3: Fetch live fixtures
            fixtures = self.fetch_live_fixtures(date)

            if not fixtures:
                logger.warning("No fixtures found for prediction")
                return results

            # Step 4: Generate predictions
            predictions = self.generate_predictions(fixtures)
            results['predictions'] = predictions

            # Step 5: Generate summary
            results['summary'] = self._generate_summary(predictions)

            logger.info("Streamlined ML pipeline completed successfully")

        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            results['error'] = str(e)

        return results

    def predict_single_fixture(self, fixture: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate predictions for a single fixture using enhanced models.

        Args:
            fixture: Fixture data dictionary

        Returns:
            Dictionary with prediction results in the format expected by complete pipeline
        """
        try:
            # Extract features using enhanced feature extractor
            features = self.enhanced_feature_extractor.extract_fixture_features(fixture)

            if features is None:
                return {"error": "Could not extract features"}

            # Generate predictions
            predictions = self._predict_fixture(fixture, features)

            if not predictions:
                return {"error": "No predictions generated"}

            # Format results to match expected format
            fixture_predictions = {
                'fixture_info': {
                    'fixture_id': fixture.get('fixture_id', fixture.get('id', 0)),
                    'home_team': fixture.get('home_team', ''),
                    'away_team': fixture.get('away_team', ''),
                    'league': fixture.get('league_name', fixture.get('league', '')),
                    'date': fixture.get('date', ''),
                    'status': fixture.get('status', 'upcoming')
                },
                'predictions': {},
                'betting_categories': {},
                'model_summary': {
                    'total_predictions': len(predictions),
                    'successful_predictions': len(predictions)
                }
            }

            # Convert predictions to expected format
            for pred in predictions:
                pred_type = pred['prediction_type']
                fixture_predictions['predictions'][pred_type] = {
                    'prediction': int(pred['prediction']),  # Convert numpy int64 to Python int
                    'confidence': float(pred['confidence']),  # Convert numpy float64 to Python float
                    'model_type': pred.get('model_type', 'enhanced')
                }

            return fixture_predictions

        except Exception as e:
            logger.error(f"Error predicting single fixture: {str(e)}")
            return {"error": f"Prediction failed: {str(e)}"}

    def _models_exist(self) -> bool:
        """Check if trained models exist (prioritize enhanced models)."""
        model_files = [
            'xgboost_match_result_model.joblib',
            'lightgbm_match_result_model.joblib',
            'ensemble_match_result_model.joblib',
            'random_forest_match_result_model.joblib',
            'neural_network_match_result_model.joblib'
        ]

        # Check enhanced models first
        enhanced_models_dir = "models_enhanced"
        if os.path.exists(enhanced_models_dir):
            for model_file in model_files:
                if os.path.exists(os.path.join(enhanced_models_dir, model_file)):
                    logger.info(f"✅ Found enhanced models in {enhanced_models_dir}")
                    return True

        # Fallback to basic models
        for model_file in model_files:
            if os.path.exists(os.path.join(settings.ml.MODEL_DIR, model_file)):
                logger.info(f"✅ Found basic models in {settings.ml.MODEL_DIR}")
                return True

        return False

    def _generate_summary(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for predictions."""
        if not predictions:
            return {}

        summary = {
            'total_predictions': len(predictions),
            'avg_confidence': np.mean([p['confidence'] for p in predictions]),
            'categories': {},
            'model_types': {}
        }

        # Count by category
        for pred in predictions:
            category = pred['category']
            model_type = pred['model_type']

            if category not in summary['categories']:
                summary['categories'][category] = 0
            summary['categories'][category] += 1

            if model_type not in summary['model_types']:
                summary['model_types'][model_type] = 0
            summary['model_types'][model_type] += 1

        return summary


# Main execution
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Streamlined ML Prediction Pipeline")
    parser.add_argument("--date", help="Date for predictions (YYYY-MM-DD)")
    parser.add_argument("--retrain", action="store_true", help="Force model retraining")
    parser.add_argument("--train-only", action="store_true", help="Only train models, don't predict")

    args = parser.parse_args()

    # Initialize pipeline
    pipeline = StreamlinedMLPipeline()

    if args.train_only:
        # Only train models
        logger.info("Training models only...")
        df = pipeline.download_github_dataset()
        features_df, targets = pipeline.prepare_training_data(df)
        results = pipeline.train_advanced_models(features_df, targets)
        print(f"Training completed. Results: {results}")
    else:
        # Run full pipeline
        results = pipeline.run_full_pipeline(date=args.date, force_retrain=args.retrain)
        print(f"Pipeline completed. Generated {len(results.get('predictions', []))} predictions.")

        # Print summary
        if 'summary' in results:
            print(f"Summary: {results['summary']}")
