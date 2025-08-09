#!/usr/bin/env python3
"""
Unified Football Prediction Pipeline
===================================

This is the single, comprehensive pipeline that consolidates all football prediction
functionality into one streamlined system:

1. Uses optimal models trained on 126k+ matches (GitHub 2015-2022 + APIFootball 2022-2025)
2. Applies strict filtering criteria (confidence ≥75%, risk level 'very_low'/'low' only)
3. Categorizes predictions by odds ranges (2.0, 5.0, 10.0, 20.0)
4. Generates predictions for all types: match results, BTTS, over/under, clean sheets
5. Builds accumulators automatically with comprehensive metadata
6. Provides ready-to-use accumulator recommendations for betting

This replaces all fragmented approaches with one cohesive system.
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
import itertools
from dataclasses import dataclass, asdict
import joblib

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config import settings
from utils.common import setup_logging
from daily_fixture_manager import DailyFixtureManager

# Set up logging
logger = setup_logging(__name__)

@dataclass
class PredictionResult:
    """Structured prediction result with metadata."""
    fixture_id: str
    home_team: str
    away_team: str
    league: str
    match_date: str
    match_time: str
    prediction_type: str
    prediction: str
    confidence: float
    model_used: str
    risk_level: str
    odds_category: str
    raw_prediction: Any = None

@dataclass
class AccumulatorBet:
    """Structured accumulator bet with metadata."""
    accumulator_id: str
    odds_category: str
    predictions: List[PredictionResult]
    total_confidence: float
    avg_confidence: float
    min_confidence: float
    risk_level: str
    estimated_odds: float
    num_selections: int
    leagues_covered: List[str]
    prediction_types_covered: List[str]
    created_at: str

class UnifiedPredictionPipeline:
    """
    Unified Football Prediction Pipeline
    
    The single, comprehensive system for football predictions that:
    - Uses optimal models trained on 126k+ matches
    - Applies strict filtering criteria
    - Categorizes by odds ranges
    - Builds accumulators automatically
    """
    
    def __init__(self):
        """Initialize the unified prediction pipeline."""
        self.models_dir = "models"
        self.optimal_models = {}
        self.encoders = {}
        self.feature_columns = ['home_team_encoded', 'away_team_encoded']
        
        # Strict filtering criteria (as per user preferences)
        self.min_confidence = 75.0  # Minimum 75% confidence
        self.allowed_risk_levels = ['very_low', 'low']  # Only very low and low risk
        
        # Odds categories for accumulator building
        self.odds_categories = {
            '2.0': {'min_odds': 1.5, 'max_odds': 2.5, 'target_selections': 3},
            '5.0': {'min_odds': 2.0, 'max_odds': 7.5, 'target_selections': 4},
            '10.0': {'min_odds': 5.0, 'max_odds': 15.0, 'target_selections': 5},
            '20.0': {'min_odds': 10.0, 'max_odds': 30.0, 'target_selections': 6}
        }
        
        # Prediction types and their configurations
        self.prediction_types = {
            'match_result': {
                'models': ['lightgbm', 'neural_network', 'random_forest'],
                'risk_mapping': {
                    'Home Win': 'low',
                    'Away Win': 'medium', 
                    'Draw': 'high'
                },
                'odds_mapping': {
                    'Home Win': 2.2,
                    'Away Win': 3.5,
                    'Draw': 3.8
                }
            },
            'btts': {
                'models': ['xgboost', 'lightgbm', 'neural_network', 'random_forest'],
                'risk_mapping': {
                    'Yes': 'low',
                    'No': 'very_low'
                },
                'odds_mapping': {
                    'Yes': 2.0,
                    'No': 1.8
                }
            },
            'over_2_5': {
                'models': ['xgboost', 'lightgbm', 'neural_network', 'random_forest'],
                'risk_mapping': {
                    'Over 2.5': 'low',
                    'Under 2.5': 'very_low'
                },
                'odds_mapping': {
                    'Over 2.5': 2.1,
                    'Under 2.5': 1.7
                }
            },
            'clean_sheet_home': {
                'models': ['xgboost', 'lightgbm'],
                'risk_mapping': {
                    'Yes': 'medium',
                    'No': 'very_low'
                },
                'odds_mapping': {
                    'Yes': 4.0,
                    'No': 1.3
                }
            },
            'clean_sheet_away': {
                'models': ['xgboost', 'lightgbm'],
                'risk_mapping': {
                    'Yes': 'high',
                    'No': 'very_low'
                },
                'odds_mapping': {
                    'Yes': 5.0,
                    'No': 1.2
                }
            }
        }
        
        # Load optimal models
        self.load_optimal_models()
    
    def load_optimal_models(self):
        """Load all optimal models and encoders."""
        logger.info("🤖 Loading optimal models and encoders...")
        
        # Load encoders
        encoders_file = f"{self.models_dir}/optimal_encoders.pkl"
        if os.path.exists(encoders_file):
            with open(encoders_file, 'rb') as f:
                self.encoders = pickle.load(f)
            logger.info("✅ Loaded optimal encoders")
        else:
            raise FileNotFoundError("❌ Optimal encoders not found. Please run optimal training first.")
        
        # Load training metadata
        metadata_file = f"{self.models_dir}/optimal_training_metadata.pkl"
        if os.path.exists(metadata_file):
            with open(metadata_file, 'rb') as f:
                metadata = pickle.load(f)
            
            logger.info(f"📊 Optimal models metadata:")
            logger.info(f"   Training date: {metadata.get('training_date')}")
            logger.info(f"   Data range: {metadata.get('data_range')}")
            logger.info(f"   Total matches: {metadata.get('total_matches'):,}")
            logger.info(f"   Models trained: {metadata.get('models_trained')}")
        
        # Load individual optimal models
        models_loaded = 0
        for prediction_type, config in self.prediction_types.items():
            self.optimal_models[prediction_type] = {}
            
            for model_type in config['models']:
                model_file = f"{self.models_dir}/optimal_{model_type}_{prediction_type}.pkl"
                
                if os.path.exists(model_file):
                    try:
                        model = joblib.load(model_file)
                        self.optimal_models[prediction_type][model_type] = model
                        models_loaded += 1
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to load {model_file}: {e}")
                else:
                    logger.warning(f"⚠️  Model file not found: {model_file}")
        
        logger.info(f"✅ Loaded {models_loaded} optimal models")
        
        if models_loaded == 0:
            raise RuntimeError("❌ No optimal models loaded. Please run optimal training first.")
    
    def get_daily_fixtures(self) -> List[Dict]:
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
        """Prepare features for fixtures using optimal encoders."""
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
        
        # Encode teams using the optimal encoders
        if 'teams' in self.encoders:
            teams_encoder = self.encoders['teams']
            known_teams = set(teams_encoder.classes_)
            
            def encode_team_safe(team_name):
                if team_name in known_teams:
                    return teams_encoder.transform([team_name])[0]
                else:
                    return 0  # Default encoding for unknown teams
            
            df['home_team_encoded'] = df['home_team'].apply(encode_team_safe)
            df['away_team_encoded'] = df['away_team'].apply(encode_team_safe)
            
            logger.info(f"✅ Encoded {len(df)} fixtures")
        else:
            logger.warning("⚠️  No team encoder available")
            return pd.DataFrame()
        
        return df

    def generate_predictions(self, fixtures_df: pd.DataFrame) -> List[PredictionResult]:
        """Generate predictions for all fixtures using optimal models."""
        logger.info("🎯 Generating predictions with optimal models...")

        if fixtures_df.empty:
            return []

        all_predictions = []

        for idx, fixture in fixtures_df.iterrows():
            try:
                # Prepare features for this fixture
                X = fixture[self.feature_columns].values.reshape(1, -1)

                # Generate predictions for each prediction type
                for prediction_type, config in self.prediction_types.items():
                    if prediction_type not in self.optimal_models:
                        continue

                    best_prediction = None
                    best_confidence = 0
                    best_model = None

                    # Try all available models for this prediction type
                    for model_type, model in self.optimal_models[prediction_type].items():
                        try:
                            # Get prediction and probability
                            pred = model.predict(X)[0]

                            if hasattr(model, 'predict_proba'):
                                proba = model.predict_proba(X)[0]
                                confidence = np.max(proba) * 100
                            else:
                                confidence = 60.0  # Default confidence

                            # Keep the prediction with highest confidence
                            if confidence > best_confidence:
                                best_confidence = confidence
                                best_prediction = pred
                                best_model = model_type

                        except Exception as e:
                            logger.warning(f"⚠️  Error with {prediction_type} {model_type}: {e}")
                            continue

                    if best_prediction is not None:
                        # Format prediction based on type
                        if prediction_type == 'match_result':
                            pred_text = {'H': 'Home Win', 'D': 'Draw', 'A': 'Away Win'}.get(best_prediction, str(best_prediction))
                        elif prediction_type == 'btts':
                            pred_text = 'Yes' if best_prediction == 1 else 'No'
                        elif prediction_type == 'over_2_5':
                            pred_text = 'Over 2.5' if best_prediction == 1 else 'Under 2.5'
                        elif prediction_type in ['clean_sheet_home', 'clean_sheet_away']:
                            pred_text = 'Yes' if best_prediction == 1 else 'No'
                        else:
                            pred_text = str(best_prediction)

                        # Get risk level and odds
                        risk_level = config['risk_mapping'].get(pred_text, 'medium')
                        estimated_odds = config['odds_mapping'].get(pred_text, 2.0)

                        # Determine odds category
                        odds_category = self.categorize_by_odds(estimated_odds)

                        # Create prediction result
                        prediction_result = PredictionResult(
                            fixture_id=str(fixture['fixture_id']),
                            home_team=fixture['home_team'],
                            away_team=fixture['away_team'],
                            league=fixture['league'],
                            match_date=fixture['date'],
                            match_time=fixture['time'],
                            prediction_type=prediction_type,
                            prediction=pred_text,
                            confidence=round(best_confidence, 1),
                            model_used=best_model,
                            risk_level=risk_level,
                            odds_category=odds_category,
                            raw_prediction=best_prediction
                        )

                        all_predictions.append(prediction_result)

            except Exception as e:
                logger.warning(f"⚠️  Error predicting fixture {fixture.get('fixture_id')}: {e}")
                continue

        logger.info(f"✅ Generated {len(all_predictions)} total predictions")
        return all_predictions

    def categorize_by_odds(self, odds: float) -> str:
        """Categorize prediction by odds range."""
        for category, config in self.odds_categories.items():
            if config['min_odds'] <= odds <= config['max_odds']:
                return category
        return '2.0'  # Default category

    def apply_strict_filtering(self, predictions: List[PredictionResult]) -> List[PredictionResult]:
        """Apply strict filtering criteria: confidence ≥75%, risk level 'very_low'/'low' only."""
        logger.info("🔍 Applying strict filtering criteria...")

        filtered_predictions = []

        for prediction in predictions:
            # Check confidence threshold
            if prediction.confidence < self.min_confidence:
                continue

            # Check risk level
            if prediction.risk_level not in self.allowed_risk_levels:
                continue

            filtered_predictions.append(prediction)

        logger.info(f"✅ Filtered to {len(filtered_predictions)} high-quality predictions")
        logger.info(f"   (from {len(predictions)} total predictions)")

        return filtered_predictions

    def build_accumulators(self, filtered_predictions: List[PredictionResult]) -> List[AccumulatorBet]:
        """Build accumulators automatically by odds categories."""
        logger.info("🎰 Building accumulators by odds categories...")

        # Group predictions by odds category
        predictions_by_category = {}
        for prediction in filtered_predictions:
            category = prediction.odds_category
            if category not in predictions_by_category:
                predictions_by_category[category] = []
            predictions_by_category[category].append(prediction)

        accumulators = []

        for category, category_predictions in predictions_by_category.items():
            if len(category_predictions) < self.odds_categories[category]['target_selections']:
                logger.info(f"⚠️  Not enough predictions for {category} category: {len(category_predictions)} < {self.odds_categories[category]['target_selections']}")
                continue

            # Create accumulator combinations
            target_selections = self.odds_categories[category]['target_selections']

            # Generate combinations of the target size
            for combo in itertools.combinations(category_predictions, target_selections):
                accumulator = self.create_accumulator(category, list(combo))
                if accumulator:
                    accumulators.append(accumulator)

            # Also create smaller combinations if we have many predictions
            if len(category_predictions) >= target_selections + 2:
                for combo in itertools.combinations(category_predictions, target_selections - 1):
                    accumulator = self.create_accumulator(category, list(combo))
                    if accumulator:
                        accumulators.append(accumulator)

        # Sort accumulators by confidence and limit to best ones
        accumulators.sort(key=lambda x: x.avg_confidence, reverse=True)

        logger.info(f"✅ Built {len(accumulators)} accumulator combinations")

        return accumulators[:20]  # Return top 20 accumulators

    def create_accumulator(self, category: str, predictions: List[PredictionResult]) -> Optional[AccumulatorBet]:
        """Create a single accumulator bet from predictions."""
        if not predictions:
            return None

        # Calculate confidence metrics
        confidences = [p.confidence for p in predictions]
        total_confidence = sum(confidences)
        avg_confidence = total_confidence / len(predictions)
        min_confidence = min(confidences)

        # Ensure minimum confidence threshold
        if min_confidence < self.min_confidence:
            return None

        # Calculate estimated odds (simplified)
        estimated_odds = 1.0
        for prediction in predictions:
            pred_odds = self.prediction_types[prediction.prediction_type]['odds_mapping'].get(prediction.prediction, 2.0)
            estimated_odds *= pred_odds

        # Determine overall risk level
        risk_levels = [p.risk_level for p in predictions]
        if all(r == 'very_low' for r in risk_levels):
            overall_risk = 'very_low'
        elif all(r in ['very_low', 'low'] for r in risk_levels):
            overall_risk = 'low'
        else:
            return None  # Don't create accumulator with higher risk

        # Get metadata
        leagues_covered = list(set(p.league for p in predictions))
        prediction_types_covered = list(set(p.prediction_type for p in predictions))

        accumulator_id = f"{category}_{dt.now().strftime('%Y%m%d_%H%M%S')}_{len(predictions)}sel"

        return AccumulatorBet(
            accumulator_id=accumulator_id,
            odds_category=category,
            predictions=predictions,
            total_confidence=round(total_confidence, 1),
            avg_confidence=round(avg_confidence, 1),
            min_confidence=round(min_confidence, 1),
            risk_level=overall_risk,
            estimated_odds=round(estimated_odds, 2),
            num_selections=len(predictions),
            leagues_covered=leagues_covered,
            prediction_types_covered=prediction_types_covered,
            created_at=dt.now().isoformat()
        )

    def run_unified_pipeline(self) -> Dict[str, Any]:
        """Run the complete unified prediction pipeline."""
        logger.info("🚀 Starting Unified Football Prediction Pipeline...")
        logger.info("=" * 60)
        logger.info("🎯 COMPREHENSIVE FOOTBALL PREDICTION SYSTEM")
        logger.info("📊 Using optimal models trained on 126k+ matches")
        logger.info("🔍 Applying strict filtering: confidence ≥75%, risk 'very_low'/'low'")
        logger.info("🎰 Building accumulators by odds categories (2.0, 5.0, 10.0, 20.0)")
        logger.info("=" * 60)

        pipeline_start = dt.now()

        try:
            # Step 1: Get today's fixtures
            fixtures = self.get_daily_fixtures()
            if not fixtures:
                return {'status': 'failed', 'error': 'No fixtures available'}

            # Step 2: Prepare features
            fixtures_df = self.prepare_fixture_features(fixtures)
            if fixtures_df.empty:
                return {'status': 'failed', 'error': 'Failed to prepare fixture features'}

            # Step 3: Generate predictions
            all_predictions = self.generate_predictions(fixtures_df)
            if not all_predictions:
                return {'status': 'failed', 'error': 'No predictions generated'}

            # Step 4: Apply strict filtering
            filtered_predictions = self.apply_strict_filtering(all_predictions)
            if not filtered_predictions:
                return {'status': 'failed', 'error': 'No predictions passed strict filtering'}

            # Step 5: Build accumulators
            accumulators = self.build_accumulators(filtered_predictions)

            # Step 6: Generate comprehensive report
            pipeline_end = dt.now()
            execution_time = (pipeline_end - pipeline_start).total_seconds()

            report = self.generate_comprehensive_report(
                fixtures, all_predictions, filtered_predictions, accumulators, execution_time
            )

            logger.info("✅ Unified pipeline completed successfully!")
            logger.info(f"⏱️  Total execution time: {execution_time:.1f} seconds")

            return {
                'status': 'success',
                'execution_time_seconds': execution_time,
                'pipeline_results': report,
                'accumulators': [asdict(acc) for acc in accumulators],
                'filtered_predictions': [asdict(pred) for pred in filtered_predictions],
                'all_predictions': [asdict(pred) for pred in all_predictions]
            }

        except Exception as e:
            logger.error(f"❌ Pipeline failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}

    def generate_comprehensive_report(self, fixtures: List[Dict], all_predictions: List[PredictionResult],
                                    filtered_predictions: List[PredictionResult], accumulators: List[AccumulatorBet],
                                    execution_time: float) -> Dict[str, Any]:
        """Generate comprehensive pipeline report."""

        # Basic statistics
        total_fixtures = len(fixtures)
        total_predictions = len(all_predictions)
        filtered_count = len(filtered_predictions)
        accumulator_count = len(accumulators)

        # Filtering statistics
        filter_rate = (filtered_count / total_predictions * 100) if total_predictions > 0 else 0

        # Prediction type breakdown
        pred_type_breakdown = {}
        for pred in filtered_predictions:
            pred_type = pred.prediction_type
            if pred_type not in pred_type_breakdown:
                pred_type_breakdown[pred_type] = {'count': 0, 'avg_confidence': 0, 'confidences': []}
            pred_type_breakdown[pred_type]['count'] += 1
            pred_type_breakdown[pred_type]['confidences'].append(pred.confidence)

        # Calculate averages
        for pred_type, data in pred_type_breakdown.items():
            data['avg_confidence'] = round(sum(data['confidences']) / len(data['confidences']), 1)
            data['min_confidence'] = round(min(data['confidences']), 1)
            data['max_confidence'] = round(max(data['confidences']), 1)
            del data['confidences']  # Remove raw data

        # Odds category breakdown
        odds_breakdown = {}
        for pred in filtered_predictions:
            category = pred.odds_category
            if category not in odds_breakdown:
                odds_breakdown[category] = 0
            odds_breakdown[category] += 1

        # Accumulator statistics
        accumulator_stats = {}
        if accumulators:
            for acc in accumulators:
                category = acc.odds_category
                if category not in accumulator_stats:
                    accumulator_stats[category] = {
                        'count': 0,
                        'avg_confidence': 0,
                        'avg_odds': 0,
                        'confidences': [],
                        'odds': []
                    }
                accumulator_stats[category]['count'] += 1
                accumulator_stats[category]['confidences'].append(acc.avg_confidence)
                accumulator_stats[category]['odds'].append(acc.estimated_odds)

            # Calculate averages
            for category, data in accumulator_stats.items():
                data['avg_confidence'] = round(sum(data['confidences']) / len(data['confidences']), 1)
                data['avg_odds'] = round(sum(data['odds']) / len(data['odds']), 2)
                del data['confidences']
                del data['odds']

        # Risk level distribution
        risk_distribution = {}
        for pred in filtered_predictions:
            risk = pred.risk_level
            if risk not in risk_distribution:
                risk_distribution[risk] = 0
            risk_distribution[risk] += 1

        return {
            'pipeline_summary': {
                'execution_time_seconds': round(execution_time, 1),
                'total_fixtures_processed': total_fixtures,
                'total_predictions_generated': total_predictions,
                'predictions_after_filtering': filtered_count,
                'filter_success_rate_percent': round(filter_rate, 1),
                'accumulators_built': accumulator_count
            },
            'prediction_breakdown': pred_type_breakdown,
            'odds_category_breakdown': odds_breakdown,
            'risk_level_distribution': risk_distribution,
            'accumulator_statistics': accumulator_stats,
            'top_accumulators': [asdict(acc) for acc in accumulators[:5]],  # Top 5 accumulators
            'filtering_criteria': {
                'min_confidence_percent': self.min_confidence,
                'allowed_risk_levels': self.allowed_risk_levels,
                'odds_categories': self.odds_categories
            }
        }

    def save_results(self, results: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Save pipeline results to JSON file."""
        if filename is None:
            timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
            filename = f"unified_predictions_{timestamp}.json"

        filepath = os.path.join("results", filename)
        os.makedirs("results", exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"💾 Results saved to: {filepath}")
        return filepath


