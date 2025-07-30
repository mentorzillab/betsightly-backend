"""
Enhanced Prediction Caching and Fixture Management Service
Implements comprehensive caching, single daily execution, and analytics tracking.
"""

import logging
import json
import time
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from database import get_db, Base, engine

# Import enhanced schema models
from database_schema_enhanced import (
    CachedFixture, CachedPrediction, PredictionBatch, 
    AccumulatorCache, PredictionAnalytics
)

# Import existing services
from services.apifootball_service import APIFootballService
from ml_pipeline_streamlined import StreamlinedMLPipeline
from services.accumulator_builder import AccumulatorBuilder

logger = logging.getLogger(__name__)

class PredictionCacheService:
    """Enhanced service for prediction caching and fixture management."""
    
    def __init__(self):
        """Initialize the caching service."""
        self.apifootball_service = APIFootballService()
        self.ml_pipeline = StreamlinedMLPipeline()
        self.accumulator_builder = AccumulatorBuilder()
        
        # Create enhanced tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Enhanced prediction cache tables created")
    
    def check_daily_predictions_exist(self, target_date: date) -> bool:
        """Check if predictions already exist for the given date."""
        try:
            db = next(get_db())
            
            # Check if batch exists and is completed
            batch = db.query(PredictionBatch).filter(
                func.date(PredictionBatch.batch_date) == target_date,
                PredictionBatch.status == 'completed'
            ).first()
            
            if batch:
                # Also check if we have actual predictions
                prediction_count = db.query(CachedPrediction).filter(
                    func.date(CachedPrediction.prediction_date) == target_date
                ).count()
                
                logger.info(f"✅ Found existing predictions for {target_date}: {prediction_count} predictions")
                return prediction_count > 0
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking existing predictions: {str(e)}")
            return False
        finally:
            db.close()
    
    def cache_fixtures(self, fixtures: List[Dict], target_date: date) -> List[Dict]:
        """Cache all fetched fixtures to database and return as dictionaries."""
        try:
            db = next(get_db())
            cached_fixture_dicts = []

            for fixture_data in fixtures:
                try:
                    # Check if fixture already exists
                    fixture_id = str(fixture_data.get('fixture_id', ''))
                    existing_fixture = db.query(CachedFixture).filter(
                        CachedFixture.fixture_id == fixture_id
                    ).first()

                    if existing_fixture:
                        # Update existing fixture
                        existing_fixture.status = fixture_data.get('status', 'upcoming')
                        existing_fixture.updated_at = datetime.utcnow()
                        existing_fixture.raw_data = json.dumps(fixture_data)
                    else:
                        # Create new cached fixture
                        cached_fixture = CachedFixture(
                            fixture_id=fixture_id,
                            home_team=fixture_data.get('home_team', ''),
                            away_team=fixture_data.get('away_team', ''),
                            league_name=fixture_data.get('league_name', ''),
                            league_id=str(fixture_data.get('league_id', '')),
                            country=fixture_data.get('country', ''),
                            fixture_date=datetime.fromisoformat(fixture_data.get('date', '').replace('Z', '+00:00')) if fixture_data.get('date') else datetime.utcnow(),
                            status=fixture_data.get('status', 'upcoming'),
                            home_odds=fixture_data.get('home_odds'),
                            draw_odds=fixture_data.get('draw_odds'),
                            away_odds=fixture_data.get('away_odds'),
                            raw_data=json.dumps(fixture_data),
                            api_source='apifootball'
                        )

                        db.add(cached_fixture)

                    # Convert to dict format immediately (while in session)
                    fixture_dict = {
                        'fixture_id': fixture_id,
                        'home_team': fixture_data.get('home_team', ''),
                        'away_team': fixture_data.get('away_team', ''),
                        'league_name': fixture_data.get('league_name', ''),
                        'date': fixture_data.get('date', ''),
                        'status': fixture_data.get('status', 'upcoming'),
                        'home_odds': float(fixture_data.get('home_odds', 2.0)) if fixture_data.get('home_odds') else 2.0,
                        'draw_odds': float(fixture_data.get('draw_odds', 3.0)) if fixture_data.get('draw_odds') else 3.0,
                        'away_odds': float(fixture_data.get('away_odds', 2.0)) if fixture_data.get('away_odds') else 2.0
                    }
                    cached_fixture_dicts.append(fixture_dict)

                except Exception as e:
                    logger.error(f"Error caching fixture {fixture_data.get('fixture_id')}: {str(e)}")
                    continue

            db.commit()
            logger.info(f"✅ Cached {len(cached_fixture_dicts)} fixtures for {target_date}")
            return cached_fixture_dicts

        except Exception as e:
            logger.error(f"Error caching fixtures: {str(e)}")
            db.rollback()
            return []
        finally:
            db.close()
    
    def cache_prediction(self, fixture: CachedFixture, prediction_data: Dict, 
                        prediction_date: datetime, generation_time: float) -> List[CachedPrediction]:
        """Cache individual prediction with full metadata."""
        try:
            db = next(get_db())
            cached_predictions = []
            
            predictions = prediction_data.get('predictions', {})
            
            for pred_type, pred_info in predictions.items():
                try:
                    cached_prediction = CachedPrediction(
                        fixture_id=fixture.fixture_id,
                        prediction_date=prediction_date,
                        prediction_type=pred_type,
                        prediction_value=str(pred_info.get('prediction', '')),
                        confidence=float(pred_info.get('confidence', 0.0)),
                        model_type=pred_info.get('model_type', 'enhanced'),
                        model_name=f"{pred_info.get('model_type', 'enhanced')}/{pred_type}",
                        feature_count=62,
                        feature_version='enhanced_v1',
                        generation_time_ms=generation_time * 1000,  # Convert to milliseconds
                        created_at=datetime.utcnow()
                    )
                    
                    db.add(cached_prediction)
                    cached_predictions.append(cached_prediction)
                    
                except Exception as e:
                    logger.error(f"Error caching prediction {pred_type}: {str(e)}")
                    continue
            
            db.commit()
            return cached_predictions
            
        except Exception as e:
            logger.error(f"Error caching predictions: {str(e)}")
            db.rollback()
            return []
        finally:
            db.close()
    
    def cache_accumulators(self, accumulator_data: Dict, prediction_date: datetime) -> List[AccumulatorCache]:
        """Cache generated accumulator combinations."""
        try:
            db = next(get_db())
            cached_accumulators = []
            
            accumulators = accumulator_data.get('accumulators', {})
            
            for acc_type, acc_info in accumulators.items():
                try:
                    cached_accumulator = AccumulatorCache(
                        prediction_date=prediction_date,
                        accumulator_type=acc_type,
                        is_selected=acc_info.get('selected', False),
                        total_odds=acc_info.get('total_odds'),
                        game_count=len(acc_info.get('games', [])),
                        average_confidence=acc_info.get('average_confidence'),
                        diversity_score=acc_info.get('diversity_score'),
                        risk_level=acc_info.get('risk_level', 'medium'),
                        games_data=json.dumps(acc_info.get('games', [])),
                        selection_reason=acc_info.get('reason', ''),
                        created_at=datetime.utcnow()
                    )
                    
                    db.add(cached_accumulator)
                    cached_accumulators.append(cached_accumulator)
                    
                except Exception as e:
                    logger.error(f"Error caching accumulator {acc_type}: {str(e)}")
                    continue
            
            db.commit()
            logger.info(f"✅ Cached {len(cached_accumulators)} accumulators")
            return cached_accumulators
            
        except Exception as e:
            logger.error(f"Error caching accumulators: {str(e)}")
            db.rollback()
            return []
        finally:
            db.close()

    def generate_and_cache_daily_predictions(self, target_date: str = None,
                                           force_regenerate: bool = False) -> Dict[str, Any]:
        """
        Main method to generate and cache daily predictions with single execution control.

        Args:
            target_date: Date string in YYYY-MM-DD format
            force_regenerate: Override existing predictions if True

        Returns:
            Dict with generation results and statistics
        """
        try:
            # Parse target date
            if target_date:
                prediction_date = datetime.strptime(target_date, '%Y-%m-%d')
                date_obj = prediction_date.date()
            else:
                prediction_date = datetime.now()
                date_obj = prediction_date.date()

            logger.info(f"🚀 Starting prediction generation for {date_obj}")

            # Check if predictions already exist (unless force regenerate)
            if not force_regenerate and self.check_daily_predictions_exist(date_obj):
                logger.info(f"✅ Predictions already exist for {date_obj}, skipping generation")
                return {
                    'status': 'skipped',
                    'message': 'Predictions already exist for this date',
                    'date': str(date_obj),
                    'force_regenerate_available': True
                }

            # Create prediction batch record
            batch = self.create_prediction_batch(prediction_date)

            try:
                # Step 1: Fetch and cache fixtures
                logger.info("📥 Fetching fixtures from APIFootball.com...")
                fixtures = self.apifootball_service.get_daily_fixtures(target_date or str(date_obj))

                if not fixtures:
                    raise Exception("No fixtures found from API")

                # Cache fixtures as backup (returns dict format to avoid session issues)
                cached_fixture_dicts = self.cache_fixtures(fixtures, date_obj)

                # Filter for upcoming fixtures only - CRITICAL: No predictions for finished games
                from datetime import datetime
                upcoming_fixture_dicts = []
                finished_statuses = [
                    'Finished', 'FT', 'finished', 'completed', 'Full Time',
                    'After Pen.', 'AET', 'Postponed', 'Cancelled', 'Abandoned'
                ]

                for f in cached_fixture_dicts:
                    # Check if game is finished by status
                    if f['status'] in finished_statuses:
                        continue

                    # Check if game time has passed (additional safety check)
                    try:
                        game_time = datetime.fromisoformat(f['date'].replace('Z', '+00:00'))
                        if game_time < datetime.now():
                            continue
                    except:
                        pass  # If we can't parse time, include it (better safe than sorry)

                    upcoming_fixture_dicts.append(f)

                logger.info(f"📊 Found {len(fixtures)} total fixtures, {len(upcoming_fixture_dicts)} upcoming")

                # Step 2: Load ML models
                logger.info("🤖 Loading enhanced ML models...")
                models = self.ml_pipeline.load_best_models()
                logger.info(f"✅ Loaded {len(models)} enhanced models")

                # Step 3: Generate predictions for each fixture
                logger.info("🎯 Generating predictions...")
                successful_predictions = 0
                failed_predictions = 0
                all_predictions = []

                for fixture_dict in upcoming_fixture_dicts:
                    try:
                        # Generate prediction with timing
                        start_time = time.time()
                        prediction_result = self.ml_pipeline.predict_single_fixture(fixture_dict)
                        generation_time = time.time() - start_time

                        if 'error' not in prediction_result:
                            # Create a mock cached fixture for the cache_prediction method
                            # We'll need to get the actual cached fixture from database
                            db = next(get_db())
                            try:
                                cached_fixture = db.query(CachedFixture).filter(
                                    CachedFixture.fixture_id == fixture_dict['fixture_id']
                                ).first()

                                if cached_fixture:
                                    # Cache the prediction
                                    cached_preds = self.cache_prediction(
                                        cached_fixture, prediction_result,
                                        prediction_date, generation_time
                                    )

                                    if cached_preds:
                                        successful_predictions += 1
                                        all_predictions.append({
                                            'fixture_dict': fixture_dict,
                                            'predictions': prediction_result.get('predictions', {}),
                                            'cached_predictions': cached_preds
                                        })
                                    else:
                                        failed_predictions += 1
                                else:
                                    failed_predictions += 1
                            finally:
                                db.close()
                        else:
                            logger.error(f"Prediction failed for {fixture_dict['home_team']} vs {fixture_dict['away_team']}: {prediction_result.get('error')}")
                            failed_predictions += 1

                    except Exception as e:
                        logger.error(f"Error processing fixture {fixture_dict['fixture_id']}: {str(e)}")
                        failed_predictions += 1
                        continue

                # Step 4: Generate and cache accumulators
                logger.info("🎲 Generating accumulators...")
                accumulator_result = self.generate_accumulators_from_cached(all_predictions, prediction_date)

                # Step 5: Update batch status
                self.complete_prediction_batch(batch, len(upcoming_fixture_dicts),
                                             successful_predictions, failed_predictions)

                logger.info(f"🎉 Prediction generation completed!")
                logger.info(f"📊 Results: {successful_predictions} successful, {failed_predictions} failed")

                return {
                    'status': 'completed',
                    'date': str(date_obj),
                    'total_fixtures': len(upcoming_fixture_dicts),
                    'successful_predictions': successful_predictions,
                    'failed_predictions': failed_predictions,
                    'models_used': len(models),
                    'accumulators_generated': len(accumulator_result.get('accumulators', {})),
                    'batch_id': batch.id,
                    'generation_time': time.time() - batch.started_at.timestamp()
                }

            except Exception as e:
                # Mark batch as failed
                self.fail_prediction_batch(batch, str(e))
                raise e

        except Exception as e:
            logger.error(f"Error in prediction generation: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'date': str(date_obj) if 'date_obj' in locals() else target_date
            }

    def create_prediction_batch(self, prediction_date: datetime) -> PredictionBatch:
        """Create a new prediction batch record or get existing one."""
        try:
            db = next(get_db())

            # Check if batch already exists for this date
            existing_batch = db.query(PredictionBatch).filter(
                func.date(PredictionBatch.batch_date) == prediction_date.date()
            ).first()

            if existing_batch:
                # Update existing batch to running status
                existing_batch.status = 'running'
                existing_batch.started_at = datetime.utcnow()
                existing_batch.completed_at = None
                existing_batch.error_message = None
                db.commit()
                db.refresh(existing_batch)
                logger.info(f"✅ Updated existing prediction batch {existing_batch.id}")
                return existing_batch
            else:
                # Create new batch
                batch = PredictionBatch(
                    batch_date=prediction_date,
                    started_at=datetime.utcnow(),
                    status='running',
                    models_used=18,
                    feature_count=62
                )

                db.add(batch)
                db.commit()
                db.refresh(batch)

                logger.info(f"✅ Created prediction batch {batch.id}")
                return batch

        except Exception as e:
            logger.error(f"Error creating prediction batch: {str(e)}")
            db.rollback()
            raise e
        finally:
            db.close()

    def complete_prediction_batch(self, batch: PredictionBatch, total_fixtures: int,
                                successful: int, failed: int) -> None:
        """Mark prediction batch as completed with statistics."""
        try:
            db = next(get_db())

            batch_obj = db.query(PredictionBatch).filter(PredictionBatch.id == batch.id).first()
            if batch_obj:
                batch_obj.status = 'completed'
                batch_obj.completed_at = datetime.utcnow()
                batch_obj.duration_seconds = (batch_obj.completed_at - batch_obj.started_at).total_seconds()
                batch_obj.total_fixtures = total_fixtures
                batch_obj.successful_predictions = successful
                batch_obj.failed_predictions = failed

                db.commit()
                logger.info(f"✅ Completed prediction batch {batch.id}")

        except Exception as e:
            logger.error(f"Error completing prediction batch: {str(e)}")
            db.rollback()
        finally:
            db.close()

    def fail_prediction_batch(self, batch: PredictionBatch, error_message: str) -> None:
        """Mark prediction batch as failed with error message."""
        try:
            db = next(get_db())

            batch_obj = db.query(PredictionBatch).filter(PredictionBatch.id == batch.id).first()
            if batch_obj:
                batch_obj.status = 'failed'
                batch_obj.completed_at = datetime.utcnow()
                batch_obj.duration_seconds = (batch_obj.completed_at - batch_obj.started_at).total_seconds()
                batch_obj.error_message = error_message

                db.commit()
                logger.error(f"❌ Failed prediction batch {batch.id}: {error_message}")

        except Exception as e:
            logger.error(f"Error failing prediction batch: {str(e)}")
            db.rollback()
        finally:
            db.close()

    def generate_accumulators_from_cached(self, predictions: List[Dict],
                                        prediction_date: datetime) -> Dict[str, Any]:
        """Generate accumulators from cached predictions."""
        try:
            # Convert cached predictions to format expected by accumulator builder
            formatted_predictions = []

            for pred_data in predictions:
                fixture_dict = pred_data['fixture_dict']
                predictions_dict = pred_data['predictions']

                formatted_prediction = {
                    'fixture_info': {
                        'fixture_id': fixture_dict['fixture_id'],
                        'home_team': fixture_dict['home_team'],
                        'away_team': fixture_dict['away_team'],
                        'league': fixture_dict['league_name'],
                        'date': fixture_dict['date']
                    },
                    'ml_predictions': predictions_dict
                }
                formatted_predictions.append(formatted_prediction)

            # Generate accumulators
            accumulator_result = self.accumulator_builder.build_accumulators(formatted_predictions)

            # Cache the accumulators
            if accumulator_result:
                self.cache_accumulators(accumulator_result, prediction_date)

            return accumulator_result

        except Exception as e:
            logger.error(f"Error generating accumulators from cached predictions: {str(e)}")
            return {'accumulators': {}}
