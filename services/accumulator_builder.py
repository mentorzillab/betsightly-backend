"""
Accumulator Builder Service
Combines multiple games to create accumulator bets that reach target odds.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from itertools import combinations
import json

# Set up logging
logger = logging.getLogger(__name__)

class AccumulatorBuilder:
    """Build accumulator bets by combining multiple games to reach target odds."""
    
    def __init__(self):
        """Initialize the accumulator builder for LOW RISK, SAFE BETS."""
        # ULTRA CONSERVATIVE ODDS TARGETS - LOW RISK ONLY
        self.target_odds = {
            '2_odds': {'min': 1.5, 'max': 2.2},     # Very conservative 2x target
            '5_odds': {'min': 2.5, 'max': 4.5},     # Conservative 5x target
            '10_odds': {'min': 4.0, 'max': 8.0},    # Conservative 10x target
            'rollover': {'min': 1.4, 'max': 2.0}    # Ultra safe rollover
        }

        # HIGH CONFIDENCE THRESHOLD - ONLY SAFEST BETS
        self.min_confidence = 0.80  # Only include 80%+ confidence predictions

        # ALLOW UP TO 10 GAMES PER ACCUMULATOR - USER REQUEST
        self.max_games_per_accumulator = 10

        # ADDITIONAL SAFETY FILTERS
        self.min_odds_per_game = 1.15  # Minimum individual game odds (very safe)
        self.max_odds_per_game = 1.80  # Maximum individual game odds (avoid risky picks)

    def categorize_prediction(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Categorize a prediction into betting categories.

        Args:
            prediction: Single prediction dictionary

        Returns:
            Dictionary with betting categories
        """
        try:
            # Extract ML predictions
            ml_predictions = prediction.get('predictions', {})

            # Initialize categories
            categories = {
                '2_odds': {},
                '5_odds': {},
                '10_odds': {},
                'rollover': {}
            }

            # Process each prediction type
            for pred_type, pred_data in ml_predictions.items():
                if not isinstance(pred_data, dict):
                    continue

                confidence = pred_data.get('confidence', 0)
                prediction_value = pred_data.get('prediction', '')

                # Categorize based on confidence and prediction type (adjusted for realistic thresholds)
                if confidence >= 0.008:  # Top tier confidence (0.8%+)
                    categories['2_odds'][pred_type] = {
                        'prediction': prediction_value,
                        'confidence': confidence,
                        'estimated_odds': round(2.0 + (confidence * 10), 2)
                    }
                elif confidence >= 0.007:  # High confidence (0.7%+)
                    categories['5_odds'][pred_type] = {
                        'prediction': prediction_value,
                        'confidence': confidence,
                        'estimated_odds': round(5.0 + (confidence * 20), 2)
                    }
                elif confidence >= 0.006:  # Medium confidence (0.6%+)
                    categories['10_odds'][pred_type] = {
                        'prediction': prediction_value,
                        'confidence': confidence,
                        'estimated_odds': round(10.0 + (confidence * 50), 2)
                    }
                elif confidence >= 0.004:  # Lower confidence for rollover (0.4%+)
                    categories['rollover'][pred_type] = {
                        'prediction': prediction_value,
                        'confidence': confidence,
                        'estimated_odds': round(15.0 + (confidence * 100), 2)
                    }

            return categories

        except Exception as e:
            logger.error(f"❌ Error categorizing prediction: {str(e)}")
            return {
                '2_odds': {},
                '5_odds': {},
                '10_odds': {},
                'rollover': {}
            }
    
    def build_accumulators(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build accumulator bets from multiple game predictions.
        
        Args:
            predictions: List of game predictions with ML data
            
        Returns:
            Dictionary with accumulator combinations for each category
        """
        try:
            logger.info(f"🎯 Building accumulators from {len(predictions)} games")
            
            # Extract high-confidence selections from all games
            selections = self._extract_selections(predictions)
            logger.info(f"📊 Found {len(selections)} high-confidence selections")
            
            if len(selections) == 0:
                return self._empty_accumulators("No high-confidence selections found")
            
            # Build accumulators for each category
            accumulators = {}
            
            for category, target in self.target_odds.items():
                accumulator = self._build_category_accumulator(selections, category, target)
                accumulators[category] = accumulator
                
                if accumulator['selected']:
                    logger.info(f"✅ {category}: {len(accumulator['games'])} games, {accumulator['total_odds']:.2f} odds")
                else:
                    logger.info(f"❌ {category}: {accumulator['reason']}")
            
            return {
                'status': 'success',
                'total_games_analyzed': len(predictions),
                'high_confidence_selections': len(selections),
                'accumulators': accumulators,
                'summary': self._generate_summary(accumulators)
            }
            
        except Exception as e:
            logger.error(f"Error building accumulators: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'accumulators': self._empty_accumulators("Error occurred")
            }
    
    def _extract_selections(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract predictions with variety for all accumulator types."""
        selections = []

        for prediction in predictions:
            fixture_info = prediction.get('fixture_info', {})
            ml_predictions = prediction.get('ml_predictions', {})

            # Get ALL predictions above minimum confidence
            game_predictions = []

            for pred_key, pred_data in ml_predictions.items():
                confidence = pred_data.get('confidence', 0)

                # ULTRA STRICT CONFIDENCE FILTER - ONLY SAFEST BETS
                if confidence >= self.min_confidence:
                    estimated_odds = self._confidence_to_odds(confidence)

                    # ADDITIONAL SAFETY CHECK - Only include if odds are in safe range
                    if not (self.min_odds_per_game <= estimated_odds <= self.max_odds_per_game):
                        continue

                    # Format prediction value based on type and prediction
                    prediction_value = self._format_enhanced_prediction_value(pred_key, pred_data)
                    readable_prediction = self._format_enhanced_readable_prediction(pred_key, pred_data, fixture_info)

                    selection = {
                        'fixture_id': fixture_info.get('fixture_id'),
                        'home_team': fixture_info.get('home_team'),
                        'away_team': fixture_info.get('away_team'),
                        'league': fixture_info.get('league'),
                        'date': fixture_info.get('date'),
                        'prediction_type': pred_key,
                        'prediction_value': prediction_value,
                        'confidence': confidence,
                        'estimated_odds': estimated_odds,
                        'model_type': pred_data.get('model_type'),
                        'raw_prediction': pred_data.get('prediction'),
                        'readable_prediction': readable_prediction
                    }
                    game_predictions.append(selection)

            # Sort by confidence and add diverse predictions per game
            game_predictions.sort(key=lambda x: x['confidence'], reverse=True)

            # Add best prediction from each game (one per fixture for accumulator)
            if game_predictions:
                # Always add the highest confidence prediction
                selections.append(game_predictions[0])

                # For diversity, also add different prediction types from the same game
                # but mark them as alternatives (they won't be used together)
                added_types = {game_predictions[0]['prediction_type']}

                for pred in game_predictions[1:]:
                    # Add if it's a different prediction type and still high confidence
                    if (pred['prediction_type'] not in added_types and
                        pred['confidence'] >= self.min_confidence and
                        len(added_types) < 3):  # Max 3 different types per game

                        # Create alternative selection for diversity
                        alt_pred = pred.copy()
                        alt_pred['is_alternative'] = True
                        alt_pred['primary_fixture_id'] = pred['fixture_id']
                        selections.append(alt_pred)
                        added_types.add(pred['prediction_type'])

        # Sort by confidence (highest first)
        selections.sort(key=lambda x: x['confidence'], reverse=True)

        return selections
    
    def _confidence_to_odds(self, confidence: float) -> float:
        """Convert confidence to realistic betting odds."""
        # Higher confidence = lower odds (more likely to happen)
        # Using more realistic odds that bookmakers would offer
        if confidence >= 0.95:
            return 1.15  # Very high confidence = very low odds
        elif confidence >= 0.90:
            return 1.25  # High confidence = low odds
        elif confidence >= 0.85:
            return 1.40  # Good confidence = moderate low odds
        elif confidence >= 0.80:
            return 1.60  # Decent confidence = moderate odds
        elif confidence >= 0.75:
            return 1.85  # Fair confidence = fair odds
        elif confidence >= 0.70:
            return 2.10  # Minimum confidence = higher odds
        elif confidence >= 0.65:
            return 2.8  # Higher odds for lower confidence
        elif confidence >= 0.60:
            return 3.5  # Even higher odds
        else:
            return 4.0  # Maximum odds for very low confidence
    
    def _format_prediction_value(self, pred_data: Dict) -> str:
        """Format prediction value for display."""
        prediction = pred_data.get('prediction', 0)
        model_name = pred_data.get('model_name', '')

        if 'match_result' in model_name:
            return ['Home Win', 'Away Win', 'Draw'][prediction] if prediction < 3 else 'Unknown'
        elif 'btts' in model_name:
            return 'Yes' if prediction == 1 else 'No'
        elif 'clean_sheet' in model_name:
            return 'Yes' if prediction == 1 else 'No'
        elif 'over' in model_name:
            return 'Yes' if prediction == 1 else 'No'
        elif 'win_to_nil' in model_name:
            return 'Yes' if prediction == 1 else 'No'
        else:
            return str(prediction)

    def _format_readable_prediction(self, prediction_type: str, prediction_value: str) -> str:
        """Format prediction into human-readable text."""
        predictions = {
            'over_2_5': {
                'Yes': 'Over 2.5 Goals',
                'No': 'Under 2.5 Goals'
            },
            'over_1_5': {
                'Yes': 'Over 1.5 Goals',
                'No': 'Under 1.5 Goals'
            },
            'over_3_5': {
                'Yes': 'Over 3.5 Goals',
                'No': 'Under 3.5 Goals'
            },
            'btts': {
                'Yes': 'Both Teams to Score',
                'No': 'Both Teams NOT to Score'
            },
            'clean_sheet_home': {
                'Yes': 'Home Clean Sheet',
                'No': 'Home NO Clean Sheet'
            },
            'clean_sheet_away': {
                'Yes': 'Away Clean Sheet',
                'No': 'Away NO Clean Sheet'
            },
            'win_to_nil_home': {
                'Yes': 'Home Win to Nil',
                'No': 'Home NOT Win to Nil'
            },
            'win_to_nil_away': {
                'Yes': 'Away Win to Nil',
                'No': 'Away NOT Win to Nil'
            },
            'match_result': {
                'Home Win': 'Home Win',
                'Away Win': 'Away Win',
                'Draw': 'Draw'
            }
        }

        return predictions.get(prediction_type, {}).get(prediction_value, f"{prediction_type}: {prediction_value}")

    def _format_enhanced_prediction_value(self, pred_type: str, pred_data: Dict) -> str:
        """Format prediction value for enhanced predictions."""
        prediction = pred_data.get('prediction', 0)

        if pred_type == 'over_under':
            return 'Over 2.5' if prediction == 1 else 'Under 2.5'
        elif pred_type == 'btts':
            return 'Yes' if prediction == 1 else 'No'
        elif pred_type == 'match_result':
            if prediction == 0:
                return 'Home Win'
            elif prediction == 1:
                return 'Away Win'
            else:  # prediction == 2
                return 'Draw'
        elif pred_type in ['clean_sheet_home', 'clean_sheet_away']:
            return 'Yes' if prediction == 1 else 'No'
        elif pred_type in ['win_to_nil_home', 'win_to_nil_away']:
            return 'Yes' if prediction == 1 else 'No'
        else:
            return str(prediction)

    def _format_enhanced_readable_prediction(self, pred_type: str, pred_data: Dict, fixture_info: Dict) -> str:
        """Format readable prediction for enhanced predictions."""
        prediction = pred_data.get('prediction', 0)
        home_team = fixture_info.get('home_team', 'Home')
        away_team = fixture_info.get('away_team', 'Away')

        if pred_type == 'over_under':
            return 'Over 2.5 Goals' if prediction == 1 else 'Under 2.5 Goals'
        elif pred_type == 'btts':
            return 'Both Teams to Score' if prediction == 1 else 'No Both Teams to Score'
        elif pred_type == 'match_result':
            if prediction == 0:
                return f'{home_team} to Win'
            elif prediction == 1:
                return f'{away_team} to Win'
            else:  # prediction == 2
                return 'Draw'
        elif pred_type == 'clean_sheet_home':
            return f'{home_team} Clean Sheet' if prediction == 1 else f'{home_team} No Clean Sheet'
        elif pred_type == 'clean_sheet_away':
            return f'{away_team} Clean Sheet' if prediction == 1 else f'{away_team} No Clean Sheet'
        elif pred_type == 'win_to_nil_home':
            return f'{home_team} Win to Nil' if prediction == 1 else f'{home_team} No Win to Nil'
        elif pred_type == 'win_to_nil_away':
            return f'{away_team} Win to Nil' if prediction == 1 else f'{away_team} No Win to Nil'
        else:
            return f'{pred_type}: {prediction}'

    def _calculate_diversity_score(self, combination: List[Dict]) -> float:
        """Calculate diversity score for a combination of predictions."""
        if len(combination) <= 1:
            return 1.0

        # Count unique prediction types
        prediction_types = set()
        fixture_ids = set()
        leagues = set()

        for selection in combination:
            prediction_types.add(selection.get('prediction_type', ''))
            fixture_ids.add(selection.get('fixture_id', ''))
            leagues.add(selection.get('league', ''))

        # Diversity factors
        type_diversity = len(prediction_types) / len(combination)  # Unique prediction types
        fixture_diversity = len(fixture_ids) / len(combination)    # Different fixtures
        league_diversity = len(leagues) / len(combination)         # Different leagues

        # Weighted diversity score
        diversity_score = (0.5 * type_diversity) + (0.3 * fixture_diversity) + (0.2 * league_diversity)

        return min(diversity_score, 1.0)  # Cap at 1.0

    def _build_category_accumulator(self, selections: List[Dict], category: str, target: Dict) -> Dict[str, Any]:
        """Build accumulator for a specific category."""
        min_odds = target['min']
        max_odds = target['max']
        
        # Try different combinations to reach target odds
        best_combination = None
        best_odds = 0
        
        # Try combinations of 1 to max_games_per_accumulator games
        for num_games in range(1, min(len(selections) + 1, self.max_games_per_accumulator + 1)):
            for combination in combinations(selections, num_games):
                # Skip combinations with duplicate fixtures (only one prediction per fixture)
                fixture_ids = []
                for s in combination:
                    # Use primary fixture ID for alternatives
                    fid = s.get('primary_fixture_id', s.get('fixture_id'))
                    fixture_ids.append(fid)

                if len(set(fixture_ids)) != len(fixture_ids):
                    continue
                # Calculate total odds (multiply individual odds)
                total_odds = 1.0
                for selection in combination:
                    total_odds *= selection['estimated_odds']
                
                # Check if this combination fits the target
                if min_odds <= total_odds <= max_odds:
                    # Calculate diversity score and confidence
                    total_confidence = sum(s['confidence'] for s in combination) / len(combination)
                    diversity_score = self._calculate_diversity_score(combination)

                    # Combined score: 70% confidence + 30% diversity
                    combined_score = (0.7 * total_confidence) + (0.3 * diversity_score)

                    if best_combination is None or combined_score > best_combination['combined_score']:
                        best_combination = {
                            'games': list(combination),
                            'total_odds': total_odds,
                            'avg_confidence': total_confidence,
                            'diversity_score': diversity_score,
                            'combined_score': combined_score,
                            'num_games': len(combination)
                        }
        
        if best_combination:
            return {
                'selected': True,
                'category': category,
                'games': best_combination['games'],
                'total_odds': round(best_combination['total_odds'], 2),
                'average_confidence': round(best_combination['avg_confidence'], 3),
                'num_games': best_combination['num_games'],
                'target_range': f"{min_odds}-{max_odds}",
                'risk_level': self._get_category_risk(category),
                'recommendation': 'INCLUDE'
            }
        else:
            return {
                'selected': False,
                'category': category,
                'reason': f'No combination found for {min_odds}-{max_odds} odds range',
                'target_range': f"{min_odds}-{max_odds}",
                'recommendation': 'EXCLUDE'
            }
    
    def _get_category_risk(self, category: str) -> str:
        """Get risk level for category."""
        risk_mapping = {
            '2_odds': 'VERY_LOW',
            '5_odds': 'LOW', 
            '10_odds': 'MEDIUM',
            'rollover': 'VERY_LOW'
        }
        return risk_mapping.get(category, 'UNKNOWN')
    
    def _empty_accumulators(self, reason: str) -> Dict[str, Any]:
        """Return empty accumulators structure."""
        empty_accumulators = {}
        for category in self.target_odds.keys():
            empty_accumulators[category] = {
                'selected': False,
                'category': category,
                'reason': reason,
                'recommendation': 'EXCLUDE'
            }
        return empty_accumulators
    
    def _generate_summary(self, accumulators: Dict) -> Dict[str, Any]:
        """Generate summary of accumulator results."""
        selected_count = sum(1 for acc in accumulators.values() if acc.get('selected', False))
        total_games_used = sum(acc.get('num_games', 0) for acc in accumulators.values() if acc.get('selected', False))
        
        return {
            'categories_with_accumulators': selected_count,
            'total_categories': len(accumulators),
            'total_games_in_accumulators': total_games_used,
            'success_rate': f"{(selected_count/len(accumulators)*100):.1f}%"
        }

def format_accumulator_for_display(accumulator: Dict) -> str:
    """Format accumulator for display."""
    if not accumulator.get('selected', False):
        return f"{accumulator['category']}: Not selected - {accumulator.get('reason', 'Unknown')}"
    
    games_text = []
    for game in accumulator['games']:
        game_text = f"{game['home_team']} vs {game['away_team']} ({game['prediction_type']}: {game['prediction_value']})"
        games_text.append(game_text)
    
    return f"""
{accumulator['category'].upper()} ACCUMULATOR:
├─ Total Odds: {accumulator['total_odds']}x
├─ Games: {accumulator['num_games']}
├─ Average Confidence: {accumulator['average_confidence']*100:.1f}%
├─ Risk Level: {accumulator['risk_level']}
└─ Games:
   {chr(10).join(f'   • {game}' for game in games_text)}
"""
