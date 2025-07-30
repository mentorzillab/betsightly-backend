#!/usr/bin/env python3
"""
📄 PREDICTION FORMATTER AND SAVER
Format multi-day predictions into a structured, readable text file.

Features:
- Formats predictions by day and category
- Includes comprehensive metadata
- Creates readable text output
- Saves with descriptive filename
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class PredictionFormatter:
    """Formatter for multi-day prediction results."""
    
    def __init__(self):
        """Initialize the formatter."""
        pass
    
    def format_predictions_to_text(self, results: Dict[str, Any]) -> str:
        """Format prediction results into readable text."""
        lines = []
        
        # Header
        lines.append("🎯 BETSIGHTLY MULTI-DAY PREDICTIONS")
        lines.append("=" * 80)
        lines.append("")
        
        # Generation info
        gen_info = results.get('generation_info', {})
        lines.append(f"📅 Generated: {gen_info.get('generated_at', 'Unknown')}")
        lines.append(f"🌍 Timezone: {gen_info.get('timezone', 'Unknown')}")
        
        date_range = gen_info.get('date_range', {})
        lines.append(f"📊 Date Range: {date_range.get('start_date', 'Unknown')} to {date_range.get('end_date', 'Unknown')}")
        lines.append(f"📈 Total Days: {date_range.get('total_days', 0)}")
        lines.append("")
        
        # Summary
        summary = results.get('summary', {})
        lines.append("📋 SUMMARY")
        lines.append("-" * 40)
        lines.append(f"✅ Successful Days: {summary.get('successful_days', 0)}/{summary.get('total_days', 0)}")
        lines.append(f"🎯 Total Predictions: {summary.get('total_predictions', 0)}")
        lines.append("")
        
        # Category breakdown
        lines.append("🎲 PREDICTIONS BY CATEGORY:")
        total_by_category = summary.get('total_by_category', {})
        for category, count in total_by_category.items():
            category_name = self._get_category_display_name(category)
            lines.append(f"   • {category_name}: {count} predictions")
        lines.append("")
        lines.append("=" * 80)
        lines.append("")
        
        # Daily predictions
        daily_predictions = results.get('daily_predictions', {})
        for date_str in sorted(daily_predictions.keys()):
            day_data = daily_predictions[date_str]
            lines.extend(self._format_daily_predictions(day_data))
            lines.append("")
        
        return "\n".join(lines)
    
    def _get_category_display_name(self, category: str) -> str:
        """Get display name for category."""
        category_names = {
            '2_odds': '2.0 Odds (Very Low Risk)',
            '5_odds': '5.0 Odds (Low Risk)',
            '10_odds': '10.0 Odds (Medium Risk)',
            'rollover': 'Rollover/Accumulator (Very Low Risk)'
        }
        return category_names.get(category, category.upper())
    
    def _format_daily_predictions(self, day_data: Dict[str, Any]) -> List[str]:
        """Format predictions for a single day."""
        lines = []
        
        date_str = day_data.get('date', 'Unknown')
        day_name = day_data.get('day_name', 'Unknown')
        status = day_data.get('status', 'unknown')
        
        # Day header
        lines.append(f"📅 {date_str.upper()} ({day_name.upper()})")
        lines.append("=" * 60)
        
        if status != 'success':
            lines.append(f"❌ Status: FAILED")
            lines.append(f"🚫 Error: {day_data.get('error', 'Unknown error')}")
            lines.append("No predictions available for this day.")
            return lines
        
        total_predictions = day_data.get('total_predictions', 0)
        lines.append(f"✅ Status: SUCCESS")
        lines.append(f"🎯 Total Predictions: {total_predictions}")
        lines.append("")
        
        if total_predictions == 0:
            lines.append("📭 No predictions available for this day.")
            return lines
        
        # Format by categories
        categories = day_data.get('categories', {})
        for category in ['2_odds', '5_odds', '10_odds', 'rollover']:
            category_predictions = categories.get(category, [])
            if category_predictions:
                lines.extend(self._format_category_predictions(category, category_predictions))
                lines.append("")
        
        # Format individual predictions if not categorized
        predictions = day_data.get('predictions', [])
        if predictions and not any(categories.values()):
            lines.append("🎯 ALL PREDICTIONS:")
            lines.append("-" * 30)
            for i, pred in enumerate(predictions, 1):
                lines.extend(self._format_single_prediction(pred, i))
                lines.append("")
        
        return lines
    
    def _format_category_predictions(self, category: str, predictions: List[Dict[str, Any]]) -> List[str]:
        """Format predictions for a specific category."""
        lines = []
        
        category_name = self._get_category_display_name(category)
        lines.append(f"🎲 {category_name.upper()}")
        lines.append("-" * 40)
        
        if not predictions:
            lines.append("   📭 No predictions in this category")
            return lines
        
        for i, pred in enumerate(predictions, 1):
            lines.extend(self._format_single_prediction(pred, i, indent="   "))
            if i < len(predictions):
                lines.append("")
        
        return lines
    
    def _format_single_prediction(self, prediction: Dict[str, Any], index: int, indent: str = "") -> List[str]:
        """Format a single prediction."""
        lines = []
        
        # Basic match info
        home_team = prediction.get('home_team', 'Unknown')
        away_team = prediction.get('away_team', 'Unknown')
        league = prediction.get('league', 'Unknown League')
        
        lines.append(f"{indent}{index}. {home_team} vs {away_team}")
        lines.append(f"{indent}   🏆 League: {league}")
        
        # Date/time info
        nigeria_datetime = prediction.get('nigeria_datetime', 'TBD')
        day_of_week = prediction.get('day_of_week', 'Unknown')
        lines.append(f"{indent}   📅 Date/Time: {nigeria_datetime} ({day_of_week})")
        
        # Prediction info
        prediction_type = prediction.get('prediction', 'Unknown')
        confidence = prediction.get('confidence', 0)
        confidence_level = prediction.get('confidence_level', 'Unknown')
        odds = prediction.get('odds', 0)
        
        lines.append(f"{indent}   🎯 Prediction: {prediction_type}")
        lines.append(f"{indent}   📊 Confidence: {confidence:.1%} ({confidence_level})")
        lines.append(f"{indent}   💰 Odds: {odds:.2f}")
        
        # Risk info
        risk_category = prediction.get('risk_category', 'Unknown')
        lines.append(f"{indent}   ⚠️  Risk Level: {risk_category}")
        
        # Additional metadata if available
        if 'explanations' in prediction and prediction['explanations']:
            lines.append(f"{indent}   💡 AI Reasoning: Available")
        
        if 'advanced_features' in prediction:
            features = prediction['advanced_features']
            models_used = features.get('models_used', 0)
            lines.append(f"{indent}   🤖 Models Used: {models_used}")
        
        return lines
    
    def save_predictions_to_file(self, results: Dict[str, Any], filename: str = None) -> str:
        """Save formatted predictions to text file."""
        if not filename:
            # Generate filename from date range
            gen_info = results.get('generation_info', {})
            date_range = gen_info.get('date_range', {})
            start_date = date_range.get('start_date', 'unknown')
            end_date = date_range.get('end_date', 'unknown')
            filename = f"predictions_{start_date}_to_{end_date}.txt"
        
        # Format predictions
        formatted_text = self.format_predictions_to_text(results)
        
        # Save to file
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(formatted_text)
            
            print(f"✅ Predictions saved to: {filename}")
            print(f"📄 File size: {len(formatted_text)} characters")
            
            return filename
            
        except Exception as e:
            print(f"❌ Error saving predictions to file: {str(e)}")
            return None

def format_and_save_from_results(results: Dict[str, Any]) -> str:
    """Format and save predictions from results dictionary."""
    formatter = PredictionFormatter()
    return formatter.save_predictions_to_file(results)

def main():
    """Main function to run the formatter."""
    print("📄 PREDICTION FORMATTER AND SAVER")
    print("=" * 50)

    # Check if results file exists (from previous generation)
    results_file = "multi_day_predictions_results.json"
    if os.path.exists(results_file):
        print(f"📂 Loading results from {results_file}")
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)
        except Exception as e:
            print(f"❌ Error loading results: {str(e)}")
            return
    else:
        print("❌ No results file found. Please run the prediction generator first.")
        return

    # Format and save
    filename = format_and_save_from_results(results)

    if filename:
        print(f"🎉 Successfully formatted and saved predictions!")
        print(f"📁 Output file: {filename}")
    else:
        print("❌ Failed to save predictions.")

if __name__ == "__main__":
    main()
