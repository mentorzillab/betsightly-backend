"""
Prediction Analytics and Result Tracking Service
Handles result tracking, accuracy calculation, and performance analytics.
"""

import logging
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, or_
from database import get_db

# Import enhanced schema models
from database_schema_enhanced import (
    CachedFixture, CachedPrediction, PredictionBatch, 
    AccumulatorCache, PredictionAnalytics
)

# Import services
from services.apifootball_service import APIFootballService

logger = logging.getLogger(__name__)

class PredictionAnalyticsService:
    """Service for tracking prediction results and generating analytics."""
    
    def __init__(self):
        """Initialize the analytics service."""
        self.apifootball_service = APIFootballService()
    
    def update_match_results(self, target_date: str = None) -> Dict[str, Any]:
        """
        Fetch actual match results and update cached fixtures and predictions.
        
        Args:
            target_date: Date string in YYYY-MM-DD format
            
        Returns:
            Dict with update results
        """
        try:
            # Parse target date (default to yesterday for completed matches)
            if target_date:
                date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
            else:
                date_obj = date.today() - timedelta(days=1)
            
            logger.info(f"🔄 Updating match results for {date_obj}")
            
            db = next(get_db())
            
            # Get fixtures that need result updates
            fixtures_to_update = db.query(CachedFixture).filter(
                and_(
                    func.date(CachedFixture.fixture_date) == date_obj,
                    or_(
                        CachedFixture.status.in_(['upcoming', 'not_started', 'live']),
                        CachedFixture.match_result.is_(None)
                    )
                )
            ).all()
            
            if not fixtures_to_update:
                logger.info(f"No fixtures to update for {date_obj}")
                return {
                    'status': 'no_updates_needed',
                    'date': str(date_obj),
                    'fixtures_checked': 0,
                    'fixtures_updated': 0
                }
            
            logger.info(f"Found {len(fixtures_to_update)} fixtures to update")
            
            # Fetch latest fixture data from API
            api_fixtures = self.apifootball_service.get_daily_fixtures(str(date_obj))
            api_fixtures_dict = {str(f.get('fixture_id', '')): f for f in api_fixtures}
            
            updated_fixtures = 0
            updated_predictions = 0
            
            for fixture in fixtures_to_update:
                try:
                    api_fixture = api_fixtures_dict.get(fixture.fixture_id)
                    
                    if api_fixture and api_fixture.get('status') in ['finished', 'completed', 'FT']:
                        # Update fixture with results
                        home_score = api_fixture.get('home_score')
                        away_score = api_fixture.get('away_score')
                        
                        if home_score is not None and away_score is not None:
                            fixture.home_score = int(home_score)
                            fixture.away_score = int(away_score)
                            fixture.status = 'finished'
                            fixture.updated_at = datetime.utcnow()
                            
                            # Determine match result
                            if home_score > away_score:
                                fixture.match_result = 'home'
                                match_result_value = '0'
                            elif away_score > home_score:
                                fixture.match_result = 'away'
                                match_result_value = '1'
                            else:
                                fixture.match_result = 'draw'
                                match_result_value = '2'
                            
                            updated_fixtures += 1
                            
                            # Update related predictions
                            predictions = db.query(CachedPrediction).filter(
                                CachedPrediction.fixture_id == fixture.fixture_id
                            ).all()
                            
                            for prediction in predictions:
                                # Update prediction accuracy
                                actual_result = self.calculate_actual_result(
                                    prediction.prediction_type, 
                                    fixture, 
                                    api_fixture
                                )
                                
                                if actual_result is not None:
                                    prediction.actual_result = actual_result
                                    prediction.is_correct = (prediction.prediction_value == actual_result)
                                    updated_predictions += 1
                            
                except Exception as e:
                    logger.error(f"Error updating fixture {fixture.fixture_id}: {str(e)}")
                    continue
            
            db.commit()
            
            logger.info(f"✅ Updated {updated_fixtures} fixtures and {updated_predictions} predictions")
            
            return {
                'status': 'completed',
                'date': str(date_obj),
                'fixtures_checked': len(fixtures_to_update),
                'fixtures_updated': updated_fixtures,
                'predictions_updated': updated_predictions
            }
            
        except Exception as e:
            logger.error(f"Error updating match results: {str(e)}")
            db.rollback()
            return {
                'status': 'error',
                'error': str(e),
                'date': target_date or str(date.today() - timedelta(days=1))
            }
        finally:
            db.close()
    
    def calculate_actual_result(self, prediction_type: str, fixture: CachedFixture, 
                              api_fixture: Dict) -> Optional[str]:
        """
        Calculate the actual result for a specific prediction type.
        
        Args:
            prediction_type: Type of prediction (match_result, over_under, etc.)
            fixture: CachedFixture with match results
            api_fixture: Raw API fixture data
            
        Returns:
            String representation of actual result or None if cannot determine
        """
        try:
            home_score = fixture.home_score
            away_score = fixture.away_score
            
            if home_score is None or away_score is None:
                return None
            
            total_goals = home_score + away_score
            
            if prediction_type == 'match_result':
                if home_score > away_score:
                    return '0'  # Home win
                elif away_score > home_score:
                    return '1'  # Away win
                else:
                    return '2'  # Draw
                    
            elif prediction_type == 'over_under':
                return '1' if total_goals > 2.5 else '0'  # Over/Under 2.5
                
            elif prediction_type == 'btts':
                return '1' if home_score > 0 and away_score > 0 else '0'
                
            elif prediction_type == 'clean_sheet_home':
                return '1' if away_score == 0 else '0'
                
            elif prediction_type == 'clean_sheet_away':
                return '1' if home_score == 0 else '0'
                
            elif prediction_type == 'win_to_nil_home':
                return '1' if home_score > away_score and away_score == 0 else '0'
                
            elif prediction_type == 'win_to_nil_away':
                return '1' if away_score > home_score and home_score == 0 else '0'
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating actual result for {prediction_type}: {str(e)}")
            return None
    
    def generate_daily_analytics(self, target_date: str = None) -> Dict[str, Any]:
        """
        Generate daily prediction analytics.
        
        Args:
            target_date: Date string in YYYY-MM-DD format
            
        Returns:
            Dict with analytics data
        """
        try:
            # Parse target date
            if target_date:
                date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
            else:
                date_obj = date.today() - timedelta(days=1)
            
            db = next(get_db())
            
            # Get all predictions for the date with results
            predictions = db.query(CachedPrediction).filter(
                and_(
                    func.date(CachedPrediction.prediction_date) == date_obj,
                    CachedPrediction.actual_result.isnot(None)
                )
            ).all()
            
            if not predictions:
                return {
                    'status': 'no_data',
                    'message': f'No completed predictions found for {date_obj}',
                    'date': str(date_obj)
                }
            
            # Calculate overall statistics
            total_predictions = len(predictions)
            correct_predictions = sum(1 for p in predictions if p.is_correct)
            accuracy_rate = correct_predictions / total_predictions if total_predictions > 0 else 0
            
            # Calculate by prediction type
            type_stats = {}
            for pred_type in ['match_result', 'over_under', 'btts', 'clean_sheet_home', 
                            'clean_sheet_away', 'win_to_nil_home', 'win_to_nil_away']:
                type_preds = [p for p in predictions if p.prediction_type == pred_type]
                if type_preds:
                    correct = sum(1 for p in type_preds if p.is_correct)
                    type_stats[f'{pred_type}_accuracy'] = correct / len(type_preds)
                else:
                    type_stats[f'{pred_type}_accuracy'] = None
            
            # Calculate by model type
            model_stats = {}
            for model_type in ['xgboost', 'lightgbm', 'random_forest']:
                model_preds = [p for p in predictions if model_type in p.model_type.lower()]
                if model_preds:
                    correct = sum(1 for p in model_preds if p.is_correct)
                    model_stats[f'{model_type}_accuracy'] = correct / len(model_preds)
                else:
                    model_stats[f'{model_type}_accuracy'] = None
            
            # Calculate by confidence level
            high_conf_preds = [p for p in predictions if p.confidence >= 0.9]
            medium_conf_preds = [p for p in predictions if 0.7 <= p.confidence < 0.9]
            low_conf_preds = [p for p in predictions if p.confidence < 0.7]
            
            confidence_stats = {
                'high_confidence_accuracy': (sum(1 for p in high_conf_preds if p.is_correct) / len(high_conf_preds)) if high_conf_preds else None,
                'medium_confidence_accuracy': (sum(1 for p in medium_conf_preds if p.is_correct) / len(medium_conf_preds)) if medium_conf_preds else None,
                'low_confidence_accuracy': (sum(1 for p in low_conf_preds if p.is_correct) / len(low_conf_preds)) if low_conf_preds else None
            }
            
            # Store analytics in database
            analytics = PredictionAnalytics(
                analysis_date=datetime.combine(date_obj, datetime.min.time()),
                period_type='daily',
                total_predictions=total_predictions,
                correct_predictions=correct_predictions,
                accuracy_rate=accuracy_rate,
                **type_stats,
                **model_stats,
                **confidence_stats,
                created_at=datetime.utcnow()
            )
            
            db.add(analytics)
            db.commit()
            
            logger.info(f"✅ Generated daily analytics for {date_obj}: {accuracy_rate:.1%} accuracy")
            
            return {
                'status': 'completed',
                'date': str(date_obj),
                'analytics': {
                    'total_predictions': total_predictions,
                    'correct_predictions': correct_predictions,
                    'accuracy_rate': accuracy_rate,
                    'by_prediction_type': type_stats,
                    'by_model_type': model_stats,
                    'by_confidence_level': confidence_stats
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating daily analytics: {str(e)}")
            db.rollback()
            return {
                'status': 'error',
                'error': str(e),
                'date': target_date or str(date.today() - timedelta(days=1))
            }
        finally:
            db.close()
