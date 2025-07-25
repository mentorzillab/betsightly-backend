"""
Data Cleanup Service
Handles automated cleanup of old predictions, fixtures, and data archival.
"""

import logging
import json
import os
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

class DataCleanupService:
    """Service for automated data cleanup and archival."""
    
    def __init__(self, retention_days: int = 90, archive_path: str = './data_archive'):
        """
        Initialize the cleanup service.
        
        Args:
            retention_days: Number of days to retain data before cleanup
            archive_path: Path to store archived data
        """
        self.retention_days = retention_days
        self.archive_path = archive_path
        
        # Create archive directory if it doesn't exist
        os.makedirs(archive_path, exist_ok=True)
    
    def cleanup_old_data(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Clean up old predictions and fixtures based on retention policy.
        
        Args:
            dry_run: If True, only report what would be deleted without actually deleting
            
        Returns:
            Dict with cleanup results
        """
        try:
            cutoff_date = date.today() - timedelta(days=self.retention_days)
            logger.info(f"🧹 Starting data cleanup for data older than {cutoff_date}")
            
            db = next(get_db())
            
            cleanup_results = {
                'status': 'completed',
                'cutoff_date': str(cutoff_date),
                'dry_run': dry_run,
                'deleted_counts': {},
                'archived_files': []
            }
            
            # 1. Archive and cleanup old predictions
            old_predictions = db.query(CachedPrediction).filter(
                func.date(CachedPrediction.prediction_date) < cutoff_date
            ).all()
            
            if old_predictions:
                if not dry_run:
                    # Archive predictions before deletion
                    archive_file = self.archive_predictions(old_predictions, cutoff_date)
                    if archive_file:
                        cleanup_results['archived_files'].append(archive_file)
                    
                    # Delete old predictions
                    deleted_count = db.query(CachedPrediction).filter(
                        func.date(CachedPrediction.prediction_date) < cutoff_date
                    ).delete()
                    cleanup_results['deleted_counts']['predictions'] = deleted_count
                else:
                    cleanup_results['deleted_counts']['predictions'] = len(old_predictions)
            
            # 2. Archive and cleanup old fixtures
            old_fixtures = db.query(CachedFixture).filter(
                func.date(CachedFixture.fixture_date) < cutoff_date
            ).all()
            
            if old_fixtures:
                if not dry_run:
                    # Archive fixtures before deletion
                    archive_file = self.archive_fixtures(old_fixtures, cutoff_date)
                    if archive_file:
                        cleanup_results['archived_files'].append(archive_file)
                    
                    # Delete old fixtures
                    deleted_count = db.query(CachedFixture).filter(
                        func.date(CachedFixture.fixture_date) < cutoff_date
                    ).delete()
                    cleanup_results['deleted_counts']['fixtures'] = deleted_count
                else:
                    cleanup_results['deleted_counts']['fixtures'] = len(old_fixtures)
            
            # 3. Archive and cleanup old accumulators
            old_accumulators = db.query(AccumulatorCache).filter(
                func.date(AccumulatorCache.prediction_date) < cutoff_date
            ).all()
            
            if old_accumulators:
                if not dry_run:
                    # Archive accumulators before deletion
                    archive_file = self.archive_accumulators(old_accumulators, cutoff_date)
                    if archive_file:
                        cleanup_results['archived_files'].append(archive_file)
                    
                    # Delete old accumulators
                    deleted_count = db.query(AccumulatorCache).filter(
                        func.date(AccumulatorCache.prediction_date) < cutoff_date
                    ).delete()
                    cleanup_results['deleted_counts']['accumulators'] = deleted_count
                else:
                    cleanup_results['deleted_counts']['accumulators'] = len(old_accumulators)
            
            # 4. Cleanup old prediction batches (keep summary info longer)
            batch_cutoff_date = date.today() - timedelta(days=self.retention_days * 2)
            old_batches = db.query(PredictionBatch).filter(
                func.date(PredictionBatch.batch_date) < batch_cutoff_date
            ).all()
            
            if old_batches:
                if not dry_run:
                    deleted_count = db.query(PredictionBatch).filter(
                        func.date(PredictionBatch.batch_date) < batch_cutoff_date
                    ).delete()
                    cleanup_results['deleted_counts']['batches'] = deleted_count
                else:
                    cleanup_results['deleted_counts']['batches'] = len(old_batches)
            
            # 5. Keep analytics data (don't delete, just report)
            old_analytics = db.query(PredictionAnalytics).filter(
                func.date(PredictionAnalytics.analysis_date) < cutoff_date
            ).count()
            cleanup_results['analytics_kept'] = old_analytics
            
            if not dry_run:
                db.commit()
                logger.info(f"✅ Data cleanup completed")
            else:
                logger.info(f"✅ Dry run completed - no data was actually deleted")
            
            return cleanup_results
            
        except Exception as e:
            logger.error(f"Error during data cleanup: {str(e)}")
            if not dry_run:
                db.rollback()
            return {
                'status': 'error',
                'error': str(e),
                'cutoff_date': str(cutoff_date) if 'cutoff_date' in locals() else None
            }
        finally:
            db.close()
    
    def archive_predictions(self, predictions: List[CachedPrediction], cutoff_date: date) -> Optional[str]:
        """Archive predictions to JSON file before deletion."""
        try:
            archive_data = []
            for pred in predictions:
                archive_data.append({
                    'id': pred.id,
                    'fixture_id': pred.fixture_id,
                    'prediction_date': pred.prediction_date.isoformat(),
                    'prediction_type': pred.prediction_type,
                    'prediction_value': pred.prediction_value,
                    'confidence': pred.confidence,
                    'model_type': pred.model_type,
                    'model_name': pred.model_name,
                    'feature_count': pred.feature_count,
                    'feature_version': pred.feature_version,
                    'actual_result': pred.actual_result,
                    'is_correct': pred.is_correct,
                    'created_at': pred.created_at.isoformat(),
                    'generation_time_ms': pred.generation_time_ms
                })
            
            filename = f"predictions_archive_{cutoff_date.strftime('%Y%m%d')}.json"
            filepath = os.path.join(self.archive_path, filename)
            
            with open(filepath, 'w') as f:
                json.dump(archive_data, f, indent=2)
            
            logger.info(f"✅ Archived {len(predictions)} predictions to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error archiving predictions: {str(e)}")
            return None
    
    def archive_fixtures(self, fixtures: List[CachedFixture], cutoff_date: date) -> Optional[str]:
        """Archive fixtures to JSON file before deletion."""
        try:
            archive_data = []
            for fixture in fixtures:
                archive_data.append({
                    'id': fixture.id,
                    'fixture_id': fixture.fixture_id,
                    'home_team': fixture.home_team,
                    'away_team': fixture.away_team,
                    'league_name': fixture.league_name,
                    'league_id': fixture.league_id,
                    'country': fixture.country,
                    'fixture_date': fixture.fixture_date.isoformat(),
                    'status': fixture.status,
                    'home_odds': fixture.home_odds,
                    'draw_odds': fixture.draw_odds,
                    'away_odds': fixture.away_odds,
                    'home_score': fixture.home_score,
                    'away_score': fixture.away_score,
                    'match_result': fixture.match_result,
                    'created_at': fixture.created_at.isoformat(),
                    'updated_at': fixture.updated_at.isoformat(),
                    'api_source': fixture.api_source,
                    'raw_data': fixture.raw_data
                })
            
            filename = f"fixtures_archive_{cutoff_date.strftime('%Y%m%d')}.json"
            filepath = os.path.join(self.archive_path, filename)
            
            with open(filepath, 'w') as f:
                json.dump(archive_data, f, indent=2)
            
            logger.info(f"✅ Archived {len(fixtures)} fixtures to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error archiving fixtures: {str(e)}")
            return None
    
    def archive_accumulators(self, accumulators: List[AccumulatorCache], cutoff_date: date) -> Optional[str]:
        """Archive accumulators to JSON file before deletion."""
        try:
            archive_data = []
            for acc in accumulators:
                archive_data.append({
                    'id': acc.id,
                    'prediction_date': acc.prediction_date.isoformat(),
                    'accumulator_type': acc.accumulator_type,
                    'is_selected': acc.is_selected,
                    'total_odds': acc.total_odds,
                    'game_count': acc.game_count,
                    'average_confidence': acc.average_confidence,
                    'diversity_score': acc.diversity_score,
                    'risk_level': acc.risk_level,
                    'recommended_stake': acc.recommended_stake,
                    'games_data': acc.games_data,
                    'selection_reason': acc.selection_reason,
                    'actual_result': acc.actual_result,
                    'actual_payout': acc.actual_payout,
                    'created_at': acc.created_at.isoformat()
                })
            
            filename = f"accumulators_archive_{cutoff_date.strftime('%Y%m%d')}.json"
            filepath = os.path.join(self.archive_path, filename)
            
            with open(filepath, 'w') as f:
                json.dump(archive_data, f, indent=2)
            
            logger.info(f"✅ Archived {len(accumulators)} accumulators to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error archiving accumulators: {str(e)}")
            return None
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """Get current database statistics for monitoring."""
        try:
            db = next(get_db())
            
            stats = {
                'cached_fixtures': db.query(CachedFixture).count(),
                'cached_predictions': db.query(CachedPrediction).count(),
                'prediction_batches': db.query(PredictionBatch).count(),
                'accumulator_cache': db.query(AccumulatorCache).count(),
                'prediction_analytics': db.query(PredictionAnalytics).count(),
                'oldest_fixture': None,
                'newest_fixture': None,
                'oldest_prediction': None,
                'newest_prediction': None
            }
            
            # Get date ranges
            oldest_fixture = db.query(CachedFixture).order_by(CachedFixture.fixture_date).first()
            newest_fixture = db.query(CachedFixture).order_by(desc(CachedFixture.fixture_date)).first()
            oldest_prediction = db.query(CachedPrediction).order_by(CachedPrediction.prediction_date).first()
            newest_prediction = db.query(CachedPrediction).order_by(desc(CachedPrediction.prediction_date)).first()
            
            if oldest_fixture:
                stats['oldest_fixture'] = oldest_fixture.fixture_date.date().isoformat()
            if newest_fixture:
                stats['newest_fixture'] = newest_fixture.fixture_date.date().isoformat()
            if oldest_prediction:
                stats['oldest_prediction'] = oldest_prediction.prediction_date.date().isoformat()
            if newest_prediction:
                stats['newest_prediction'] = newest_prediction.prediction_date.date().isoformat()
            
            return {
                'status': 'success',
                'statistics': stats,
                'retention_days': self.retention_days,
                'archive_path': self.archive_path
            }
            
        except Exception as e:
            logger.error(f"Error getting database statistics: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
        finally:
            db.close()
