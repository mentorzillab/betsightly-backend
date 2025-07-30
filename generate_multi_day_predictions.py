#!/usr/bin/env python3
"""
🎯 MULTI-DAY PREDICTION GENERATOR
Generate predictions for multiple consecutive days using the betsightly prediction system.

Features:
- Generates predictions from tomorrow through Sunday
- Uses Nigeria timezone (WAT - UTC+1)
- Includes comprehensive metadata
- Categorizes predictions by odds/risk levels
- Saves structured output to text file
"""

import os
import sys
import json
import pytz
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("multi_day_predictions.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MultiDayPredictionGenerator:
    """Generator for multi-day football predictions."""
    
    def __init__(self):
        """Initialize the multi-day prediction generator."""
        self.nigeria_tz = pytz.timezone('Africa/Lagos')
        self.prediction_service = None
        self.categorizer = None
        self.initialized = False
        
    def initialize_services(self) -> bool:
        """Initialize prediction services."""
        try:
            logger.info("🚀 Initializing prediction services...")

            # Initialize working prediction service (real data, working predictions)
            from create_working_prediction_system import WorkingPredictionService
            self.prediction_service = WorkingPredictionService()
            logger.info("   ✅ Working Prediction Service initialized")

            # Initialize prediction categorizer
            from services.prediction_categorizer import PredictionCategorizer
            self.categorizer = PredictionCategorizer()
            logger.info("   ✅ Prediction Categorizer initialized")

            self.initialized = True
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize services: {str(e)}")
            return False
    
    def calculate_prediction_dates(self) -> List[Dict[str, Any]]:
        """Calculate date range from tomorrow through Sunday in Nigeria timezone."""
        # Get current time in Nigeria
        utc_now = datetime.now(pytz.UTC)
        nigeria_time = utc_now.astimezone(self.nigeria_tz)
        
        logger.info(f"🇳🇬 Current Nigeria Time: {nigeria_time.strftime('%Y-%m-%d %H:%M:%S WAT')}")
        
        # Calculate tomorrow
        tomorrow = nigeria_time + timedelta(days=1)
        tomorrow_date = tomorrow.date()
        
        # Find the next Sunday
        days_until_sunday = (6 - tomorrow.weekday()) % 7
        if days_until_sunday == 0 and tomorrow.weekday() != 6:
            days_until_sunday = 7
        
        sunday_date = tomorrow_date + timedelta(days=days_until_sunday)
        
        # Generate all dates from tomorrow through Sunday
        prediction_dates = []
        current_date = tomorrow_date
        
        while current_date <= sunday_date:
            day_name = (nigeria_time.replace(
                year=current_date.year, 
                month=current_date.month, 
                day=current_date.day
            )).strftime('%A')
            
            prediction_dates.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'day_name': day_name,
                'date_obj': current_date
            })
            current_date += timedelta(days=1)
        
        logger.info(f"📋 Prediction dates calculated: {len(prediction_dates)} days")
        for i, date_info in enumerate(prediction_dates, 1):
            logger.info(f"   {i}. {date_info['date']} ({date_info['day_name']})")
        
        return prediction_dates
    
    def generate_predictions_for_date(self, date_str: str) -> Dict[str, Any]:
        """Generate predictions for a specific date."""
        if not self.initialized:
            if not self.initialize_services():
                return {'status': 'error', 'error': 'Service initialization failed'}
        
        logger.info(f"🎯 Generating predictions for {date_str}")
        
        try:
            # Generate predictions using advanced service
            result = self.prediction_service.get_predictions_for_date(date_str)
            
            if result.get('status') == 'success':
                logger.info(f"✅ Generated {len(result.get('predictions', []))} predictions for {date_str}")
                return result
            else:
                logger.warning(f"⚠️  No predictions generated for {date_str}: {result.get('message', 'Unknown reason')}")
                return result
                
        except Exception as e:
            logger.error(f"❌ Error generating predictions for {date_str}: {str(e)}")
            return {
                'status': 'error',
                'date': date_str,
                'error': str(e),
                'predictions': [],
                'categories': {'2_odds': [], '5_odds': [], '10_odds': [], 'rollover': []}
            }
    
    def enhance_prediction_metadata(self, prediction: Dict[str, Any], date_str: str) -> Dict[str, Any]:
        """Enhance prediction with comprehensive metadata."""
        enhanced = prediction.copy()
        
        # Add Nigeria timezone information
        try:
            # Parse the fixture date if available
            if 'fixture_date' in prediction:
                fixture_date = datetime.fromisoformat(prediction['fixture_date'].replace('Z', '+00:00'))
            else:
                fixture_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Convert to Nigeria timezone
            nigeria_time = fixture_date.astimezone(self.nigeria_tz)
            
            enhanced['nigeria_datetime'] = nigeria_time.strftime('%Y-%m-%d %H:%M:%S WAT')
            enhanced['nigeria_date'] = nigeria_time.strftime('%Y-%m-%d')
            enhanced['nigeria_time'] = nigeria_time.strftime('%H:%M')
            enhanced['day_of_week'] = nigeria_time.strftime('%A')
            
        except Exception as e:
            logger.warning(f"⚠️  Could not parse date for prediction: {str(e)}")
            enhanced['nigeria_datetime'] = f"{date_str} TBD WAT"
            enhanced['nigeria_date'] = date_str
            enhanced['nigeria_time'] = "TBD"
            enhanced['day_of_week'] = "Unknown"
        
        # Add prediction metadata
        enhanced['prediction_generated_at'] = datetime.now(self.nigeria_tz).strftime('%Y-%m-%d %H:%M:%S WAT')
        enhanced['prediction_type'] = enhanced.get('prediction', 'Unknown')
        enhanced['confidence_level'] = self._get_confidence_level(enhanced.get('confidence', 0))
        enhanced['risk_category'] = self._get_risk_category(enhanced.get('category', 'unknown'))
        
        return enhanced
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Convert confidence score to descriptive level."""
        if confidence >= 0.8:
            return "Very High"
        elif confidence >= 0.7:
            return "High"
        elif confidence >= 0.6:
            return "Medium"
        elif confidence >= 0.5:
            return "Low"
        else:
            return "Very Low"
    
    def _get_risk_category(self, category: str) -> str:
        """Convert category to risk description."""
        risk_mapping = {
            '2_odds': 'Very Low Risk',
            '5_odds': 'Low Risk', 
            '10_odds': 'Medium Risk',
            'rollover': 'Very Low Risk (Accumulator)'
        }
        return risk_mapping.get(category, 'Unknown Risk')
    
    def generate_multi_day_predictions(self) -> Dict[str, Any]:
        """Generate predictions for all days from tomorrow through Sunday."""
        logger.info("🎯 STARTING MULTI-DAY PREDICTION GENERATION")
        logger.info("=" * 60)
        
        # Calculate prediction dates
        prediction_dates = self.calculate_prediction_dates()
        
        # Initialize results structure
        results = {
            'generation_info': {
                'generated_at': datetime.now(self.nigeria_tz).strftime('%Y-%m-%d %H:%M:%S WAT'),
                'date_range': {
                    'start_date': prediction_dates[0]['date'],
                    'end_date': prediction_dates[-1]['date'],
                    'total_days': len(prediction_dates)
                },
                'timezone': 'Nigeria (WAT - UTC+1)'
            },
            'daily_predictions': {},
            'summary': {
                'total_days': len(prediction_dates),
                'successful_days': 0,
                'total_predictions': 0,
                'total_by_category': {'2_odds': 0, '5_odds': 0, '10_odds': 0, 'rollover': 0}
            }
        }
        
        # Generate predictions for each date
        for date_info in prediction_dates:
            date_str = date_info['date']
            day_name = date_info['day_name']
            
            logger.info(f"📅 Processing {date_str} ({day_name})")
            
            # Generate predictions for this date
            day_result = self.generate_predictions_for_date(date_str)
            
            if day_result.get('status') == 'success':
                # Enhance predictions with metadata
                enhanced_predictions = []
                for pred in day_result.get('predictions', []):
                    enhanced_pred = self.enhance_prediction_metadata(pred, date_str)
                    enhanced_predictions.append(enhanced_pred)
                
                # Store enhanced results
                results['daily_predictions'][date_str] = {
                    'date': date_str,
                    'day_name': day_name,
                    'status': 'success',
                    'predictions': enhanced_predictions,
                    'categories': day_result.get('categories', {}),
                    'metadata': day_result.get('metadata', {}),
                    'total_predictions': len(enhanced_predictions)
                }
                
                # Update summary
                results['summary']['successful_days'] += 1
                results['summary']['total_predictions'] += len(enhanced_predictions)
                
                # Count by category
                for category, preds in day_result.get('categories', {}).items():
                    if category in results['summary']['total_by_category']:
                        results['summary']['total_by_category'][category] += len(preds)
                
                logger.info(f"✅ {len(enhanced_predictions)} predictions generated for {date_str}")
            else:
                # Store failed result
                results['daily_predictions'][date_str] = {
                    'date': date_str,
                    'day_name': day_name,
                    'status': 'failed',
                    'error': day_result.get('error', 'Unknown error'),
                    'predictions': [],
                    'categories': {'2_odds': [], '5_odds': [], '10_odds': [], 'rollover': []},
                    'total_predictions': 0
                }
                logger.warning(f"❌ Failed to generate predictions for {date_str}")
        
        logger.info("🎉 Multi-day prediction generation completed!")
        logger.info(f"📊 Summary: {results['summary']['successful_days']}/{results['summary']['total_days']} days successful")
        logger.info(f"🎯 Total predictions: {results['summary']['total_predictions']}")
        
        return results

if __name__ == "__main__":
    generator = MultiDayPredictionGenerator()
    results = generator.generate_multi_day_predictions()
    
    # The results will be formatted and saved by the main script
    print(json.dumps(results, indent=2, default=str))
