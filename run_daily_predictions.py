#!/usr/bin/env python3
"""
Daily Predictions Runner
Simple wrapper script for the complete prediction pipeline.
Run this script daily to get fresh predictions.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from complete_prediction_pipeline import CompletePredictionPipeline

def main():
    """Run daily predictions with simple interface."""
    print("🎯 DAILY PREDICTIONS RUNNER")
    print("=" * 50)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        # Initialize and run pipeline
        pipeline = CompletePredictionPipeline()
        results = pipeline.run_complete_pipeline()
        
        if results['status'] == 'success':
            print("\n🎉 SUCCESS! Daily predictions are ready!")
            print("\n🌐 Available endpoints:")
            print("   • GET /api/daily-predictions/today")
            print("   • GET /api/accumulators/today")
            print("   • GET /api/accumulators/2-odds")
            print("   • GET /api/accumulators/5-odds")
            print("   • GET /api/accumulators/10-odds")
            print("   • GET /api/accumulators/rollover")
            
            summary = results.get('summary', {})
            print(f"\n📊 Quick Stats:")
            print(f"   • Fixtures: {summary.get('fixtures_processed', 0)}")
            print(f"   • Predictions: {summary.get('predictions_generated', 0)}")
            print(f"   • Success Rate: {summary.get('success_rate', '0%')}")
            
            return True
        else:
            print(f"\n❌ FAILED: {results.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    print("\n" + "=" * 50)
    if success:
        print("✅ Daily predictions completed successfully!")
    else:
        print("❌ Daily predictions failed!")
    print("=" * 50)
    sys.exit(0 if success else 1)
