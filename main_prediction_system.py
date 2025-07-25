#!/usr/bin/env python3
"""
🎯 BETSIGHTLY MAIN PREDICTION SYSTEM
Single entry point for the comprehensive football prediction system.

Features:
- Enhanced ML Pipeline (62 features, 18 models)
- Prediction Caching System
- Analytics and Result Tracking
- Risk-Optimized Accumulators
- Telegram and N8N Integration
- Automated Scheduling

Usage:
    python main_prediction_system.py --mode [daily|server|scheduler|analytics]
"""

import argparse
import logging
import sys
import os
import asyncio
from datetime import datetime, date
from typing import Dict, Any, Optional

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("betsightly_system.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BetsightlyMainSystem:
    """Main orchestrator for the Betsightly prediction system."""
    
    def __init__(self):
        """Initialize the main system."""
        self.system_initialized = False
        self.services = {}
        
    def initialize_system(self) -> bool:
        """Initialize all system components."""
        try:
            logger.info("🚀 Initializing Betsightly Prediction System")
            logger.info("=" * 60)
            
            # Step 1: Initialize database
            logger.info("🗄️  Initializing enhanced database...")
            from initialize_enhanced_database import initialize_enhanced_database
            if not initialize_enhanced_database():
                logger.error("❌ Database initialization failed")
                return False
            
            # Step 2: Initialize core services
            logger.info("🎯 Initializing core services...")
            
            # Enhanced ML Pipeline
            from ml_pipeline_streamlined import StreamlinedMLPipeline
            self.services['ml_pipeline'] = StreamlinedMLPipeline()
            logger.info("   ✅ Enhanced ML Pipeline (62 features, 18 models)")
            
            # Prediction Cache Service
            from services.prediction_cache_service import PredictionCacheService
            self.services['cache_service'] = PredictionCacheService()
            logger.info("   ✅ Prediction Cache Service")
            
            # Prediction Retrieval Service
            from services.prediction_retrieval_service import PredictionRetrievalService
            self.services['retrieval_service'] = PredictionRetrievalService()
            logger.info("   ✅ Prediction Retrieval Service")
            
            # Analytics Service
            from services.prediction_analytics_service import PredictionAnalyticsService
            self.services['analytics_service'] = PredictionAnalyticsService()
            logger.info("   ✅ Analytics Service")
            
            # Data Cleanup Service
            from services.data_cleanup_service import DataCleanupService
            self.services['cleanup_service'] = DataCleanupService()
            logger.info("   ✅ Data Cleanup Service")
            
            # Orchestrator Service
            from services.prediction_orchestrator import PredictionOrchestrator
            self.services['orchestrator'] = PredictionOrchestrator(auto_schedule=False)
            logger.info("   ✅ Orchestrator Service")
            
            self.system_initialized = True
            logger.info("✅ System initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {str(e)}")
            return False
    
    def run_daily_predictions(self, target_date: str = None, force_regenerate: bool = False) -> Dict[str, Any]:
        """Run daily prediction generation."""
        if not self.system_initialized:
            if not self.initialize_system():
                return {'status': 'error', 'error': 'System initialization failed'}
        
        logger.info("🎯 RUNNING DAILY PREDICTIONS")
        logger.info("=" * 50)
        
        try:
            # Generate predictions using orchestrator
            result = self.services['orchestrator'].run_daily_predictions(
                target_date=target_date,
                force_regenerate=force_regenerate
            )
            
            if result['status'] == 'completed':
                logger.info("🎉 Daily predictions completed successfully!")
                logger.info(f"   📊 {result['successful_predictions']} predictions generated")
                logger.info(f"   🎲 {result['accumulators_generated']} accumulator categories")
                logger.info(f"   ⏱️  Generation time: {result['generation_time']:.2f}s")
            elif result['status'] == 'skipped':
                logger.info("⏭️  Daily predictions skipped - already exist")
            else:
                logger.error(f"❌ Daily predictions failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in daily predictions: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def run_api_server(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Run the FastAPI server with all enhanced endpoints."""
        if not self.system_initialized:
            if not self.initialize_system():
                logger.error("❌ Cannot start server - system initialization failed")
                return
        
        logger.info("🌐 STARTING ENHANCED API SERVER")
        logger.info("=" * 50)
        
        try:
            import uvicorn
            from main import app
            
            logger.info(f"🚀 Starting server on {host}:{port}")
            logger.info("📋 Available endpoints:")
            logger.info("   • GET  /api/health - System health")
            logger.info("   • GET  /api/daily-predictions/today - Today's predictions")
            logger.info("   • GET  /api/daily-predictions/today/enhanced - Enhanced predictions")
            logger.info("   • GET  /api/accumulators/today - Today's accumulators")
            logger.info("   • GET  /api/accumulators/today/enhanced - Enhanced accumulators")
            logger.info("   • GET  /api/accumulators/{type} - Specific accumulator types")
            
            # Run server
            uvicorn.run(app, host=host, port=port, log_level="info")
            
        except Exception as e:
            logger.error(f"❌ Error starting API server: {str(e)}")
    
    def run_scheduler(self) -> None:
        """Run the automated scheduler for daily operations."""
        if not self.system_initialized:
            if not self.initialize_system():
                logger.error("❌ Cannot start scheduler - system initialization failed")
                return
        
        logger.info("⏰ STARTING AUTOMATED SCHEDULER")
        logger.info("=" * 50)
        
        try:
            # Create orchestrator with auto-scheduling enabled
            from services.prediction_orchestrator import PredictionOrchestrator
            orchestrator = PredictionOrchestrator(auto_schedule=True)
            
            logger.info("📅 Scheduled tasks:")
            logger.info("   • 06:00 - Daily prediction generation")
            logger.info("   • 23:00 - Result updates")
            logger.info("   • 23:30 - Analytics generation")
            logger.info("   • Sunday 02:00 - Data cleanup")
            
            # Run scheduler (blocking)
            orchestrator.run_scheduler()
            
        except Exception as e:
            logger.error(f"❌ Error in scheduler: {str(e)}")
    
    def run_analytics(self, target_date: str = None) -> Dict[str, Any]:
        """Run analytics and result tracking."""
        if not self.system_initialized:
            if not self.initialize_system():
                return {'status': 'error', 'error': 'System initialization failed'}
        
        logger.info("📊 RUNNING ANALYTICS AND RESULT TRACKING")
        logger.info("=" * 50)
        
        try:
            # Run result updates
            result_update = self.services['orchestrator'].run_result_updates(target_date)
            
            # Run analytics generation
            analytics_result = self.services['orchestrator'].run_daily_analytics(target_date)
            
            return {
                'status': 'completed',
                'result_updates': result_update,
                'analytics': analytics_result
            }
            
        except Exception as e:
            logger.error(f"❌ Error in analytics: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        if not self.system_initialized:
            return {'status': 'not_initialized', 'message': 'System not initialized'}
        
        try:
            status = self.services['orchestrator'].get_system_status()
            
            # Add system information
            status.update({
                'system_version': '2.0.0',
                'features': {
                    'enhanced_ml_pipeline': True,
                    'prediction_caching': True,
                    'analytics_tracking': True,
                    'risk_management': True,
                    'telegram_integration': True,
                    'n8n_integration': True,
                    'automated_scheduling': True
                },
                'components': {
                    'ml_models': 18,
                    'features_per_prediction': 62,
                    'accumulator_categories': 4,
                    'api_endpoints': 'enhanced',
                    'database_tables': 'enhanced_schema'
                }
            })
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Error getting system status: {str(e)}")
            return {'status': 'error', 'error': str(e)}

def main():
    """Main entry point with command line interface."""
    parser = argparse.ArgumentParser(
        description="Betsightly Main Prediction System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main_prediction_system.py --mode daily                    # Generate today's predictions
  python main_prediction_system.py --mode daily --date 2025-07-26  # Generate for specific date
  python main_prediction_system.py --mode daily --force            # Force regenerate
  python main_prediction_system.py --mode server                   # Start API server
  python main_prediction_system.py --mode scheduler                # Start automated scheduler
  python main_prediction_system.py --mode analytics                # Run analytics
  python main_prediction_system.py --mode status                   # Get system status
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['daily', 'server', 'scheduler', 'analytics', 'status'],
        required=True,
        help='Operation mode'
    )
    
    parser.add_argument(
        '--date',
        type=str,
        help='Target date in YYYY-MM-DD format (for daily/analytics modes)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force regenerate predictions (for daily mode)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Server host (for server mode)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Server port (for server mode)'
    )
    
    args = parser.parse_args()
    
    # Initialize main system
    system = BetsightlyMainSystem()
    
    # Execute based on mode
    if args.mode == 'daily':
        result = system.run_daily_predictions(
            target_date=args.date,
            force_regenerate=args.force
        )
        if result['status'] != 'completed' and result['status'] != 'skipped':
            sys.exit(1)
    
    elif args.mode == 'server':
        system.run_api_server(host=args.host, port=args.port)
    
    elif args.mode == 'scheduler':
        system.run_scheduler()
    
    elif args.mode == 'analytics':
        result = system.run_analytics(target_date=args.date)
        if result['status'] != 'completed':
            sys.exit(1)
    
    elif args.mode == 'status':
        status = system.get_system_status()
        print("🎯 SYSTEM STATUS")
        print("=" * 50)
        print(f"Status: {status.get('status', 'unknown')}")
        if 'features' in status:
            print("Features:")
            for feature, enabled in status['features'].items():
                print(f"  • {feature}: {'✅' if enabled else '❌'}")
        if 'components' in status:
            print("Components:")
            for component, value in status['components'].items():
                print(f"  • {component}: {value}")

if __name__ == "__main__":
    main()
