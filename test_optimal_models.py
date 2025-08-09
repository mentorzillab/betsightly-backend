#!/usr/bin/env python3
"""
Test Optimal Models
==================

This script tests the newly trained optimal models with today's fixtures
to evaluate their real-world performance and prediction quality.
"""

import os
import sys
import json
import pickle
import logging
import numpy as np
import pandas as pd
from datetime import datetime as dt
from typing import Dict, List, Any, Optional
import joblib

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config import settings
from utils.common import setup_logging
from daily_fixture_manager import DailyFixtureManager

# Set up logging
logger = setup_logging(__name__)

class OptimalModelTester:
    """Test optimal models with real fixtures."""
    
    def __init__(self):
        """Initialize the model tester."""
        self.models_dir = "models"
        self.models = {}
        self.encoders = {}
        self.feature_columns = []
        
        # Load optimal models and metadata
        self.load_optimal_models()
    
    def load_optimal_models(self):
        """Load all optimal models and their metadata."""
        logger.info("🤖 Loading optimal models...")
        
        # Load encoders
        encoders_file = f"{self.models_dir}/optimal_encoders.pkl"
        if os.path.exists(encoders_file):
            with open(encoders_file, 'rb') as f:
                self.encoders = pickle.load(f)
            logger.info("✅ Loaded optimal encoders")
        else:
            logger.warning("⚠️  No optimal encoders found")
        
        # Load training metadata
        metadata_file = f"{self.models_dir}/optimal_training_metadata.pkl"
        if os.path.exists(metadata_file):
            with open(metadata_file, 'rb') as f:
                metadata = pickle.load(f)
            
            logger.info(f"📊 Training metadata loaded:")
            logger.info(f"   Training date: {metadata.get('training_date')}")
            logger.info(f"   Data range: {metadata.get('data_range')}")
            logger.info(f"   Total matches: {metadata.get('total_matches'):,}")
            logger.info(f"   Models trained: {metadata.get('models_trained')}")
        
        # Load individual models
        model_files = [
            ('match_result', 'lightgbm', 'optimal_lightgbm_match_result.pkl'),
            ('match_result', 'neural_network', 'optimal_neural_network_match_result.pkl'),
            ('match_result', 'random_forest', 'optimal_random_forest_match_result.pkl'),
            ('btts', 'xgboost', 'optimal_xgboost_btts.pkl'),
            ('btts', 'lightgbm', 'optimal_lightgbm_btts.pkl'),
            ('btts', 'neural_network', 'optimal_neural_network_btts.pkl'),
            ('btts', 'random_forest', 'optimal_random_forest_btts.pkl'),
            ('over_2_5', 'xgboost', 'optimal_xgboost_over_2_5.pkl'),
            ('over_2_5', 'lightgbm', 'optimal_lightgbm_over_2_5.pkl'),
            ('over_2_5', 'neural_network', 'optimal_neural_network_over_2_5.pkl'),
            ('over_2_5', 'random_forest', 'optimal_random_forest_over_2_5.pkl'),
            ('clean_sheet_home', 'xgboost', 'optimal_xgboost_clean_sheet_home.pkl'),
            ('clean_sheet_home', 'lightgbm', 'optimal_lightgbm_clean_sheet_home.pkl'),
            ('clean_sheet_away', 'xgboost', 'optimal_xgboost_clean_sheet_away.pkl'),
            ('clean_sheet_away', 'lightgbm', 'optimal_lightgbm_clean_sheet_away.pkl')
        ]
        
        models_loaded = 0
        for prediction_type, model_type, filename in model_files:
            model_path = os.path.join(self.models_dir, filename)
            
            if os.path.exists(model_path):
                try:
                    model = joblib.load(model_path)
                    
                    if prediction_type not in self.models:
                        self.models[prediction_type] = {}
                    
                    self.models[prediction_type][model_type] = model
                    models_loaded += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️  Failed to load {filename}: {e}")
            else:
                logger.warning(f"⚠️  Model file not found: {filename}")
        
        logger.info(f"✅ Loaded {models_loaded} optimal models")
        
        # Set feature columns (simplified for testing)
        self.feature_columns = ['home_team_encoded', 'away_team_encoded']
    
    def get_todays_fixtures(self) -> List[Dict]:
        """Get today's fixtures using the daily fixture manager."""
        logger.info("🏈 Getting today's fixtures...")
        
        try:
            fixture_manager = DailyFixtureManager()
            result = fixture_manager.get_daily_fixtures()
            
            if result['status'] == 'success':
                fixtures = result['fixtures']
                logger.info(f"✅ Loaded {len(fixtures)} fixtures for today")
                return fixtures
            else:
                logger.error(f"❌ Failed to get fixtures: {result.get('error')}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting fixtures: {str(e)}")
            return []
    
    def prepare_fixture_features(self, fixtures: List[Dict]) -> pd.DataFrame:
        """Prepare features for fixtures."""
        logger.info("🔧 Preparing fixture features...")
        
        fixture_data = []
        
        for fixture in fixtures:
            try:
                home_team = fixture.get('match_hometeam_name', '')
                away_team = fixture.get('match_awayteam_name', '')
                
                if not home_team or not away_team:
                    continue
                
                fixture_info = {
                    'fixture_id': fixture.get('match_id'),
                    'home_team': home_team,
                    'away_team': away_team,
                    'league': fixture.get('league_name', ''),
                    'date': fixture.get('match_date', ''),
                    'time': fixture.get('match_time', '')
                }
                
                fixture_data.append(fixture_info)
                
            except Exception as e:
                logger.warning(f"⚠️  Error processing fixture: {e}")
                continue
        
        if not fixture_data:
            logger.warning("⚠️  No valid fixtures to process")
            return pd.DataFrame()
        
        df = pd.DataFrame(fixture_data)
        
        # Encode teams using the trained encoders
        if 'teams' in self.encoders:
            teams_encoder = self.encoders['teams']
            
            # Handle unknown teams
            known_teams = set(teams_encoder.classes_)
            
            def encode_team_safe(team_name):
                if team_name in known_teams:
                    return teams_encoder.transform([team_name])[0]
                else:
                    # Use a default encoding for unknown teams
                    return 0  # or len(teams_encoder.classes_)
            
            df['home_team_encoded'] = df['home_team'].apply(encode_team_safe)
            df['away_team_encoded'] = df['away_team'].apply(encode_team_safe)
            
            logger.info(f"✅ Encoded {len(df)} fixtures")
        else:
            logger.warning("⚠️  No team encoder available")
            return pd.DataFrame()
        
        return df
    
    def generate_predictions(self, fixtures_df: pd.DataFrame) -> Dict[str, Any]:
        """Generate predictions for fixtures using optimal models."""
        logger.info("🎯 Generating predictions with optimal models...")
        
        if fixtures_df.empty:
            return {'status': 'failed', 'error': 'No fixtures to predict'}
        
        predictions = []
        
        for idx, fixture in fixtures_df.iterrows():
            try:
                fixture_predictions = {
                    'fixture_id': fixture['fixture_id'],
                    'home_team': fixture['home_team'],
                    'away_team': fixture['away_team'],
                    'league': fixture['league'],
                    'date': fixture['date'],
                    'time': fixture['time'],
                    'predictions': {}
                }
                
                # Prepare features for this fixture
                X = fixture[self.feature_columns].values.reshape(1, -1)
                
                # Generate predictions for each prediction type
                for prediction_type, models in self.models.items():
                    fixture_predictions['predictions'][prediction_type] = {}
                    
                    for model_type, model in models.items():
                        try:
                            # Get prediction and probability
                            pred = model.predict(X)[0]
                            
                            if hasattr(model, 'predict_proba'):
                                proba = model.predict_proba(X)[0]
                                confidence = np.max(proba) * 100
                            else:
                                confidence = 60.0  # Default confidence
                            
                            # Format prediction based on type
                            if prediction_type == 'match_result':
                                pred_text = {'H': 'Home Win', 'D': 'Draw', 'A': 'Away Win'}.get(pred, str(pred))
                            elif prediction_type == 'btts':
                                pred_text = 'Yes' if pred == 1 else 'No'
                            elif prediction_type == 'over_2_5':
                                pred_text = 'Over 2.5' if pred == 1 else 'Under 2.5'
                            elif prediction_type in ['clean_sheet_home', 'clean_sheet_away']:
                                pred_text = 'Yes' if pred == 1 else 'No'
                            else:
                                pred_text = str(pred)
                            
                            fixture_predictions['predictions'][prediction_type][model_type] = {
                                'prediction': pred_text,
                                'confidence': round(confidence, 1),
                                'raw_prediction': pred
                            }
                            
                        except Exception as e:
                            logger.warning(f"⚠️  Error with {prediction_type} {model_type}: {e}")
                            continue
                
                predictions.append(fixture_predictions)
                
            except Exception as e:
                logger.warning(f"⚠️  Error predicting fixture {fixture.get('fixture_id')}: {e}")
                continue
        
        logger.info(f"✅ Generated predictions for {len(predictions)} fixtures")
        
        return {
            'status': 'success',
            'total_fixtures': len(predictions),
            'predictions': predictions
        }
    
    def analyze_predictions(self, predictions_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the prediction results."""
        logger.info("📊 Analyzing prediction results...")
        
        if predictions_result['status'] != 'success':
            return {'status': 'failed', 'error': 'No predictions to analyze'}
        
        predictions = predictions_result['predictions']
        
        analysis = {
            'total_fixtures': len(predictions),
            'prediction_types': {},
            'model_performance': {},
            'confidence_distribution': {},
            'sample_predictions': predictions[:5]  # First 5 for display
        }
        
        # Analyze by prediction type
        for prediction_type in ['match_result', 'btts', 'over_2_5', 'clean_sheet_home', 'clean_sheet_away']:
            type_analysis = {
                'total_predictions': 0,
                'model_consensus': 0,
                'avg_confidence': 0,
                'prediction_distribution': {}
            }
            
            confidences = []
            predictions_by_model = {}
            
            for fixture_pred in predictions:
                if prediction_type in fixture_pred['predictions']:
                    type_analysis['total_predictions'] += 1
                    
                    for model_type, pred_data in fixture_pred['predictions'][prediction_type].items():
                        if model_type not in predictions_by_model:
                            predictions_by_model[model_type] = []
                        
                        predictions_by_model[model_type].append(pred_data['prediction'])
                        confidences.append(pred_data['confidence'])
                        
                        # Count prediction distribution
                        pred_text = pred_data['prediction']
                        if pred_text not in type_analysis['prediction_distribution']:
                            type_analysis['prediction_distribution'][pred_text] = 0
                        type_analysis['prediction_distribution'][pred_text] += 1
            
            if confidences:
                type_analysis['avg_confidence'] = round(np.mean(confidences), 1)
                type_analysis['min_confidence'] = round(np.min(confidences), 1)
                type_analysis['max_confidence'] = round(np.max(confidences), 1)
            
            analysis['prediction_types'][prediction_type] = type_analysis
        
        return analysis
    
    def run_model_test(self) -> Dict[str, Any]:
        """Run complete model test with today's fixtures."""
        logger.info("🚀 Starting optimal model test...")
        
        # Get today's fixtures
        fixtures = self.get_todays_fixtures()
        
        if not fixtures:
            return {'status': 'failed', 'error': 'No fixtures available for testing'}
        
        # Prepare features
        fixtures_df = self.prepare_fixture_features(fixtures)
        
        if fixtures_df.empty:
            return {'status': 'failed', 'error': 'Failed to prepare fixture features'}
        
        # Generate predictions
        predictions_result = self.generate_predictions(fixtures_df)
        
        if predictions_result['status'] != 'success':
            return predictions_result
        
        # Analyze results
        analysis = self.analyze_predictions(predictions_result)
        
        return {
            'status': 'success',
            'test_date': dt.now().isoformat(),
            'fixtures_processed': len(fixtures),
            'predictions_generated': predictions_result['total_fixtures'],
            'predictions': predictions_result['predictions'],
            'analysis': analysis
        }


def main():
    """Main execution function."""
    print("🧪 OPTIMAL MODEL TESTING")
    print("=" * 50)
    print("Testing newly trained optimal models with today's fixtures")
    print()
    
    tester = OptimalModelTester()
    
    # Run the test
    result = tester.run_model_test()
    
    print("📊 TEST RESULTS")
    print("=" * 50)
    
    if result['status'] == 'success':
        print(f"✅ Status: {result['status'].upper()}")
        print(f"📅 Test Date: {result['test_date']}")
        print(f"🏈 Fixtures Processed: {result['fixtures_processed']}")
        print(f"🎯 Predictions Generated: {result['predictions_generated']}")
        
        analysis = result['analysis']
        
        print(f"\n📈 PREDICTION ANALYSIS:")
        for pred_type, type_analysis in analysis['prediction_types'].items():
            if type_analysis['total_predictions'] > 0:
                print(f"\n  {pred_type.upper().replace('_', ' ')}:")
                print(f"    Total Predictions: {type_analysis['total_predictions']}")
                print(f"    Avg Confidence: {type_analysis['avg_confidence']}%")
                print(f"    Confidence Range: {type_analysis['min_confidence']}% - {type_analysis['max_confidence']}%")
                
                print(f"    Prediction Distribution:")
                for pred_value, count in type_analysis['prediction_distribution'].items():
                    percentage = (count / type_analysis['total_predictions']) * 100
                    print(f"      {pred_value}: {count} ({percentage:.1f}%)")
        
        print(f"\n🎯 SAMPLE PREDICTIONS:")
        for i, sample in enumerate(analysis['sample_predictions'], 1):
            print(f"\n  {i}. {sample['home_team']} vs {sample['away_team']}")
            print(f"     League: {sample['league']}")
            print(f"     Date: {sample['date']} {sample['time']}")
            
            # Show best predictions from each type
            for pred_type, predictions in sample['predictions'].items():
                if predictions:
                    # Get the prediction with highest confidence
                    best_pred = max(predictions.items(), key=lambda x: x[1]['confidence'])
                    model_name, pred_data = best_pred
                    
                    print(f"     {pred_type.replace('_', ' ').title()}: {pred_data['prediction']} ({pred_data['confidence']}% - {model_name})")
    
    else:
        print(f"❌ Status: {result['status'].upper()}")
        print(f"📝 Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
