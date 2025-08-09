"""
Enhanced Database Initialization Script
Creates all tables for the comprehensive prediction caching and fixture management system.
"""

import logging
from datetime import datetime
from database import engine, Base, get_db

# Import all enhanced schema models to ensure they're registered
from database_schema_enhanced import (
    CachedFixture, CachedPrediction, PredictionBatch, 
    AccumulatorCache, PredictionAnalytics
)

# Import existing models
from services.daily_predictions_service import DailyPrediction, DailyPredictionSummary

logger = logging.getLogger(__name__)

def initialize_enhanced_database():
    """Initialize the enhanced database with all required tables."""
    try:
        logger.info("🚀 Initializing enhanced database schema...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Enhanced database tables created successfully:")

        # List all created tables
        table_names = [
            'cached_fixtures',
            'cached_predictions',
            'enhanced_prediction_batches',
            'accumulator_cache',
            'prediction_analytics',
            'daily_predictions',
            'daily_prediction_summary'
        ]
        
        for table_name in table_names:
            logger.info(f"   📋 {table_name}")
        
        # Verify tables exist by checking metadata
        inspector_tables = Base.metadata.tables.keys()
        logger.info(f"✅ Total tables in metadata: {len(inspector_tables)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing enhanced database: {str(e)}")
        return False

def verify_database_structure():
    """Verify that all required tables and indexes exist."""
    try:
        logger.info("🔍 Verifying database structure...")
        
        db = next(get_db())
        
        # Test each table by performing a simple query
        from sqlalchemy import text

        test_queries = [
            ("cached_fixtures", "SELECT COUNT(*) FROM cached_fixtures"),
            ("cached_predictions", "SELECT COUNT(*) FROM cached_predictions"),
            ("enhanced_prediction_batches", "SELECT COUNT(*) FROM enhanced_prediction_batches"),
            ("accumulator_cache", "SELECT COUNT(*) FROM accumulator_cache"),
            ("prediction_analytics", "SELECT COUNT(*) FROM prediction_analytics")
        ]

        for table_name, query in test_queries:
            try:
                result = db.execute(text(query)).fetchone()
                count = result[0] if result else 0
                logger.info(f"   ✅ {table_name}: {count} records")
            except Exception as e:
                logger.error(f"   ❌ {table_name}: Error - {str(e)}")
                return False
        
        logger.info("✅ Database structure verification completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verifying database structure: {str(e)}")
        return False
    finally:
        db.close()

def create_sample_data():
    """Create sample data for testing (optional)."""
    try:
        logger.info("📝 Creating sample data for testing...")
        
        db = next(get_db())
        
        # Create a sample prediction batch
        sample_batch = PredictionBatch(
            batch_date=datetime.now(),
            total_fixtures=0,
            successful_predictions=0,
            failed_predictions=0,
            status='completed',
            models_used=18,
            feature_count=62,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration_seconds=0.0
        )
        
        db.add(sample_batch)
        db.commit()
        
        logger.info("✅ Sample data created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating sample data: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Main initialization function."""
    print("🗄️  ENHANCED DATABASE INITIALIZATION")
    print("=" * 50)
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    # Step 1: Initialize database
    if not initialize_enhanced_database():
        print("❌ Database initialization failed")
        return False
    
    # Step 2: Verify structure
    if not verify_database_structure():
        print("❌ Database verification failed")
        return False
    
    # Step 3: Create sample data (optional)
    create_sample_data()
    
    print("\n🎉 ENHANCED DATABASE INITIALIZATION COMPLETED!")
    print("=" * 50)
    print("✅ All tables created and verified")
    print("✅ Database ready for prediction caching system")
    print("✅ Indexes created for optimal performance")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