def main():
    """Main execution function with comprehensive reporting."""
    import argparse

    parser = argparse.ArgumentParser(description='Unified Football Prediction Pipeline')
    parser.add_argument('--save-results', action='store_true', help='Save results to JSON file')
    parser.add_argument('--show-details', action='store_true', help='Show detailed prediction breakdown')
    parser.add_argument('--min-confidence', type=float, default=75.0, help='Minimum confidence threshold')

    args = parser.parse_args()

    print("🚀 UNIFIED FOOTBALL PREDICTION PIPELINE")
    print("=" * 80)
    print("🎯 Comprehensive Football Prediction System")
    print("📊 Using optimal models trained on 126k+ matches")
    print("🔍 Strict filtering: confidence ≥75%, risk 'very_low'/'low' only")
    print("🎰 Automatic accumulator building by odds categories")
    print("=" * 80)
    print()

    try:
        # Initialize pipeline
        pipeline = UnifiedPredictionPipeline()

        # Override confidence threshold if specified
        if args.min_confidence != 75.0:
            pipeline.min_confidence = args.min_confidence
            print(f"🔧 Using custom confidence threshold: {args.min_confidence}%")

        # Run the unified pipeline
        results = pipeline.run_unified_pipeline()

        if results['status'] == 'success':
            report = results['pipeline_results']
            accumulators = results['accumulators']

            print("📊 PIPELINE EXECUTION SUMMARY")
            print("=" * 50)
            summary = report['pipeline_summary']
            print(f"⏱️  Execution Time: {summary['execution_time_seconds']} seconds")
            print(f"🏈 Fixtures Processed: {summary['total_fixtures_processed']}")
            print(f"🎯 Total Predictions: {summary['total_predictions_generated']}")
            print(f"✅ Filtered Predictions: {summary['predictions_after_filtering']}")
            print(f"📈 Filter Success Rate: {summary['filter_success_rate_percent']}%")
            print(f"🎰 Accumulators Built: {summary['accumulators_built']}")

            print(f"\n📈 PREDICTION TYPE BREAKDOWN")
            print("-" * 40)
            for pred_type, data in report['prediction_breakdown'].items():
                print(f"{pred_type.upper().replace('_', ' ')}: {data['count']} predictions")
                print(f"  Avg Confidence: {data['avg_confidence']}%")
                print(f"  Range: {data['min_confidence']}% - {data['max_confidence']}%")

            print(f"\n🎯 ODDS CATEGORY DISTRIBUTION")
            print("-" * 40)
            for category, count in report['odds_category_breakdown'].items():
                print(f"Category {category}: {count} predictions")

            print(f"\n🛡️  RISK LEVEL DISTRIBUTION")
            print("-" * 40)
            for risk, count in report['risk_level_distribution'].items():
                print(f"{risk.upper()}: {count} predictions")

            if accumulators:
                print(f"\n🏆 TOP ACCUMULATOR RECOMMENDATIONS")
                print("=" * 50)

                for i, acc in enumerate(accumulators[:5], 1):
                    print(f"\n{i}. ACCUMULATOR {acc['accumulator_id']}")
                    print(f"   Category: {acc['odds_category']} | Selections: {acc['num_selections']}")
                    print(f"   Confidence: {acc['avg_confidence']}% (min: {acc['min_confidence']}%)")
                    print(f"   Risk Level: {acc['risk_level'].upper()}")
                    print(f"   Estimated Odds: {acc['estimated_odds']}")
                    print(f"   Leagues: {', '.join(acc['leagues_covered'][:3])}{'...' if len(acc['leagues_covered']) > 3 else ''}")

                    if args.show_details:
                        print(f"   Predictions:")
                        for pred in acc['predictions']:
                            print(f"     • {pred['home_team']} vs {pred['away_team']}")
                            print(f"       {pred['prediction_type'].replace('_', ' ').title()}: {pred['prediction']} ({pred['confidence']}%)")

            # Save results if requested
            if args.save_results:
                filepath = pipeline.save_results(results)
                print(f"\n💾 Results saved to: {filepath}")

            print(f"\n✅ PIPELINE COMPLETED SUCCESSFULLY!")
            print(f"🎯 Ready-to-use accumulator recommendations generated")
            print(f"📊 All predictions meet strict filtering criteria")

        else:
            print(f"❌ PIPELINE FAILED")
            print(f"Error: {results.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
