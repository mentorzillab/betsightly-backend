"""
Enhanced Risk Management Service
Implements confidence-based filtering, risk assessment, and bankroll management.
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RiskProfile:
    """Risk profile configuration for different accumulator strategies."""
    name: str
    min_confidence: float
    max_games: int
    max_correlation: float
    target_odds_min: float
    target_odds_max: float
    bankroll_percentage: float
    description: str

class RiskManagementService:
    """Enhanced risk management for optimal predictions and low risk."""
    
    def __init__(self):
        """Initialize risk management service."""
        self.risk_profiles = self._initialize_risk_profiles()
        logger.info("✅ Risk Management Service initialized")
    
    def _initialize_risk_profiles(self) -> Dict[str, RiskProfile]:
        """Initialize risk profiles for different strategies."""
        return {
            'ultra_low_risk': RiskProfile(
                name='Ultra Low Risk (2-odds)',
                min_confidence=0.95,  # 95%+ confidence only
                max_games=2,
                max_correlation=0.3,
                target_odds_min=1.8,
                target_odds_max=2.2,
                bankroll_percentage=0.05,  # 5% of bankroll
                description='Highest confidence predictions, minimal risk'
            ),
            'low_risk': RiskProfile(
                name='Low Risk (5-odds)',
                min_confidence=0.90,  # 90%+ confidence
                max_games=3,
                max_correlation=0.4,
                target_odds_min=4.0,
                target_odds_max=6.0,
                bankroll_percentage=0.03,  # 3% of bankroll
                description='High confidence with controlled risk'
            ),
            'medium_risk': RiskProfile(
                name='Medium Risk (10-odds)',
                min_confidence=0.85,  # 85%+ confidence
                max_games=4,
                max_correlation=0.5,
                target_odds_min=8.0,
                target_odds_max=12.0,
                bankroll_percentage=0.02,  # 2% of bankroll
                description='Balanced risk-reward with diversification'
            ),
            'conservative_rollover': RiskProfile(
                name='Conservative Rollover',
                min_confidence=0.88,  # 88%+ confidence
                max_games=3,
                max_correlation=0.35,
                target_odds_min=3.0,
                target_odds_max=8.0,
                bankroll_percentage=0.025,  # 2.5% of bankroll
                description='Conservative growth strategy'
            )
        }
    
    def filter_high_confidence_predictions(self, predictions: List[Dict], 
                                         min_confidence: float = 0.85) -> List[Dict]:
        """Filter predictions based on confidence threshold."""
        try:
            high_confidence_predictions = []
            
            for prediction in predictions:
                ml_predictions = prediction.get('ml_predictions', {})
                
                # Check each prediction type for confidence
                for pred_type, pred_data in ml_predictions.items():
                    confidence = pred_data.get('confidence', 0.0)
                    
                    if confidence >= min_confidence:
                        # Create enhanced prediction with risk metadata
                        enhanced_prediction = {
                            'fixture_info': prediction.get('fixture_info', {}),
                            'prediction_type': pred_type,
                            'prediction_value': pred_data.get('prediction'),
                            'confidence': confidence,
                            'model_type': pred_data.get('model_type', 'enhanced'),
                            'risk_score': self._calculate_risk_score(pred_data, prediction),
                            'estimated_odds': self._estimate_odds_from_confidence(confidence),
                            'correlation_group': self._get_correlation_group(pred_type)
                        }
                        high_confidence_predictions.append(enhanced_prediction)
            
            logger.info(f"✅ Filtered {len(high_confidence_predictions)} high-confidence predictions (>{min_confidence:.0%})")
            return high_confidence_predictions
            
        except Exception as e:
            logger.error(f"Error filtering high-confidence predictions: {str(e)}")
            return []
    
    def _calculate_risk_score(self, pred_data: Dict, prediction: Dict) -> float:
        """Calculate risk score for a prediction (0.0 = lowest risk, 1.0 = highest risk)."""
        try:
            confidence = pred_data.get('confidence', 0.0)
            
            # Base risk from confidence (higher confidence = lower risk)
            confidence_risk = 1.0 - confidence
            
            # League risk (major leagues = lower risk)
            league = prediction.get('fixture_info', {}).get('league', '').lower()
            league_risk = 0.1 if any(major in league for major in 
                                   ['premier league', 'la liga', 'bundesliga', 'serie a', 'ligue 1']) else 0.3
            
            # Prediction type risk
            pred_type = pred_data.get('prediction_type', '')
            type_risk = {
                'match_result': 0.2,
                'over_under': 0.3,
                'btts': 0.4,
                'clean_sheet_home': 0.3,
                'clean_sheet_away': 0.3,
                'win_to_nil_home': 0.5,
                'win_to_nil_away': 0.5
            }.get(pred_type, 0.4)
            
            # Combined risk score
            risk_score = (confidence_risk * 0.6) + (league_risk * 0.2) + (type_risk * 0.2)
            return min(max(risk_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {str(e)}")
            return 0.5  # Default medium risk
    
    def _estimate_odds_from_confidence(self, confidence: float) -> float:
        """Estimate betting odds from prediction confidence."""
        try:
            # Convert confidence to implied probability and then to decimal odds
            # Add small buffer to account for bookmaker margin
            implied_prob = confidence * 0.95  # 5% margin adjustment
            odds = 1.0 / implied_prob if implied_prob > 0 else 2.0
            
            # Clamp odds to reasonable range
            return min(max(odds, 1.1), 10.0)
            
        except Exception as e:
            logger.error(f"Error estimating odds: {str(e)}")
            return 2.0
    
    def _get_correlation_group(self, prediction_type: str) -> str:
        """Get correlation group for prediction type to avoid correlated bets."""
        correlation_groups = {
            'match_result': 'match_outcome',
            'over_under': 'goals',
            'btts': 'goals',
            'clean_sheet_home': 'goals',
            'clean_sheet_away': 'goals',
            'win_to_nil_home': 'match_outcome',
            'win_to_nil_away': 'match_outcome'
        }
        return correlation_groups.get(prediction_type, 'other')
    
    def build_risk_optimized_accumulators(self, predictions: List[Dict]) -> Dict[str, Any]:
        """Build risk-optimized accumulators based on risk profiles."""
        try:
            logger.info("🎯 Building risk-optimized accumulators...")
            
            risk_accumulators = {}
            
            for profile_name, profile in self.risk_profiles.items():
                logger.info(f"Building {profile.name} accumulator...")
                
                # Filter predictions by confidence
                filtered_predictions = self.filter_high_confidence_predictions(
                    predictions, profile.min_confidence
                )
                
                if not filtered_predictions:
                    risk_accumulators[profile_name] = {
                        'selected': False,
                        'reason': f'No predictions meet {profile.min_confidence:.0%} confidence threshold',
                        'profile': profile.__dict__
                    }
                    continue
                
                # Build accumulator with diversification
                accumulator = self._build_diversified_accumulator(
                    filtered_predictions, profile
                )
                
                risk_accumulators[profile_name] = accumulator
            
            logger.info(f"✅ Built {len(risk_accumulators)} risk-optimized accumulators")
            return {'accumulators': risk_accumulators}
            
        except Exception as e:
            logger.error(f"Error building risk-optimized accumulators: {str(e)}")
            return {'accumulators': {}}
    
    def _build_diversified_accumulator(self, predictions: List[Dict], 
                                     profile: RiskProfile) -> Dict[str, Any]:
        """Build a diversified accumulator based on risk profile."""
        try:
            # Sort by confidence (highest first)
            sorted_predictions = sorted(predictions, key=lambda x: x['confidence'], reverse=True)
            
            selected_games = []
            used_correlation_groups = set()
            total_odds = 1.0
            
            for prediction in sorted_predictions:
                if len(selected_games) >= profile.max_games:
                    break
                
                correlation_group = prediction['correlation_group']
                
                # Avoid correlated predictions
                if correlation_group in used_correlation_groups and profile.max_correlation < 0.5:
                    continue
                
                # Check if adding this game keeps us within odds range
                estimated_odds = prediction['estimated_odds']
                potential_total_odds = total_odds * estimated_odds
                
                if potential_total_odds > profile.target_odds_max:
                    continue
                
                # Add game to accumulator
                selected_games.append({
                    'fixture_id': prediction['fixture_info'].get('fixture_id'),
                    'home_team': prediction['fixture_info'].get('home_team'),
                    'away_team': prediction['fixture_info'].get('away_team'),
                    'league': prediction['fixture_info'].get('league'),
                    'prediction_type': prediction['prediction_type'],
                    'prediction_value': prediction['prediction_value'],
                    'confidence': prediction['confidence'],
                    'estimated_odds': estimated_odds,
                    'risk_score': prediction['risk_score'],
                    'readable_prediction': self._format_readable_prediction(
                        prediction['prediction_type'], 
                        prediction['prediction_value'],
                        prediction['fixture_info']
                    )
                })
                
                used_correlation_groups.add(correlation_group)
                total_odds *= estimated_odds
            
            # Check if accumulator meets criteria
            if (len(selected_games) >= 2 and 
                profile.target_odds_min <= total_odds <= profile.target_odds_max):
                
                # Calculate metrics
                avg_confidence = sum(g['confidence'] for g in selected_games) / len(selected_games)
                avg_risk_score = sum(g['risk_score'] for g in selected_games) / len(selected_games)
                diversity_score = len(used_correlation_groups) / len(selected_games)
                
                return {
                    'selected': True,
                    'games': selected_games,
                    'total_odds': round(total_odds, 2),
                    'game_count': len(selected_games),
                    'average_confidence': avg_confidence,
                    'average_risk_score': avg_risk_score,
                    'diversity_score': diversity_score,
                    'risk_level': self._assess_risk_level(avg_risk_score),
                    'recommended_stake': profile.bankroll_percentage,
                    'profile': profile.__dict__,
                    'expected_value': self._calculate_expected_value(selected_games, total_odds)
                }
            else:
                return {
                    'selected': False,
                    'reason': f'Could not build accumulator within {profile.target_odds_min}-{profile.target_odds_max} odds range',
                    'games_found': len(selected_games),
                    'total_odds': round(total_odds, 2),
                    'profile': profile.__dict__
                }
                
        except Exception as e:
            logger.error(f"Error building diversified accumulator: {str(e)}")
            return {
                'selected': False,
                'reason': f'Error building accumulator: {str(e)}',
                'profile': profile.__dict__
            }
    
    def _format_readable_prediction(self, pred_type: str, pred_value: str, fixture_info: Dict) -> str:
        """Format prediction into readable text."""
        home_team = fixture_info.get('home_team', 'Home')
        away_team = fixture_info.get('away_team', 'Away')
        
        if pred_type == 'match_result':
            if pred_value == '0':
                return f'{home_team} to Win'
            elif pred_value == '1':
                return f'{away_team} to Win'
            else:
                return 'Draw'
        elif pred_type == 'over_under':
            return 'Over 2.5 Goals' if pred_value == '1' else 'Under 2.5 Goals'
        elif pred_type == 'btts':
            return 'Both Teams to Score' if pred_value == '1' else 'Both Teams NOT to Score'
        elif pred_type == 'clean_sheet_home':
            return f'{home_team} Clean Sheet' if pred_value == '1' else f'{home_team} NOT Clean Sheet'
        elif pred_type == 'clean_sheet_away':
            return f'{away_team} Clean Sheet' if pred_value == '1' else f'{away_team} NOT Clean Sheet'
        elif pred_type == 'win_to_nil_home':
            return f'{home_team} to Win to Nil' if pred_value == '1' else f'{home_team} NOT to Win to Nil'
        elif pred_type == 'win_to_nil_away':
            return f'{away_team} to Win to Nil' if pred_value == '1' else f'{away_team} NOT to Win to Nil'
        else:
            return f'{pred_type}: {pred_value}'
    
    def _assess_risk_level(self, avg_risk_score: float) -> str:
        """Assess risk level based on average risk score."""
        if avg_risk_score <= 0.2:
            return 'very_low'
        elif avg_risk_score <= 0.4:
            return 'low'
        elif avg_risk_score <= 0.6:
            return 'medium'
        elif avg_risk_score <= 0.8:
            return 'high'
        else:
            return 'very_high'
    
    def _calculate_expected_value(self, games: List[Dict], total_odds: float) -> float:
        """Calculate expected value of the accumulator."""
        try:
            # Probability of winning = product of individual confidences
            win_probability = 1.0
            for game in games:
                win_probability *= game['confidence']
            
            # Expected value = (win_probability * payout) - stake
            # Assuming stake of 1 unit
            expected_payout = total_odds * win_probability
            expected_value = expected_payout - 1.0
            
            return round(expected_value, 3)
            
        except Exception as e:
            logger.error(f"Error calculating expected value: {str(e)}")
            return 0.0
    
    def get_bankroll_recommendations(self, bankroll: float, 
                                   accumulators: Dict[str, Any]) -> Dict[str, Any]:
        """Get bankroll management recommendations."""
        try:
            recommendations = {
                'total_bankroll': bankroll,
                'daily_risk_limit': bankroll * 0.05,  # Max 5% per day
                'recommendations': {}
            }
            
            total_recommended_stake = 0.0
            
            for acc_type, acc_data in accumulators.items():
                if acc_data.get('selected', False):
                    profile = self.risk_profiles.get(acc_type)
                    if profile:
                        stake_amount = bankroll * profile.bankroll_percentage
                        total_recommended_stake += stake_amount
                        
                        recommendations['recommendations'][acc_type] = {
                            'stake_amount': round(stake_amount, 2),
                            'stake_percentage': profile.bankroll_percentage,
                            'potential_return': round(stake_amount * acc_data['total_odds'], 2),
                            'expected_value': acc_data.get('expected_value', 0.0),
                            'risk_level': acc_data.get('risk_level', 'medium')
                        }
            
            recommendations['total_stake'] = round(total_recommended_stake, 2)
            recommendations['remaining_bankroll'] = round(bankroll - total_recommended_stake, 2)
            recommendations['risk_utilization'] = round(total_recommended_stake / bankroll, 3)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating bankroll recommendations: {str(e)}")
            return {'error': str(e)}
