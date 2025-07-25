#!/usr/bin/env python3
"""
Enhanced Feature Extractor for Real-time Predictions

This service generates the exact 62 features that our enhanced models expect
during real-time prediction, matching the training feature format.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

logger = logging.getLogger(__name__)

class EnhancedFeatureExtractor:
    """
    Extract the exact 62 features that enhanced models expect.
    
    Features generated:
    1. Odds features (3): home_odds, draw_odds, away_odds
    2. Team form features (23): Various form metrics over 3, 5, 10 games
    3. Head-to-head features (18): Historical matchup analysis
    4. Venue-specific features (18): Home/away performance analysis
    """
    
    def __init__(self):
        """Initialize the enhanced feature extractor."""
        self.historical_data = None
        self.feature_columns = [
            'home_odds', 'draw_odds', 'away_odds',
            'home_team_form_3g', 'away_team_form_3g', 'home_team_form_5g', 'away_team_form_5g',
            'home_team_form_10g', 'away_team_form_10g', 'home_team_goals_3g', 'away_team_goals_3g',
            'home_team_goals_5g', 'away_team_goals_5g', 'home_team_conceded_3g', 'away_team_conceded_3g',
            'home_team_conceded_5g', 'away_team_conceded_5g', 'home_team_wins_5g', 'away_team_wins_5g',
            'home_team_clean_sheets_5g', 'away_team_clean_sheets_5g', 'form_difference_5g',
            'attack_difference_5g', 'defense_difference_5g', 'form_momentum_home', 'form_momentum_away',
            'h2h_total_meetings', 'h2h_home_wins_all', 'h2h_draws_all', 'h2h_away_wins_all',
            'h2h_home_win_rate', 'h2h_avg_goals_all', 'h2h_over_2_5_rate', 'h2h_btts_rate',
            'h2h_home_goals_avg', 'h2h_away_goals_avg', 'h2h_last_5_home_wins', 'h2h_last_5_draws',
            'h2h_last_5_away_wins', 'h2h_last_5_avg_goals', 'h2h_recent_trend', 'h2h_home_advantage',
            'h2h_goal_difference_avg', 'h2h_days_since_last_meeting', 'home_team_home_form_5g',
            'home_team_home_goals_5g', 'home_team_home_conceded_5g', 'home_team_home_wins_5g',
            'home_team_home_clean_sheets_5g', 'away_team_away_form_5g', 'away_team_away_goals_5g',
            'away_team_away_conceded_5g', 'away_team_away_wins_5g', 'away_team_away_clean_sheets_5g',
            'home_advantage_strength', 'venue_form_difference', 'venue_attack_difference',
            'venue_defense_difference', 'home_team_home_streak', 'away_team_away_streak',
            'home_team_home_last_result', 'away_team_away_last_result'
        ]
        
        # Load historical data for feature calculation
        self._load_historical_data()
        
        logger.info(f"Enhanced Feature Extractor initialized with {len(self.feature_columns)} features")
    
    def _load_historical_data(self):
        """Load historical data for feature calculation."""
        try:
            # Try to load the enhanced dataset
            if os.path.exists('data/enhanced_dataset_complete.pkl'):
                self.historical_data = pd.read_pickle('data/enhanced_dataset_complete.pkl')
                logger.info(f"Loaded enhanced historical data: {len(self.historical_data)} matches")
            elif os.path.exists('real_football_data.csv'):
                self.historical_data = pd.read_csv('real_football_data.csv')
                logger.info(f"Loaded basic historical data: {len(self.historical_data)} matches")
            else:
                logger.warning("No historical data found - using default values")
                self.historical_data = None
        except Exception as e:
            logger.error(f"Error loading historical data: {str(e)}")
            self.historical_data = None
    
    def extract_fixture_features(self, fixture: Dict[str, Any]) -> Optional[np.ndarray]:
        """
        Extract the exact 62 features for a fixture that enhanced models expect.
        
        Args:
            fixture: Fixture data from API
            
        Returns:
            numpy array with 62 features in correct order
        """
        try:
            # Extract basic fixture info
            home_team = fixture.get('home_team', '')
            away_team = fixture.get('away_team', '')
            league = fixture.get('league', '')
            
            # Get odds (with defaults if not available)
            home_odds = fixture.get('home_odds', 2.0)
            draw_odds = fixture.get('draw_odds', 3.5)
            away_odds = fixture.get('away_odds', 3.0)
            
            # Initialize feature dictionary
            features = {}
            
            # 1. Odds features (3 features)
            features['home_odds'] = home_odds
            features['draw_odds'] = draw_odds
            features['away_odds'] = away_odds
            
            # 2. Team form features (23 features)
            home_form = self._calculate_team_form(home_team, league)
            away_form = self._calculate_team_form(away_team, league)
            
            features.update({
                'home_team_form_3g': home_form['form_3g'],
                'away_team_form_3g': away_form['form_3g'],
                'home_team_form_5g': home_form['form_5g'],
                'away_team_form_5g': away_form['form_5g'],
                'home_team_form_10g': home_form['form_10g'],
                'away_team_form_10g': away_form['form_10g'],
                'home_team_goals_3g': home_form['goals_3g'],
                'away_team_goals_3g': away_form['goals_3g'],
                'home_team_goals_5g': home_form['goals_5g'],
                'away_team_goals_5g': away_form['goals_5g'],
                'home_team_conceded_3g': home_form['conceded_3g'],
                'away_team_conceded_3g': away_form['conceded_3g'],
                'home_team_conceded_5g': home_form['conceded_5g'],
                'away_team_conceded_5g': away_form['conceded_5g'],
                'home_team_wins_5g': home_form['wins_5g'],
                'away_team_wins_5g': away_form['wins_5g'],
                'home_team_clean_sheets_5g': home_form['clean_sheets_5g'],
                'away_team_clean_sheets_5g': away_form['clean_sheets_5g'],
                'form_difference_5g': home_form['form_5g'] - away_form['form_5g'],
                'attack_difference_5g': home_form['goals_5g'] - away_form['goals_5g'],
                'defense_difference_5g': away_form['conceded_5g'] - home_form['conceded_5g'],
                'form_momentum_home': home_form['momentum'],
                'form_momentum_away': away_form['momentum']
            })
            
            # 3. Head-to-head features (18 features)
            h2h_features = self._calculate_h2h_features(home_team, away_team)
            features.update(h2h_features)
            
            # 4. Venue-specific features (18 features)
            venue_features = self._calculate_venue_features(home_team, away_team, league)
            features.update(venue_features)
            
            # Convert to numpy array in correct order
            feature_array = np.array([features.get(col, 0.0) for col in self.feature_columns])
            
            logger.debug(f"Extracted {len(feature_array)} features for {home_team} vs {away_team}")
            return feature_array
            
        except Exception as e:
            logger.error(f"Error extracting features for fixture: {str(e)}")
            return None
    
    def _calculate_team_form(self, team: str, league: str) -> Dict[str, float]:
        """Calculate team form metrics."""
        if self.historical_data is None:
            # Return default values if no historical data
            return {
                'form_3g': 1.5, 'form_5g': 1.5, 'form_10g': 1.5,
                'goals_3g': 1.2, 'goals_5g': 1.2, 'conceded_3g': 1.0,
                'conceded_5g': 1.0, 'wins_5g': 2.0, 'clean_sheets_5g': 1.0,
                'momentum': 0.5
            }
        
        try:
            # Get team's recent matches
            team_matches = self.historical_data[
                (self.historical_data['home_team'] == team) | 
                (self.historical_data['away_team'] == team)
            ].sort_values('date', ascending=False).head(10)
            
            if len(team_matches) == 0:
                # Return defaults for unknown teams
                return {
                    'form_3g': 1.5, 'form_5g': 1.5, 'form_10g': 1.5,
                    'goals_3g': 1.2, 'goals_5g': 1.2, 'conceded_3g': 1.0,
                    'conceded_5g': 1.0, 'wins_5g': 2.0, 'clean_sheets_5g': 1.0,
                    'momentum': 0.5
                }
            
            # Calculate form metrics
            form_3g = self._calculate_form_points(team_matches.head(3), team)
            form_5g = self._calculate_form_points(team_matches.head(5), team)
            form_10g = self._calculate_form_points(team_matches.head(10), team)
            
            goals_3g = self._calculate_goals_scored(team_matches.head(3), team)
            goals_5g = self._calculate_goals_scored(team_matches.head(5), team)
            
            conceded_3g = self._calculate_goals_conceded(team_matches.head(3), team)
            conceded_5g = self._calculate_goals_conceded(team_matches.head(5), team)
            
            wins_5g = self._calculate_wins(team_matches.head(5), team)
            clean_sheets_5g = self._calculate_clean_sheets(team_matches.head(5), team)
            
            momentum = self._calculate_momentum(team_matches.head(5), team)
            
            return {
                'form_3g': form_3g, 'form_5g': form_5g, 'form_10g': form_10g,
                'goals_3g': goals_3g, 'goals_5g': goals_5g,
                'conceded_3g': conceded_3g, 'conceded_5g': conceded_5g,
                'wins_5g': wins_5g, 'clean_sheets_5g': clean_sheets_5g,
                'momentum': momentum
            }
            
        except Exception as e:
            logger.error(f"Error calculating team form for {team}: {str(e)}")
            return {
                'form_3g': 1.5, 'form_5g': 1.5, 'form_10g': 1.5,
                'goals_3g': 1.2, 'goals_5g': 1.2, 'conceded_3g': 1.0,
                'conceded_5g': 1.0, 'wins_5g': 2.0, 'clean_sheets_5g': 1.0,
                'momentum': 0.5
            }
    
    def _calculate_form_points(self, matches: pd.DataFrame, team: str) -> float:
        """Calculate form points (3 for win, 1 for draw, 0 for loss)."""
        if len(matches) == 0:
            return 1.5
        
        points = 0
        for _, match in matches.iterrows():
            if match['home_team'] == team:
                if match['home_score'] > match['away_score']:
                    points += 3
                elif match['home_score'] == match['away_score']:
                    points += 1
            else:
                if match['away_score'] > match['home_score']:
                    points += 3
                elif match['away_score'] == match['home_score']:
                    points += 1
        
        return points / len(matches)
    
    def _calculate_goals_scored(self, matches: pd.DataFrame, team: str) -> float:
        """Calculate average goals scored."""
        if len(matches) == 0:
            return 1.2
        
        goals = 0
        for _, match in matches.iterrows():
            if match['home_team'] == team:
                goals += match['home_score']
            else:
                goals += match['away_score']
        
        return goals / len(matches)
    
    def _calculate_goals_conceded(self, matches: pd.DataFrame, team: str) -> float:
        """Calculate average goals conceded."""
        if len(matches) == 0:
            return 1.0
        
        conceded = 0
        for _, match in matches.iterrows():
            if match['home_team'] == team:
                conceded += match['away_score']
            else:
                conceded += match['home_score']
        
        return conceded / len(matches)
    
    def _calculate_wins(self, matches: pd.DataFrame, team: str) -> float:
        """Calculate number of wins."""
        if len(matches) == 0:
            return 2.0
        
        wins = 0
        for _, match in matches.iterrows():
            if match['home_team'] == team:
                if match['home_score'] > match['away_score']:
                    wins += 1
            else:
                if match['away_score'] > match['home_score']:
                    wins += 1
        
        return float(wins)
    
    def _calculate_clean_sheets(self, matches: pd.DataFrame, team: str) -> float:
        """Calculate number of clean sheets."""
        if len(matches) == 0:
            return 1.0
        
        clean_sheets = 0
        for _, match in matches.iterrows():
            if match['home_team'] == team:
                if match['away_score'] == 0:
                    clean_sheets += 1
            else:
                if match['home_score'] == 0:
                    clean_sheets += 1
        
        return float(clean_sheets)
    
    def _calculate_momentum(self, matches: pd.DataFrame, team: str) -> float:
        """Calculate team momentum (recent form trend)."""
        if len(matches) < 3:
            return 0.5
        
        # Weight recent matches more heavily
        weights = [0.4, 0.3, 0.2, 0.1][:len(matches)]
        weighted_points = 0
        total_weight = 0
        
        for i, (_, match) in enumerate(matches.iterrows()):
            weight = weights[i] if i < len(weights) else 0.05
            
            if match['home_team'] == team:
                if match['home_score'] > match['away_score']:
                    points = 3
                elif match['home_score'] == match['away_score']:
                    points = 1
                else:
                    points = 0
            else:
                if match['away_score'] > match['home_score']:
                    points = 3
                elif match['away_score'] == match['home_score']:
                    points = 1
                else:
                    points = 0
            
            weighted_points += points * weight
            total_weight += weight
        
        return weighted_points / total_weight / 3.0  # Normalize to 0-1

    def _calculate_h2h_features(self, home_team: str, away_team: str) -> Dict[str, float]:
        """Calculate head-to-head features."""
        if self.historical_data is None:
            return self._get_default_h2h_features()

        try:
            # Get head-to-head matches
            h2h_matches = self.historical_data[
                ((self.historical_data['home_team'] == home_team) & (self.historical_data['away_team'] == away_team)) |
                ((self.historical_data['home_team'] == away_team) & (self.historical_data['away_team'] == home_team))
            ].sort_values('date', ascending=False)

            if len(h2h_matches) == 0:
                return self._get_default_h2h_features()

            # Calculate H2H statistics
            total_meetings = len(h2h_matches)
            home_wins_all = len(h2h_matches[
                ((h2h_matches['home_team'] == home_team) & (h2h_matches['home_score'] > h2h_matches['away_score'])) |
                ((h2h_matches['away_team'] == home_team) & (h2h_matches['away_score'] > h2h_matches['home_score']))
            ])
            away_wins_all = len(h2h_matches[
                ((h2h_matches['home_team'] == away_team) & (h2h_matches['home_score'] > h2h_matches['away_score'])) |
                ((h2h_matches['away_team'] == away_team) & (h2h_matches['away_score'] > h2h_matches['home_score']))
            ])
            draws_all = total_meetings - home_wins_all - away_wins_all

            home_win_rate = home_wins_all / total_meetings if total_meetings > 0 else 0.4

            # Calculate goal statistics
            total_goals = 0
            over_2_5_count = 0
            btts_count = 0
            home_goals_total = 0
            away_goals_total = 0

            for _, match in h2h_matches.iterrows():
                match_goals = match['home_score'] + match['away_score']
                total_goals += match_goals

                if match_goals > 2.5:
                    over_2_5_count += 1

                if match['home_score'] > 0 and match['away_score'] > 0:
                    btts_count += 1

                if match['home_team'] == home_team:
                    home_goals_total += match['home_score']
                    away_goals_total += match['away_score']
                else:
                    home_goals_total += match['away_score']
                    away_goals_total += match['home_score']

            avg_goals_all = total_goals / total_meetings if total_meetings > 0 else 2.5
            over_2_5_rate = over_2_5_count / total_meetings if total_meetings > 0 else 0.5
            btts_rate = btts_count / total_meetings if total_meetings > 0 else 0.5
            home_goals_avg = home_goals_total / total_meetings if total_meetings > 0 else 1.3
            away_goals_avg = away_goals_total / total_meetings if total_meetings > 0 else 1.2

            # Last 5 meetings
            last_5 = h2h_matches.head(5)
            last_5_home_wins = len(last_5[
                ((last_5['home_team'] == home_team) & (last_5['home_score'] > last_5['away_score'])) |
                ((last_5['away_team'] == home_team) & (last_5['away_score'] > last_5['home_score']))
            ])
            last_5_away_wins = len(last_5[
                ((last_5['home_team'] == away_team) & (last_5['home_score'] > last_5['away_score'])) |
                ((last_5['away_team'] == away_team) & (last_5['away_score'] > last_5['home_score']))
            ])
            last_5_draws = len(last_5) - last_5_home_wins - last_5_away_wins
            last_5_avg_goals = (last_5['home_score'] + last_5['away_score']).mean() if len(last_5) > 0 else 2.5

            # Recent trend and other features
            recent_trend = self._calculate_h2h_trend(last_5, home_team)
            home_advantage = home_win_rate - 0.5  # Advantage over neutral
            goal_difference_avg = home_goals_avg - away_goals_avg

            # Days since last meeting
            if len(h2h_matches) > 0:
                last_meeting = pd.to_datetime(h2h_matches.iloc[0]['date'])
                days_since = (datetime.now() - last_meeting).days
            else:
                days_since = 365

            return {
                'h2h_total_meetings': float(total_meetings),
                'h2h_home_wins_all': float(home_wins_all),
                'h2h_draws_all': float(draws_all),
                'h2h_away_wins_all': float(away_wins_all),
                'h2h_home_win_rate': home_win_rate,
                'h2h_avg_goals_all': avg_goals_all,
                'h2h_over_2_5_rate': over_2_5_rate,
                'h2h_btts_rate': btts_rate,
                'h2h_home_goals_avg': home_goals_avg,
                'h2h_away_goals_avg': away_goals_avg,
                'h2h_last_5_home_wins': float(last_5_home_wins),
                'h2h_last_5_draws': float(last_5_draws),
                'h2h_last_5_away_wins': float(last_5_away_wins),
                'h2h_last_5_avg_goals': last_5_avg_goals,
                'h2h_recent_trend': recent_trend,
                'h2h_home_advantage': home_advantage,
                'h2h_goal_difference_avg': goal_difference_avg,
                'h2h_days_since_last_meeting': float(days_since)
            }

        except Exception as e:
            logger.error(f"Error calculating H2H features: {str(e)}")
            return self._get_default_h2h_features()

    def _get_default_h2h_features(self) -> Dict[str, float]:
        """Get default H2H features when no data available."""
        return {
            'h2h_total_meetings': 5.0,
            'h2h_home_wins_all': 2.0,
            'h2h_draws_all': 1.0,
            'h2h_away_wins_all': 2.0,
            'h2h_home_win_rate': 0.4,
            'h2h_avg_goals_all': 2.5,
            'h2h_over_2_5_rate': 0.5,
            'h2h_btts_rate': 0.5,
            'h2h_home_goals_avg': 1.3,
            'h2h_away_goals_avg': 1.2,
            'h2h_last_5_home_wins': 2.0,
            'h2h_last_5_draws': 1.0,
            'h2h_last_5_away_wins': 2.0,
            'h2h_last_5_avg_goals': 2.5,
            'h2h_recent_trend': 0.5,
            'h2h_home_advantage': 0.1,
            'h2h_goal_difference_avg': 0.1,
            'h2h_days_since_last_meeting': 180.0
        }

    def _calculate_h2h_trend(self, matches: pd.DataFrame, home_team: str) -> float:
        """Calculate recent H2H trend for home team."""
        if len(matches) == 0:
            return 0.5

        trend_score = 0
        for i, (_, match) in enumerate(matches.iterrows()):
            weight = 1.0 / (i + 1)  # More recent matches weighted higher

            if match['home_team'] == home_team:
                if match['home_score'] > match['away_score']:
                    trend_score += weight
                elif match['home_score'] == match['away_score']:
                    trend_score += weight * 0.5
            else:
                if match['away_score'] > match['home_score']:
                    trend_score += weight
                elif match['away_score'] == match['home_score']:
                    trend_score += weight * 0.5

        max_possible = sum(1.0 / (i + 1) for i in range(len(matches)))
        return trend_score / max_possible if max_possible > 0 else 0.5

    def _calculate_venue_features(self, home_team: str, away_team: str, league: str) -> Dict[str, float]:
        """Calculate venue-specific features."""
        if self.historical_data is None:
            return self._get_default_venue_features()

        try:
            # Get home team's home matches
            home_matches = self.historical_data[
                self.historical_data['home_team'] == home_team
            ].sort_values('date', ascending=False).head(5)

            # Get away team's away matches
            away_matches = self.historical_data[
                self.historical_data['away_team'] == away_team
            ].sort_values('date', ascending=False).head(5)

            # Calculate home team's home form
            home_form_5g = self._calculate_form_points(home_matches, home_team)
            home_goals_5g = self._calculate_goals_scored(home_matches, home_team)
            home_conceded_5g = self._calculate_goals_conceded(home_matches, home_team)
            home_wins_5g = self._calculate_wins(home_matches, home_team)
            home_clean_sheets_5g = self._calculate_clean_sheets(home_matches, home_team)

            # Calculate away team's away form
            away_form_5g = self._calculate_form_points(away_matches, away_team)
            away_goals_5g = self._calculate_goals_scored(away_matches, away_team)
            away_conceded_5g = self._calculate_goals_conceded(away_matches, away_team)
            away_wins_5g = self._calculate_wins(away_matches, away_team)
            away_clean_sheets_5g = self._calculate_clean_sheets(away_matches, away_team)

            # Calculate venue advantages
            home_advantage_strength = self._calculate_home_advantage(home_team, league)
            venue_form_difference = home_form_5g - away_form_5g
            venue_attack_difference = home_goals_5g - away_goals_5g
            venue_defense_difference = away_conceded_5g - home_conceded_5g

            # Calculate streaks
            home_streak = self._calculate_home_streak(home_matches, home_team)
            away_streak = self._calculate_away_streak(away_matches, away_team)

            # Last results
            home_last_result = self._get_last_result(home_matches, home_team) if len(home_matches) > 0 else 1.0
            away_last_result = self._get_last_result(away_matches, away_team) if len(away_matches) > 0 else 1.0

            return {
                'home_team_home_form_5g': home_form_5g,
                'home_team_home_goals_5g': home_goals_5g,
                'home_team_home_conceded_5g': home_conceded_5g,
                'home_team_home_wins_5g': home_wins_5g,
                'home_team_home_clean_sheets_5g': home_clean_sheets_5g,
                'away_team_away_form_5g': away_form_5g,
                'away_team_away_goals_5g': away_goals_5g,
                'away_team_away_conceded_5g': away_conceded_5g,
                'away_team_away_wins_5g': away_wins_5g,
                'away_team_away_clean_sheets_5g': away_clean_sheets_5g,
                'home_advantage_strength': home_advantage_strength,
                'venue_form_difference': venue_form_difference,
                'venue_attack_difference': venue_attack_difference,
                'venue_defense_difference': venue_defense_difference,
                'home_team_home_streak': home_streak,
                'away_team_away_streak': away_streak,
                'home_team_home_last_result': home_last_result,
                'away_team_away_last_result': away_last_result
            }

        except Exception as e:
            logger.error(f"Error calculating venue features: {str(e)}")
            return self._get_default_venue_features()

    def _get_default_venue_features(self) -> Dict[str, float]:
        """Get default venue features when no data available."""
        return {
            'home_team_home_form_5g': 1.8,
            'home_team_home_goals_5g': 1.5,
            'home_team_home_conceded_5g': 0.8,
            'home_team_home_wins_5g': 3.0,
            'home_team_home_clean_sheets_5g': 2.0,
            'away_team_away_form_5g': 1.2,
            'away_team_away_goals_5g': 1.0,
            'away_team_away_conceded_5g': 1.2,
            'away_team_away_wins_5g': 2.0,
            'away_team_away_clean_sheets_5g': 1.0,
            'home_advantage_strength': 0.3,
            'venue_form_difference': 0.6,
            'venue_attack_difference': 0.5,
            'venue_defense_difference': 0.4,
            'home_team_home_streak': 2.0,
            'away_team_away_streak': 1.0,
            'home_team_home_last_result': 1.0,
            'away_team_away_last_result': 0.0
        }

    def _calculate_home_advantage(self, home_team: str, league: str) -> float:
        """Calculate home advantage strength."""
        if self.historical_data is None:
            return 0.3

        try:
            home_matches = self.historical_data[self.historical_data['home_team'] == home_team]
            if len(home_matches) == 0:
                return 0.3

            home_wins = len(home_matches[home_matches['home_score'] > home_matches['away_score']])
            home_win_rate = home_wins / len(home_matches)

            # League average home win rate is typically around 45%
            league_avg = 0.45
            return max(0.0, min(1.0, home_win_rate - league_avg + 0.3))

        except Exception:
            return 0.3

    def _calculate_home_streak(self, matches: pd.DataFrame, team: str) -> float:
        """Calculate current home streak."""
        if len(matches) == 0:
            return 2.0

        streak = 0
        for _, match in matches.iterrows():
            if match['home_score'] > match['away_score']:
                streak += 1
            else:
                break

        return float(streak)

    def _calculate_away_streak(self, matches: pd.DataFrame, team: str) -> float:
        """Calculate current away streak."""
        if len(matches) == 0:
            return 1.0

        streak = 0
        for _, match in matches.iterrows():
            if match['away_score'] > match['home_score']:
                streak += 1
            else:
                break

        return float(streak)

    def _get_last_result(self, matches: pd.DataFrame, team: str) -> float:
        """Get last match result (3=win, 1=draw, 0=loss)."""
        if len(matches) == 0:
            return 1.0

        last_match = matches.iloc[0]

        if team == last_match['home_team']:
            if last_match['home_score'] > last_match['away_score']:
                return 3.0
            elif last_match['home_score'] == last_match['away_score']:
                return 1.0
            else:
                return 0.0
        else:
            if last_match['away_score'] > last_match['home_score']:
                return 3.0
            elif last_match['away_score'] == last_match['home_score']:
                return 1.0
            else:
                return 0.0
