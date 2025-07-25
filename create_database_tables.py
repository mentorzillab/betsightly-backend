#!/usr/bin/env python3
"""
Create Database Tables
Initialize the database with all required tables for the prediction system.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def create_tables():
    """Create all database tables."""
    print("🗄️  CREATING DATABASE TABLES")
    print("=" * 50)
    
    try:
        # Import database components
        from database import engine, Base
        from services.daily_predictions_service import DailyPrediction, DailyPredictionSummary
        
        print("✅ Database components imported successfully")
        
        # Create all tables
        print("🔨 Creating tables...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ All tables created successfully!")
        
        # Verify tables were created
        print("\n📋 Verifying table creation...")
        
        import sqlite3
        conn = sqlite3.connect('./football.db')
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📊 Found {len(tables)} tables:")
        for table in tables:
            print(f"   • {table[0]}")
        
        # Check specifically for prediction tables
        prediction_tables = ['daily_predictions', 'daily_prediction_summary']
        print(f"\n🎯 Checking prediction tables:")
        
        all_exist = True
        for table_name in prediction_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            exists = cursor.fetchone()
            status = "✅ EXISTS" if exists else "❌ MISSING"
            print(f"   • {table_name}: {status}")
            if not exists:
                all_exist = False
        
        conn.close()
        
        if all_exist:
            print("\n🎉 SUCCESS! All prediction tables are ready!")
            return True
        else:
            print("\n❌ FAILED! Some tables are missing!")
            return False
            
    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        return False

def show_table_schemas():
    """Show the schema of created tables."""
    print("\n📋 TABLE SCHEMAS")
    print("=" * 50)
    
    try:
        import sqlite3
        conn = sqlite3.connect('./football.db')
        cursor = conn.cursor()
        
        # Show schema for prediction tables
        tables = ['daily_predictions', 'daily_prediction_summary']
        
        for table_name in tables:
            print(f"\n🗂️  {table_name.upper()}:")
            print("-" * 30)
            
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            if columns:
                for col in columns:
                    col_id, name, data_type, not_null, default, pk = col
                    pk_str = " (PRIMARY KEY)" if pk else ""
                    null_str = " NOT NULL" if not_null else ""
                    default_str = f" DEFAULT {default}" if default else ""
                    print(f"   • {name}: {data_type}{null_str}{default_str}{pk_str}")
            else:
                print(f"   ❌ Table {table_name} not found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error showing schemas: {str(e)}")

def main():
    """Main function."""
    print("🚀 DATABASE INITIALIZATION")
    print("=" * 60)
    print(f"📅 Started: {os.popen('date').read().strip()}")
    print("=" * 60)
    
    # Create tables
    success = create_tables()
    
    if success:
        # Show table schemas
        show_table_schemas()
        
        print("\n🎯 READY FOR PREDICTIONS!")
        print("=" * 60)
        print("✅ Database is ready for the prediction pipeline")
        print("🚀 You can now run:")
        print("   python run_daily_predictions.py")
        print("   python complete_prediction_pipeline.py")
        print("=" * 60)
        
        return True
    else:
        print("\n❌ DATABASE SETUP FAILED!")
        print("=" * 60)
        print("🔧 Please check the error messages above")
        print("💡 Try running this script again or check database permissions")
        print("=" * 60)
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
