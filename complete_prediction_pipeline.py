#!/usr/bin/env python3
"""
Complete Prediction Pipeline
Comprehensive script that:
1. Fetches today's fixtures from APIFootball
2. Checks if models are trained, if not trains them from GitHub data
3. Makes predictions using trained models
4. Stores results in database for frontend consumption

This is the master script that combines all functionality.
"""

import os
import sys
import logging
import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import all required services and modules with error handling
try:
    from services.apifootball_service import APIFootballService
    from services.fixture_cache_service import FixtureCacheService
    from services.daily_predictions_service import DailyPredictionsService, DailyPrediction, DailyPredictionSummary
    # RealMLPredictionService removed - replaced by enhanced pipeline
    from services.accumulator_builder import AccumulatorBuilder
    from ml_pipeline_streamlined import StreamlinedMLPipeline
    from train_models_github_dataset import GitHubDatasetTrainer
    from database import get_db
    from utils.common import setup_logging
    from utils.config import settings
except ImportError as e:
    print(f"❌ Import error: {str(e)}")
    print("💡 Please install missing dependencies:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

# Set up logging
logger = setup_logging(__name__)

class CompletePredictionPipeline:
    """
    Complete prediction pipeline that handles everything from data fetching to predictions.
    """
    
    def __init__(self):
        """Initialize the complete pipeline."""
        self.apifootball_service = APIFootballService()
        self.fixture_cache = FixtureCacheService()
        # self.ml_service = RealMLPredictionService()  # Replaced by enhanced pipeline
        self.accumulator_builder = AccumulatorBuilder()
        self.streamlined_pipeline = StreamlinedMLPipeline()
        self.github_trainer = GitHubDatasetTrainer()

        # Load enhanced models immediately
        self.streamlined_pipeline.load_best_models()

        logger.info("🚀 Complete Prediction Pipeline initialized")
    
    def check_models_availability(self) -> Dict[str, bool]:
        """
        Check if trained models are available.
        
        Returns:
            Dictionary with model availability status
        """
        logger.info("🔍 Checking model availability...")
        
        model_status = {}
        models_dir = Path(settings.ml.MODEL_DIR)
        
        # Define required models
        required_models = {
            'xgboost': ['match_result', 'over_2_5', 'btts', 'clean_sheet_home', 'clean_sheet_away'],
            'lightgbm': ['match_result', 'over_2_5', 'btts', 'clean_sheet_home', 'clean_sheet_away'],
            'neural_network': ['match_result', 'over_2_5', 'btts'],
            'random_forest': ['match_result', 'over_2_5', 'btts']
        }
        
        total_required = 0
        total_available = 0
        
        for model_type, prediction_types in required_models.items():
            model_status[model_type] = {}
            
            for pred_type in prediction_types:
                total_required += 1
                model_path = models_dir / model_type / f"{pred_type}_model.joblib"

                if model_path.exists():
                    model_status[model_type][pred_type] = True
                    total_available += 1
                    logger.info(f"✅ Found {model_type}/{pred_type}")
                else:
                    model_status[model_type][pred_type] = False
                    logger.warning(f"❌ Missing {model_type}/{pred_type} at {model_path}")
        
        availability_percentage = (total_available / total_required) * 100
        logger.info(f"📊 Model availability: {total_available}/{total_required} ({availability_percentage:.1f}%)")
        
        return {
            'models': model_status,
            'total_required': total_required,
            'total_available': total_available,
            'availability_percentage': availability_percentage,
            'sufficient': availability_percentage >= 70  # Consider 70% sufficient
        }
    
    def train_models_if_needed(self, force_retrain: bool = False) -> bool:
        """
        Train models if they're not available or if forced.
        
        Args:
            force_retrain: Force retraining even if models exist
            
        Returns:
            True if training was successful or not needed
        """
        logger.info("🎯 Checking if model training is needed...")
        
        model_status = self.check_models_availability()
        
        if model_status['sufficient'] and not force_retrain:
            logger.info("✅ Sufficient models available, skipping training")
            return True
        
        if force_retrain:
            logger.info("🔄 Force retraining requested")
        else:
            logger.info(f"⚠️  Insufficient models ({model_status['availability_percentage']:.1f}%), training needed")
        
        try:
            logger.info("🚀 Starting model training from GitHub dataset...")
            
            # Use the GitHub dataset trainer
            success = self.github_trainer.train_all_models()
            
            if success:
                logger.info("🎉 Model training completed successfully!")
                
                # Verify models are now available
                new_status = self.check_models_availability()
                if new_status['sufficient']:
                    logger.info("✅ Model training verification passed")
                    return True
                else:
                    logger.error("❌ Model training verification failed")
                    return False
            else:
                logger.error("❌ Model training failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error during model training: {str(e)}")
            return False
    
    def fetch_todays_fixtures(self, date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch today's fixtures from APIFootball with caching to avoid repeated API calls.

        Args:
            date_str: Date in YYYY-MM-DD format (default: today)

        Returns:
            List of fixture dictionaries
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"🌐 Fetching fixtures for {date_str}...")

        # First, try to load from cache
        cached_fixtures = self.fixture_cache.load_fixtures_from_cache(date_str, "apifootball")

        if cached_fixtures is not None:
            logger.info(f"📂 Using cached fixtures: {len(cached_fixtures)} fixtures")

            # Filter for upcoming fixtures only
            upcoming_fixtures = self._filter_upcoming_fixtures(cached_fixtures)
            logger.info(f"📊 Found {len(upcoming_fixtures)} upcoming fixtures from cache")
            return upcoming_fixtures

        # Cache miss - fetch from API
        logger.info(f"🌐 Cache miss - fetching from APIFootball API...")

        try:
            fixtures = self.apifootball_service.get_daily_fixtures(date_str)
            logger.info(f"✅ Fetched {len(fixtures)} fixtures from APIFootball API")

            # Save to cache for future use
            if fixtures:
                cache_success = self.fixture_cache.save_fixtures_to_cache(fixtures, date_str, "apifootball")
                if cache_success:
                    logger.info(f"💾 Cached {len(fixtures)} fixtures for future use")
                else:
                    logger.warning("⚠️  Failed to cache fixtures")

            # Filter for upcoming fixtures only
            upcoming_fixtures = self._filter_upcoming_fixtures(fixtures)
            logger.info(f"📊 Found {len(upcoming_fixtures)} upcoming fixtures")
            return upcoming_fixtures

        except Exception as e:
            logger.error(f"❌ Error fetching fixtures from API: {str(e)}")

            # Try to get cache info for debugging
            cache_info = self.fixture_cache.get_cached_fixtures_info(date_str, "apifootball")
            if cache_info:
                logger.info(f"📋 Cache info: {cache_info['fixture_count']} fixtures cached at {cache_info['cached_at']}")

            return []

    def _filter_upcoming_fixtures(self, fixtures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter fixtures to only include upcoming ones.

        Args:
            fixtures: List of fixture dictionaries

        Returns:
            List of upcoming fixtures
        """
        upcoming_fixtures = []
        current_time = datetime.now()

        for fixture in fixtures:
            try:
                fixture_time = datetime.fromisoformat(fixture.get('date', '').replace('Z', '+00:00'))
                if fixture_time > current_time:
                    upcoming_fixtures.append(fixture)
            except:
                # If we can't parse the time, include it anyway
                upcoming_fixtures.append(fixture)

        return upcoming_fixtures

    def get_cache_status(self) -> Dict[str, Any]:
        """
        Get fixture cache status and statistics.

        Returns:
            Dictionary with cache status information
        """
        logger.info("📊 Getting fixture cache status...")

        try:
            cache_stats = self.fixture_cache.get_cache_stats()
            cached_dates = self.fixture_cache.list_cached_dates()

            # Get info for recent dates
            recent_cache_info = []
            for date in cached_dates[-5:]:  # Last 5 cached dates
                info = self.fixture_cache.get_cached_fixtures_info(date, "apifootball")
                if info:
                    recent_cache_info.append(info)

            return {
                "cache_stats": cache_stats,
                "cached_dates": cached_dates,
                "recent_cache_info": recent_cache_info,
                "total_cached_dates": len(cached_dates)
            }

        except Exception as e:
            logger.error(f"❌ Error getting cache status: {str(e)}")
            return {}

    def clear_fixture_cache(self, date: Optional[str] = None) -> bool:
        """
        Clear fixture cache.

        Args:
            date: Specific date to clear (optional, clears all if None)

        Returns:
            True if successful
        """
        try:
            if date:
                logger.info(f"🗑️  Clearing cache for {date}...")
                self.fixture_cache.clear_cache(date, "apifootball")
            else:
                logger.info("🗑️  Clearing all fixture cache...")
                self.fixture_cache.clear_cache()

            logger.info("✅ Cache cleared successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Error clearing cache: {str(e)}")
            return False
    
    def generate_predictions_for_fixtures(self, fixtures: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate predictions for a list of fixtures.
        
        Args:
            fixtures: List of fixture dictionaries
            
        Returns:
            Dictionary with prediction results
        """
        logger.info(f"🎯 Generating predictions for {len(fixtures)} fixtures...")
        
        all_predictions = []
        successful_predictions = 0
        failed_predictions = 0
        
        for i, fixture in enumerate(fixtures, 1):
            try:
                logger.info(f"{i}/{len(fixtures)}: {fixture.get('home_team', 'Unknown')} vs {fixture.get('away_team', 'Unknown')}")
                
                # Generate ML prediction using the enhanced streamlined pipeline
                prediction_result = self.streamlined_pipeline.predict_single_fixture(fixture)
                
                if 'error' not in prediction_result:
                    all_predictions.append(prediction_result)
                    successful_predictions += 1
                    logger.info(f"✅ Prediction generated successfully")
                else:
                    failed_predictions += 1
                    logger.warning(f"❌ Prediction failed: {prediction_result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                failed_predictions += 1
                logger.error(f"❌ Error generating prediction: {str(e)}")
                continue
        
        logger.info(f"📊 Prediction summary: {successful_predictions} successful, {failed_predictions} failed")
        
        return {
            'predictions': all_predictions,
            'successful_count': successful_predictions,
            'failed_count': failed_predictions,
            'total_fixtures': len(fixtures)
        }
    
    def store_predictions_in_database(self, predictions: List[Dict[str, Any]], target_date: str) -> bool:
        """
        Store predictions in database for frontend consumption.
        
        Args:
            predictions: List of prediction dictionaries
            target_date: Date string in YYYY-MM-DD format
            
        Returns:
            True if storage was successful
        """
        logger.info(f"💾 Storing {len(predictions)} predictions in database...")
        
        try:
            # Get database session
            db = next(get_db())
            prediction_date = datetime.strptime(target_date, "%Y-%m-%d").date()
            
            # Clear existing predictions for this date
            logger.info("🧹 Clearing existing predictions for the date...")
            db.query(DailyPrediction).filter(
                DailyPrediction.prediction_date == prediction_date
            ).delete()
            
            db.query(DailyPredictionSummary).filter(
                DailyPredictionSummary.prediction_date == prediction_date
            ).delete()
            
            db.commit()
            
            # Store each prediction
            stored_count = 0
            
            for prediction in predictions:
                try:
                    # Extract fixture info
                    fixture_info = prediction.get('fixture_info', {})
                    ml_predictions = prediction.get('predictions', {})
                    
                    # Generate betting categories using accumulator builder
                    betting_categories = self.accumulator_builder.categorize_prediction(prediction)
                    
                    # Create database record
                    db_prediction = DailyPrediction(
                        prediction_date=prediction_date,
                        fixture_id=fixture_info.get('fixture_id', 0),
                        home_team=fixture_info.get('home_team', 'Unknown'),
                        away_team=fixture_info.get('away_team', 'Unknown'),
                        league_name=fixture_info.get('league', 'Unknown'),
                        fixture_date=datetime.fromisoformat(fixture_info.get('date', datetime.now().isoformat())),
                        fixture_status=fixture_info.get('status', 'Not Started'),
                        ml_predictions=json.dumps(ml_predictions),
                        betting_2_odds=json.dumps(betting_categories.get('2_odds', {})),
                        betting_5_odds=json.dumps(betting_categories.get('5_odds', {})),
                        betting_10_odds=json.dumps(betting_categories.get('10_odds', {})),
                        betting_rollover=json.dumps(betting_categories.get('rollover', {})),
                        total_models_used=len(ml_predictions),
                        highest_confidence=max([pred.get('confidence', 0) for pred in ml_predictions.values()] + [0])
                    )
                    
                    db.add(db_prediction)
                    stored_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error storing individual prediction: {str(e)}")
                    continue
            
            # Create summary record
            summary = DailyPredictionSummary(
                prediction_date=prediction_date,
                total_fixtures=len(predictions),
                predictions_generated=stored_count,
                models_used=len(self.streamlined_pipeline.models) if hasattr(self.streamlined_pipeline, 'models') else 0,
                generation_status="completed",  # Set status to completed
                generation_time=datetime.now()
            )
            
            db.add(summary)
            db.commit()
            
            logger.info(f"✅ Successfully stored {stored_count} predictions in database")
            return True

        except Exception as e:
            logger.error(f"❌ Error storing predictions in database: {str(e)}")
            return False

    def run_complete_pipeline(self, date_str: Optional[str] = None, force_retrain: bool = False) -> Dict[str, Any]:
        """
        Run the complete prediction pipeline.

        Args:
            date_str: Date in YYYY-MM-DD format (default: today)
            force_retrain: Force model retraining

        Returns:
            Pipeline execution results
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        logger.info("🚀 Starting Complete Prediction Pipeline")
        logger.info("=" * 60)
        logger.info(f"📅 Target Date: {date_str}")
        logger.info(f"🔄 Force Retrain: {force_retrain}")
        logger.info("=" * 60)

        results = {
            'date': date_str,
            'started_at': datetime.now().isoformat(),
            'steps': {}
        }

        try:
            # Step 1: Check and train models if needed
            logger.info("🎯 STEP 1: Model Training Check")
            logger.info("-" * 40)

            training_success = self.train_models_if_needed(force_retrain)
            results['steps']['model_training'] = {
                'success': training_success,
                'forced': force_retrain
            }

            if not training_success:
                logger.error("❌ Model training failed, cannot proceed")
                results['status'] = 'failed'
                results['error'] = 'Model training failed'
                return results

            # Step 2: Fetch today's fixtures
            logger.info("\n🌐 STEP 2: Fixture Fetching")
            logger.info("-" * 40)

            fixtures = self.fetch_todays_fixtures(date_str)
            results['steps']['fixture_fetching'] = {
                'success': len(fixtures) > 0,
                'fixture_count': len(fixtures)
            }

            if not fixtures:
                logger.warning("⚠️  No fixtures found for the date")
                results['status'] = 'no_fixtures'
                results['message'] = f'No fixtures found for {date_str}'
                return results

            # Step 3: Generate predictions
            logger.info("\n🎯 STEP 3: Prediction Generation")
            logger.info("-" * 40)

            prediction_results = self.generate_predictions_for_fixtures(fixtures)
            results['steps']['prediction_generation'] = {
                'success': prediction_results['successful_count'] > 0,
                'successful_predictions': prediction_results['successful_count'],
                'failed_predictions': prediction_results['failed_count'],
                'total_fixtures': prediction_results['total_fixtures']
            }

            if prediction_results['successful_count'] == 0:
                logger.error("❌ No predictions were generated successfully")
                results['status'] = 'no_predictions'
                results['error'] = 'No predictions generated'
                return results

            # Step 4: Store predictions in database
            logger.info("\n💾 STEP 4: Database Storage")
            logger.info("-" * 40)

            storage_success = self.store_predictions_in_database(
                prediction_results['predictions'],
                date_str
            )
            results['steps']['database_storage'] = {
                'success': storage_success,
                'predictions_stored': len(prediction_results['predictions'])
            }

            if not storage_success:
                logger.error("❌ Failed to store predictions in database")
                results['status'] = 'storage_failed'
                results['error'] = 'Database storage failed'
                return results

            # Success!
            results['status'] = 'success'
            results['completed_at'] = datetime.now().isoformat()
            results['summary'] = {
                'fixtures_processed': len(fixtures),
                'predictions_generated': prediction_results['successful_count'],
                'predictions_stored': len(prediction_results['predictions']),
                'success_rate': f"{(prediction_results['successful_count'] / len(fixtures) * 100):.1f}%"
            }

            logger.info("\n🎉 PIPELINE COMPLETED SUCCESSFULLY!")
            logger.info("=" * 60)
            logger.info(f"📊 Summary:")
            logger.info(f"   Fixtures processed: {results['summary']['fixtures_processed']}")
            logger.info(f"   Predictions generated: {results['summary']['predictions_generated']}")
            logger.info(f"   Success rate: {results['summary']['success_rate']}")
            logger.info(f"🌐 Frontend endpoints now have fresh data:")
            logger.info(f"   GET /api/daily-predictions/today")
            logger.info(f"   GET /api/accumulators/today")
            logger.info("=" * 60)

            return results

        except Exception as e:
            logger.error(f"❌ Pipeline failed with error: {str(e)}")
            results['status'] = 'error'
            results['error'] = str(e)
            results['completed_at'] = datetime.now().isoformat()
            return results


def main():
    """Main function with command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Complete Prediction Pipeline - Fetch fixtures, train models, generate predictions"
    )
    parser.add_argument(
        '--date',
        type=str,
        help='Target date in YYYY-MM-DD format (default: today)'
    )
    parser.add_argument(
        '--force-retrain',
        action='store_true',
        help='Force model retraining even if models exist'
    )
    parser.add_argument(
        '--check-models-only',
        action='store_true',
        help='Only check model availability and exit'
    )
    parser.add_argument(
        '--train-only',
        action='store_true',
        help='Only train models and exit'
    )
    parser.add_argument(
        '--fetch-only',
        action='store_true',
        help='Only fetch fixtures and exit'
    )
    parser.add_argument(
        '--cache-status',
        action='store_true',
        help='Show fixture cache status and exit'
    )
    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Clear fixture cache and exit'
    )
    parser.add_argument(
        '--clear-cache-date',
        type=str,
        help='Clear cache for specific date (YYYY-MM-DD) and exit'
    )

    args = parser.parse_args()

    # Initialize pipeline
    pipeline = CompletePredictionPipeline()

    print("🚀 COMPLETE PREDICTION PIPELINE")
    print("=" * 60)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    try:
        # Handle specific operations
        if args.check_models_only:
            print("🔍 Checking model availability only...")
            status = pipeline.check_models_availability()
            print(f"\n📊 Model Status:")
            print(f"   Available: {status['total_available']}/{status['total_required']}")
            print(f"   Percentage: {status['availability_percentage']:.1f}%")
            print(f"   Sufficient: {'✅ Yes' if status['sufficient'] else '❌ No'}")
            return 0 if status['sufficient'] else 1

        elif args.train_only:
            print("🎯 Training models only...")
            success = pipeline.train_models_if_needed(force_retrain=True)
            print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Model training")
            return 0 if success else 1

        elif args.fetch_only:
            print("🌐 Fetching fixtures only...")
            fixtures = pipeline.fetch_todays_fixtures(args.date)
            print(f"\n📊 Fetched {len(fixtures)} fixtures")
            for i, fixture in enumerate(fixtures[:10], 1):  # Show first 10
                print(f"   {i}. {fixture.get('home_team', 'Unknown')} vs {fixture.get('away_team', 'Unknown')}")
            if len(fixtures) > 10:
                print(f"   ... and {len(fixtures) - 10} more")
            return 0 if fixtures else 1

        elif args.cache_status:
            print("📊 Checking fixture cache status...")
            cache_status = pipeline.get_cache_status()

            if cache_status:
                stats = cache_status.get('cache_stats', {})
                print(f"\n📋 Cache Statistics:")
                print(f"   Total files: {stats.get('total_files', 0)}")
                print(f"   Valid files: {stats.get('valid_files', 0)}")
                print(f"   Expired files: {stats.get('expired_files', 0)}")
                print(f"   Total size: {stats.get('total_size_mb', 0)} MB")
                print(f"   Cache directory: {stats.get('cache_dir', 'Unknown')}")

                cached_dates = cache_status.get('cached_dates', [])
                print(f"\n📅 Cached dates ({len(cached_dates)}):")
                for date in cached_dates[-10:]:  # Show last 10
                    print(f"   • {date}")

                recent_info = cache_status.get('recent_cache_info', [])
                if recent_info:
                    print(f"\n🕒 Recent cache info:")
                    for info in recent_info:
                        status = "✅ Valid" if info['is_valid'] else "❌ Expired"
                        print(f"   • {info['date']}: {info['fixture_count']} fixtures ({status})")

            return 0

        elif args.clear_cache:
            print("🗑️  Clearing all fixture cache...")
            success = pipeline.clear_fixture_cache()
            print(f"{'✅ SUCCESS' if success else '❌ FAILED'}: Cache clearing")
            return 0 if success else 1

        elif args.clear_cache_date:
            print(f"🗑️  Clearing cache for {args.clear_cache_date}...")
            success = pipeline.clear_fixture_cache(args.clear_cache_date)
            print(f"{'✅ SUCCESS' if success else '❌ FAILED'}: Cache clearing for {args.clear_cache_date}")
            return 0 if success else 1

        else:
            # Run complete pipeline
            results = pipeline.run_complete_pipeline(
                date_str=args.date,
                force_retrain=args.force_retrain
            )

            print(f"\n📊 FINAL RESULTS:")
            print(f"Status: {results['status']}")

            if results['status'] == 'success':
                summary = results['summary']
                print(f"✅ SUCCESS!")
                print(f"   Fixtures: {summary['fixtures_processed']}")
                print(f"   Predictions: {summary['predictions_generated']}")
                print(f"   Success Rate: {summary['success_rate']}")
                return 0
            else:
                print(f"❌ FAILED: {results.get('error', 'Unknown error')}")
                return 1

    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
