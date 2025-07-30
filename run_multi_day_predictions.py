#!/usr/bin/env python3
"""
🎯 BETSIGHTLY MULTI-DAY PREDICTION ORCHESTRATOR
Main script to generate, format, and save predictions for tomorrow through Sunday.

This script:
1. Generates predictions for each day from tomorrow through Sunday
2. Categorizes predictions according to the existing system (2_odds, 5_odds, 10_odds, rollover)
3. Includes comprehensive metadata (date/time in Nigeria timezone, teams, confidence, odds)
4. Formats predictions in a structured, readable format
5. Saves to a text file with clear filename including date range

Usage:
    python run_multi_day_predictions.py
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("multi_day_predictions_orchestrator.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main orchestrator function."""
    print("🎯 BETSIGHTLY MULTI-DAY PREDICTION ORCHESTRATOR")
    print("=" * 80)
    print("🇳🇬 Generating predictions for tomorrow through Sunday (Nigeria timezone)")
    print("=" * 80)
    print("")
    
    try:
        # Step 1: Generate multi-day predictions
        print("📊 STEP 1: GENERATING MULTI-DAY PREDICTIONS")
        print("-" * 50)
        
        from generate_multi_day_predictions import MultiDayPredictionGenerator
        generator = MultiDayPredictionGenerator()
        
        print("🚀 Starting prediction generation...")
        results = generator.generate_multi_day_predictions()
        
        if not results:
            print("❌ Failed to generate predictions")
            return False
        
        # Save results to intermediate file
        results_file = "multi_day_predictions_results.json"
        try:
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"💾 Results saved to {results_file}")
        except Exception as e:
            print(f"⚠️  Warning: Could not save intermediate results: {str(e)}")
        
        print("✅ Prediction generation completed!")
        print("")
        
        # Step 2: Format and save predictions
        print("📄 STEP 2: FORMATTING AND SAVING PREDICTIONS")
        print("-" * 50)
        
        from format_and_save_predictions import format_and_save_from_results
        
        print("🎨 Formatting predictions...")
        filename = format_and_save_from_results(results)
        
        if filename:
            print("✅ Predictions formatted and saved successfully!")
            print("")
            
            # Step 3: Display summary
            print("📋 STEP 3: SUMMARY")
            print("-" * 50)
            
            summary = results.get('summary', {})
            gen_info = results.get('generation_info', {})
            
            print(f"📅 Date Range: {gen_info.get('date_range', {}).get('start_date', 'Unknown')} to {gen_info.get('date_range', {}).get('end_date', 'Unknown')}")
            print(f"🌍 Timezone: {gen_info.get('timezone', 'Unknown')}")
            print(f"📊 Total Days: {summary.get('total_days', 0)}")
            print(f"✅ Successful Days: {summary.get('successful_days', 0)}")
            print(f"🎯 Total Predictions: {summary.get('total_predictions', 0)}")
            print("")
            
            print("🎲 Predictions by Category:")
            total_by_category = summary.get('total_by_category', {})
            category_names = {
                '2_odds': '2.0 Odds (Very Low Risk)',
                '5_odds': '5.0 Odds (Low Risk)',
                '10_odds': '10.0 Odds (Medium Risk)',
                'rollover': 'Rollover/Accumulator (Very Low Risk)'
            }
            
            for category, count in total_by_category.items():
                category_name = category_names.get(category, category.upper())
                print(f"   • {category_name}: {count} predictions")
            
            print("")
            print(f"📁 Output File: {filename}")
            print("")
            
            # Step 4: Display daily breakdown
            print("📅 DAILY BREAKDOWN:")
            print("-" * 30)
            
            daily_predictions = results.get('daily_predictions', {})
            for date_str in sorted(daily_predictions.keys()):
                day_data = daily_predictions[date_str]
                day_name = day_data.get('day_name', 'Unknown')
                status = day_data.get('status', 'unknown')
                total_preds = day_data.get('total_predictions', 0)
                
                status_icon = "✅" if status == 'success' else "❌"
                print(f"   {status_icon} {date_str} ({day_name}): {total_preds} predictions")
            
            print("")
            print("🎉 MULTI-DAY PREDICTION GENERATION COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print("")
            print("📖 Next Steps:")
            print(f"   1. Review the predictions in: {filename}")
            print("   2. Use the categorized predictions for betting purposes")
            print("   3. Monitor the results and track accuracy")
            print("")
            
            return True
            
        else:
            print("❌ Failed to format and save predictions")
            return False
    
    except Exception as e:
        logger.error(f"❌ Error in multi-day prediction orchestrator: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return False

def display_help():
    """Display help information."""
    print("🎯 BETSIGHTLY MULTI-DAY PREDICTION ORCHESTRATOR")
    print("=" * 60)
    print("")
    print("This script generates football predictions for multiple days")
    print("from tomorrow through Sunday using the betsightly prediction system.")
    print("")
    print("Features:")
    print("• Generates predictions for tomorrow through Sunday")
    print("• Uses Nigeria timezone (WAT - UTC+1)")
    print("• Categorizes predictions by risk level (2_odds, 5_odds, 10_odds, rollover)")
    print("• Includes comprehensive metadata (teams, date/time, confidence, odds)")
    print("• Saves structured output to readable text file")
    print("")
    print("Usage:")
    print("   python run_multi_day_predictions.py")
    print("")
    print("Output:")
    print("   predictions_YYYY-MM-DD_to_YYYY-MM-DD.txt")
    print("")

if __name__ == "__main__":
    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        display_help()
        sys.exit(0)
    
    # Run the main orchestrator
    success = main()
    
    if success:
        print("✅ All operations completed successfully!")
        sys.exit(0)
    else:
        print("❌ Some operations failed. Check the logs for details.")
        sys.exit(1)
