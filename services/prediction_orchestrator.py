"""
Prediction Orchestrator Service
Main service that coordinates all prediction caching, analytics, and cleanup operations.
"""

import logging
import schedule
import time
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional

# Import all the enhanced services
from services.prediction_cache_service import PredictionCacheService
from services.prediction_retrieval_service import PredictionRetrievalService
from services.prediction_analytics_service import PredictionAnalyticsService
from services.data_cleanup_service import DataCleanupService

logger = logging.getLogger(__name__)

class PredictionOrchestrator:
    """
    Main orchestrator for the comprehensive prediction system.
    Coordinates caching, analytics, and cleanup operations.
    """
    
    def __init__(self, 
                 auto_schedule: bool = True,
                 retention_days: int = 90,
                 archive_path: str = './data_archive'):
        """
        Initialize the orchestrator.
        
        Args:
            auto_schedule: Whether to automatically schedule daily operations
            retention_days: Data retention period in days
            archive_path: Path for data archival
        """
        self.cache_service = PredictionCacheService()
        self.retrieval_service = PredictionRetrievalService()
        self.analytics_service = PredictionAnalyticsService()
        self.cleanup_service = DataCleanupService(retention_days, archive_path)
        
        self.auto_schedule = auto_schedule
        
        if auto_schedule:
            self.setup_scheduled_tasks()
            logger.info("✅ Prediction orchestrator initialized with automatic scheduling")
        else:
            logger.info("✅ Prediction orchestrator initialized (manual mode)")
    
    def setup_scheduled_tasks(self):
        """Set up automatic scheduling for daily operations."""
        try:
            # Schedule daily prediction generation at 6:00 AM
            schedule.every().day.at("06:00").do(self.run_daily_predictions)
            
            # Schedule result updates at 11:00 PM (for completed matches)
            schedule.every().day.at("23:00").do(self.run_result_updates)
            
            # Schedule analytics generation at 11:30 PM
            schedule.every().day.at("23:30").do(self.run_daily_analytics)
            
            # Schedule weekly cleanup on Sundays at 2:00 AM
            schedule.every().sunday.at("02:00").do(self.run_data_cleanup)
            
            logger.info("✅ Scheduled tasks configured:")
            logger.info("   📅 06:00 - Daily prediction generation")
            logger.info("   📅 23:00 - Result updates")
            logger.info("   📅 23:30 - Analytics generation")
            logger.info("   📅 Sunday 02:00 - Data cleanup")
            
        except Exception as e:
            logger.error(f"Error setting up scheduled tasks: {str(e)}")
    
    def run_daily_predictions(self, target_date: str = None, force_regenerate: bool = False) -> Dict[str, Any]:
        """
        Run daily prediction generation process.
        
        Args:
            target_date: Date string in YYYY-MM-DD format
            force_regenerate: Force regeneration even if predictions exist
            
        Returns:
            Dict with operation results
        """
        try:
            logger.info("🚀 Starting daily prediction generation process")
            
            # Generate and cache predictions
            result = self.cache_service.generate_and_cache_daily_predictions(
                target_date=target_date,
                force_regenerate=force_regenerate
            )
            
            if result['status'] == 'completed':
                logger.info(f"✅ Daily predictions completed successfully")
                logger.info(f"   📊 {result['successful_predictions']} predictions generated")
                logger.info(f"   🎲 {result['accumulators_generated']} accumulator categories")
                logger.info(f"   ⏱️  Generation time: {result['generation_time']:.2f}s")
            elif result['status'] == 'skipped':
                logger.info(f"⏭️  Daily predictions skipped - already exist for {result['date']}")
            else:
                logger.error(f"❌ Daily predictions failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in daily prediction process: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'operation': 'daily_predictions'
            }
    
    def run_result_updates(self, target_date: str = None) -> Dict[str, Any]:
        """
        Run result updates for completed matches.
        
        Args:
            target_date: Date string in YYYY-MM-DD format (defaults to yesterday)
            
        Returns:
            Dict with operation results
        """
        try:
            logger.info("🔄 Starting result updates process")
            
            # Update match results
            result = self.analytics_service.update_match_results(target_date=target_date)
            
            if result['status'] == 'completed':
                logger.info(f"✅ Result updates completed successfully")
                logger.info(f"   📊 {result['fixtures_updated']} fixtures updated")
                logger.info(f"   🎯 {result['predictions_updated']} predictions updated")
            elif result['status'] == 'no_updates_needed':
                logger.info(f"⏭️  No result updates needed for {result['date']}")
            else:
                logger.error(f"❌ Result updates failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in result updates process: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'operation': 'result_updates'
            }
    
    def run_daily_analytics(self, target_date: str = None) -> Dict[str, Any]:
        """
        Run daily analytics generation.
        
        Args:
            target_date: Date string in YYYY-MM-DD format (defaults to yesterday)
            
        Returns:
            Dict with operation results
        """
        try:
            logger.info("📊 Starting daily analytics generation")
            
            # Generate analytics
            result = self.analytics_service.generate_daily_analytics(target_date=target_date)
            
            if result['status'] == 'completed':
                analytics = result['analytics']
                logger.info(f"✅ Daily analytics completed successfully")
                logger.info(f"   🎯 Overall accuracy: {analytics['accuracy_rate']:.1%}")
                logger.info(f"   📈 Total predictions: {analytics['total_predictions']}")
                logger.info(f"   ✅ Correct predictions: {analytics['correct_predictions']}")
            elif result['status'] == 'no_data':
                logger.info(f"⏭️  No analytics data available for {result['date']}")
            else:
                logger.error(f"❌ Analytics generation failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in analytics generation: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'operation': 'daily_analytics'
            }
    
    def run_data_cleanup(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Run data cleanup process.
        
        Args:
            dry_run: If True, only report what would be cleaned without actually cleaning
            
        Returns:
            Dict with operation results
        """
        try:
            logger.info("🧹 Starting data cleanup process")
            
            # Run cleanup
            result = self.cleanup_service.cleanup_old_data(dry_run=dry_run)
            
            if result['status'] == 'completed':
                deleted_counts = result['deleted_counts']
                logger.info(f"✅ Data cleanup completed successfully")
                logger.info(f"   🗑️  Predictions: {deleted_counts.get('predictions', 0)} deleted")
                logger.info(f"   🗑️  Fixtures: {deleted_counts.get('fixtures', 0)} deleted")
                logger.info(f"   🗑️  Accumulators: {deleted_counts.get('accumulators', 0)} deleted")
                logger.info(f"   📦 Archived files: {len(result.get('archived_files', []))}")
            else:
                logger.error(f"❌ Data cleanup failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in data cleanup process: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'operation': 'data_cleanup'
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        try:
            # Get database statistics
            db_stats = self.cleanup_service.get_database_statistics()
            
            # Get today's prediction status
            today_predictions = self.retrieval_service.get_daily_predictions()
            
            # Get today's accumulators
            today_accumulators = self.retrieval_service.get_daily_accumulators()
            
            return {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'database_statistics': db_stats.get('statistics', {}),
                'today_predictions': {
                    'status': today_predictions['status'],
                    'count': today_predictions.get('total_predictions', 0)
                },
                'today_accumulators': {
                    'status': today_accumulators['status'],
                    'selected_count': today_accumulators.get('selected_count', 0),
                    'total_categories': today_accumulators.get('total_categories', 0)
                },
                'scheduled_tasks': self.auto_schedule,
                'next_scheduled_run': self.get_next_scheduled_run()
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_next_scheduled_run(self) -> Optional[str]:
        """Get the next scheduled task run time."""
        try:
            if not self.auto_schedule:
                return None
            
            next_run = schedule.next_run()
            return next_run.isoformat() if next_run else None
            
        except Exception:
            return None
    
    def run_scheduler(self):
        """Run the scheduler loop (blocking operation)."""
        if not self.auto_schedule:
            logger.warning("Scheduler not enabled - use auto_schedule=True")
            return
        
        logger.info("🔄 Starting prediction orchestrator scheduler...")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("🛑 Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
    
    def run_manual_operation(self, operation: str, **kwargs) -> Dict[str, Any]:
        """
        Run a specific operation manually.
        
        Args:
            operation: Operation name ('predictions', 'results', 'analytics', 'cleanup')
            **kwargs: Additional arguments for the operation
            
        Returns:
            Dict with operation results
        """
        operations = {
            'predictions': self.run_daily_predictions,
            'results': self.run_result_updates,
            'analytics': self.run_daily_analytics,
            'cleanup': self.run_data_cleanup
        }
        
        if operation not in operations:
            return {
                'status': 'error',
                'error': f'Unknown operation: {operation}',
                'available_operations': list(operations.keys())
            }
        
        try:
            return operations[operation](**kwargs)
        except Exception as e:
            logger.error(f"Error running manual operation {operation}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'operation': operation
            }
