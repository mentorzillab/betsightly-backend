"""
Prediction Retrieval Service for Frontend API Integration
Handles cached prediction retrieval and formatting for API responses.
"""

import logging
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, text
from database import get_db

# Import enhanced schema models
from database_schema_enhanced import (
    CachedFixture, CachedPrediction, PredictionBatch, 
    AccumulatorCache, PredictionAnalytics
)

logger = logging.getLogger(__name__)

class PredictionRetrievalService:
    """Service for retrieving cached predictions for frontend API."""

    def __init__(self):
        """Initialize the retrieval service."""
        pass

    def _format_readable_prediction(self, pred_type: str, prediction: str, home_team: str, away_team: str) -> str:
        """Format prediction into readable text."""
        if pred_type == 'match_result':
            if prediction == '0':
                return f'{home_team} to Win'
            elif prediction == '1':
                return f'{away_team} to Win'
            else:
                return 'Draw'
        elif pred_type in ['over_under', 'over_2_5']:
            return 'Over 2.5 Goals' if prediction == '1' else 'Under 2.5 Goals'
        elif pred_type == 'btts':
            return 'Both Teams to Score' if prediction == '1' else 'Both Teams NOT to Score'
        elif pred_type == 'clean_sheet_home':
            return f'{home_team} Clean Sheet' if prediction == '1' else f'{home_team} NOT Clean Sheet'
        elif pred_type == 'clean_sheet_away':
            return f'{away_team} Clean Sheet' if prediction == '1' else f'{away_team} NOT Clean Sheet'
        elif pred_type == 'win_to_nil_home':
            return f'{home_team} to Win to Nil' if prediction == '1' else f'{home_team} NOT to Win to Nil'
        elif pred_type == 'win_to_nil_away':
            return f'{away_team} to Win to Nil' if prediction == '1' else f'{away_team} NOT to Win to Nil'
        else:
            return f'{pred_type}: {prediction}'

    def _get_confidence_level(self, confidence: float) -> str:
        """Get confidence level description."""
        if confidence >= 0.95:
            return 'ultra_high'
        elif confidence >= 0.90:
            return 'very_high'
        elif confidence >= 0.85:
            return 'high'
        elif confidence >= 0.75:
            return 'medium'
        else:
            return 'low'
    
    def get_daily_predictions(self, target_date: str = None) -> Dict[str, Any]:
        """
        Retrieve cached predictions for a specific date.
        
        Args:
            target_date: Date string in YYYY-MM-DD format
            
        Returns:
            Dict with predictions and metadata
        """
        try:
            # Parse target date
            if target_date:
                date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
            else:
                date_obj = date.today()
            
            db = next(get_db())
            
            # Get prediction batch info
            batch = db.query(PredictionBatch).filter(
                func.date(PredictionBatch.batch_date) == date_obj
            ).first()
            
            if not batch:
                return {
                    'status': 'not_found',
                    'message': f'No predictions found for {date_obj}',
                    'date': str(date_obj),
                    'predictions': []
                }
            
            # Get cached predictions with fixture data
            predictions_query = db.query(CachedPrediction, CachedFixture).join(
                CachedFixture, CachedPrediction.fixture_id == CachedFixture.fixture_id
            ).filter(
                func.date(CachedPrediction.prediction_date) == date_obj
            ).order_by(CachedFixture.fixture_date)
            
            # Group predictions by fixture
            fixture_predictions = {}
            for pred, fixture in predictions_query:
                if fixture.fixture_id not in fixture_predictions:
                    fixture_predictions[fixture.fixture_id] = {
                        'fixture_info': {
                            'fixture_id': fixture.fixture_id,
                            'home_team': fixture.home_team,
                            'away_team': fixture.away_team,
                            'league': fixture.league_name,
                            'country': fixture.country,
                            'date': fixture.fixture_date.isoformat(),
                            'status': fixture.status,
                            'home_odds': fixture.home_odds,
                            'draw_odds': fixture.draw_odds,
                            'away_odds': fixture.away_odds
                        },
                        'predictions': {},
                        'metadata': {
                            'feature_count': pred.feature_count,
                            'feature_version': pred.feature_version,
                            'generation_time_ms': pred.generation_time_ms,
                            'created_at': pred.created_at.isoformat()
                        }
                    }
                
                # Add prediction to fixture
                fixture_predictions[fixture.fixture_id]['predictions'][pred.prediction_type] = {
                    'prediction': pred.prediction_value,
                    'confidence': pred.confidence,
                    'model_type': pred.model_type,
                    'model_name': pred.model_name,
                    'actual_result': pred.actual_result,
                    'is_correct': pred.is_correct
                }
            
            # Convert to list format
            predictions_list = list(fixture_predictions.values())
            
            return {
                'status': 'success',
                'date': str(date_obj),
                'batch_info': {
                    'batch_id': batch.id,
                    'status': batch.status,
                    'total_fixtures': batch.total_fixtures,
                    'successful_predictions': batch.successful_predictions,
                    'failed_predictions': batch.failed_predictions,
                    'models_used': batch.models_used,
                    'feature_count': batch.feature_count,
                    'started_at': batch.started_at.isoformat(),
                    'completed_at': batch.completed_at.isoformat() if batch.completed_at else None,
                    'duration_seconds': batch.duration_seconds
                },
                'predictions': predictions_list,
                'total_predictions': len(predictions_list),
                'data_source': 'cached_predictions'
            }
            
        except Exception as e:
            logger.error(f"Error retrieving daily predictions: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'date': target_date or str(date.today()),
                'predictions': []
            }
        finally:
            db.close()
    
    def get_daily_accumulators(self, target_date: str = None) -> Dict[str, Any]:
        """
        Retrieve cached accumulators for a specific date.
        
        Args:
            target_date: Date string in YYYY-MM-DD format
            
        Returns:
            Dict with accumulator data
        """
        try:
            # Parse target date
            if target_date:
                date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
            else:
                date_obj = date.today()
            
            db = next(get_db())
            
            # Get cached accumulators
            accumulators_query = db.query(AccumulatorCache).filter(
                func.date(AccumulatorCache.prediction_date) == date_obj
            ).order_by(AccumulatorCache.accumulator_type)
            
            accumulators = {}
            for acc in accumulators_query:
                accumulators[acc.accumulator_type] = {
                    'selected': acc.is_selected,
                    'total_odds': acc.total_odds,
                    'game_count': acc.game_count,
                    'average_confidence': acc.average_confidence,
                    'diversity_score': acc.diversity_score,
                    'risk_level': acc.risk_level,
                    'recommended_stake': acc.recommended_stake,
                    'games': json.loads(acc.games_data) if acc.games_data else [],
                    'reason': acc.selection_reason,
                    'actual_result': acc.actual_result,
                    'actual_payout': acc.actual_payout,
                    'created_at': acc.created_at.isoformat()
                }
            
            return {
                'status': 'success',
                'date': str(date_obj),
                'accumulators': accumulators,
                'total_categories': len(accumulators),
                'selected_count': sum(1 for acc in accumulators.values() if acc['selected']),
                'data_source': 'cached_accumulators'
            }
            
        except Exception as e:
            logger.error(f"Error retrieving daily accumulators: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'date': target_date or str(date.today()),
                'accumulators': {}
            }
        finally:
            db.close()

    def get_comprehensive_daily_predictions(self, target_date: str = None) -> Dict[str, Any]:
        """Get comprehensive daily predictions with full fixture information."""
        if not target_date:
            target_date = str(date.today())

        try:
            db = next(get_db())

            # Join daily_predictions with cached_fixtures for comprehensive information
            # ONLY show predictions for upcoming games (not finished)
            query = '''
                SELECT
                    dp.home_team, dp.away_team, dp.league_name, dp.fixture_date, dp.ml_predictions,
                    cf.fixture_id, cf.country, cf.status, cf.home_odds, cf.draw_odds, cf.away_odds,
                    cf.home_score, cf.away_score, cf.match_result
                FROM daily_predictions dp
                LEFT JOIN cached_fixtures cf ON (
                    dp.home_team = cf.home_team AND
                    dp.away_team = cf.away_team AND
                    DATE(dp.fixture_date) = DATE(cf.fixture_date)
                )
                WHERE dp.prediction_date = ?
                AND (cf.status IS NULL OR cf.status NOT IN ('Finished', 'FT', 'finished', 'completed', 'Full Time', 'After Pen.', 'AET', 'Postponed', 'Cancelled', 'Abandoned'))
                AND dp.fixture_date > datetime('now')
                ORDER BY dp.fixture_date
            '''

            result = db.execute(text(query), (target_date,))
            rows = result.fetchall()

            if not rows:
                return {
                    'status': 'error',
                    'error': f'No predictions found for {target_date}',
                    'date': target_date
                }

            # Format predictions with comprehensive information
            formatted_predictions = []
            high_confidence_count = 0

            for row in rows:
                try:
                    (home_team, away_team, league, fixture_date, ml_predictions_json,
                     fixture_id, country, status, home_odds, draw_odds, away_odds,
                     home_score, away_score, match_result) = row

                    ml_predictions = json.loads(ml_predictions_json) if ml_predictions_json else {}

                    # Format fixture date and time
                    try:
                        dt = datetime.fromisoformat(fixture_date.replace('Z', '+00:00'))
                        formatted_date = dt.strftime('%Y-%m-%d')
                        formatted_time = dt.strftime('%H:%M')
                        formatted_datetime = dt.isoformat()
                    except:
                        formatted_date = target_date
                        formatted_time = 'TBD'
                        formatted_datetime = fixture_date

                    # Create comprehensive fixture info
                    fixture_info = {
                        'fixture_id': fixture_id or 'N/A',
                        'home_team': home_team,
                        'away_team': away_team,
                        'league': league,
                        'country': country or 'Unknown',
                        'date': formatted_date,
                        'time': formatted_time,
                        'datetime': formatted_datetime,
                        'status': status or 'upcoming',
                        'odds': {
                            'home': float(home_odds) if home_odds else 2.0,
                            'draw': float(draw_odds) if draw_odds else 3.0,
                            'away': float(away_odds) if away_odds else 2.0
                        }
                    }

                    # Add score and result if available
                    if home_score is not None and away_score is not None:
                        fixture_info['score'] = {
                            'home': home_score,
                            'away': away_score
                        }
                        fixture_info['result'] = match_result

                    # Format predictions with readable text
                    formatted_ml_predictions = {}
                    for pred_type, pred_data in ml_predictions.items():
                        confidence = pred_data.get('confidence', 0.0)
                        prediction = pred_data.get('prediction', 'N/A')
                        model_type = pred_data.get('model_type', 'unknown')

                        # Count high confidence predictions
                        if confidence >= 0.85:
                            high_confidence_count += 1

                        # Create readable prediction
                        readable_prediction = self._format_readable_prediction(
                            pred_type, str(prediction), home_team, away_team
                        )

                        formatted_ml_predictions[pred_type] = {
                            'prediction': prediction,
                            'readable_prediction': readable_prediction,
                            'confidence': confidence,
                            'confidence_percentage': f"{confidence:.1%}",
                            'confidence_level': self._get_confidence_level(confidence),
                            'model_type': model_type
                        }

                    formatted_predictions.append({
                        'fixture_info': fixture_info,
                        'predictions': formatted_ml_predictions
                    })

                except Exception as e:
                    logger.error(f"Error formatting prediction for {home_team} vs {away_team}: {str(e)}")
                    continue

            return {
                'status': 'success',
                'date': target_date,
                'predictions': formatted_predictions,
                'total_predictions': len(formatted_predictions),
                'high_confidence_count': high_confidence_count,
                'summary': {
                    'total_fixtures': len(formatted_predictions),
                    'high_confidence_predictions': high_confidence_count,
                    'leagues_covered': len(set(p['fixture_info']['league'] for p in formatted_predictions)),
                    'countries_covered': len(set(p['fixture_info']['country'] for p in formatted_predictions))
                }
            }

        except Exception as e:
            logger.error(f"Error retrieving comprehensive daily predictions: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'date': target_date
            }
        finally:
            db.close()
    
    def get_specific_accumulator(self, accumulator_type: str, target_date: str = None) -> Dict[str, Any]:
        """
        Retrieve a specific accumulator type for a date.
        
        Args:
            accumulator_type: Type of accumulator (2_odds, 5_odds, 10_odds, rollover)
            target_date: Date string in YYYY-MM-DD format
            
        Returns:
            Dict with specific accumulator data
        """
        try:
            # Parse target date
            if target_date:
                date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
            else:
                date_obj = date.today()
            
            db = next(get_db())
            
            # Get specific accumulator
            accumulator = db.query(AccumulatorCache).filter(
                and_(
                    func.date(AccumulatorCache.prediction_date) == date_obj,
                    AccumulatorCache.accumulator_type == accumulator_type
                )
            ).first()
            
            if not accumulator:
                return {
                    'status': 'not_found',
                    'message': f'No {accumulator_type} accumulator found for {date_obj}',
                    'date': str(date_obj),
                    'accumulator_type': accumulator_type,
                    'accumulator': None
                }
            
            accumulator_data = {
                'selected': accumulator.is_selected,
                'total_odds': accumulator.total_odds,
                'game_count': accumulator.game_count,
                'average_confidence': accumulator.average_confidence,
                'diversity_score': accumulator.diversity_score,
                'risk_level': accumulator.risk_level,
                'recommended_stake': accumulator.recommended_stake,
                'games': json.loads(accumulator.games_data) if accumulator.games_data else [],
                'reason': accumulator.selection_reason,
                'actual_result': accumulator.actual_result,
                'actual_payout': accumulator.actual_payout,
                'created_at': accumulator.created_at.isoformat()
            }
            
            return {
                'status': 'success',
                'date': str(date_obj),
                'accumulator_type': accumulator_type,
                'accumulator': accumulator_data,
                'data_source': 'cached_accumulator'
            }
            
        except Exception as e:
            logger.error(f"Error retrieving specific accumulator: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'date': target_date or str(date.today()),
                'accumulator_type': accumulator_type,
                'accumulator': None
            }
        finally:
            db.close()
