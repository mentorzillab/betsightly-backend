#!/usr/bin/env python3
"""
Immediate Improvements for Better Predictions
Shows how to achieve 60%+ accuracy with current setup.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import lightgbm as lgb
import joblib

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from train_models_real_data import RealDataTrainer

class ImmediateImprovements:
    """Immediate improvements to boost accuracy to 60%+."""
    
    def __init__(self):
        """Initialize the improvement trainer."""
        self.real_data_trainer = RealDataTrainer()
        
    def add_team_form_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add basic team form features for immediate improvement."""
        print("🔧 Adding team form features...")
        
        # Sort by date
        df = df.sort_values('date').reset_index(drop=True)
        
        # Initialize form features
        df['home_team_form_5g'] = 0.0  # Points per game in last 5
        df['away_team_form_5g'] = 0.0
        df['home_team_goals_5g'] = 0.0  # Goals per game in last 5
        df['away_team_goals_5g'] = 0.0
        df['home_team_conceded_5g'] = 0.0  # Goals conceded per game in last 5
        df['away_team_conceded_5g'] = 0.0
        
        # Calculate form for each team
        teams = set(df['home_team'].unique()) | set(df['away_team'].unique())
        
        for team in teams:
            # Get all matches for this team
            team_matches = df[
                (df['home_team'] == team) | (df['away_team'] == team)
            ].copy().sort_values('date')
            
            for i, (idx, match) in enumerate(team_matches.iterrows()):
                if i >= 5:  # Need at least 5 previous games
                    # Get last 5 games
                    recent_matches = team_matches.iloc[i-5:i]
                    
                    points = 0
                    goals_for = 0
                    goals_against = 0
                    
                    for _, recent_match in recent_matches.iterrows():
                        if recent_match['home_team'] == team:
                            # Team was playing at home
                            goals_for += recent_match['home_score']
                            goals_against += recent_match['away_score']
                            
                            if recent_match['home_score'] > recent_match['away_score']:
                                points += 3  # Win
                            elif recent_match['home_score'] == recent_match['away_score']:
                                points += 1  # Draw
                        else:
                            # Team was playing away
                            goals_for += recent_match['away_score']
                            goals_against += recent_match['home_score']
                            
                            if recent_match['away_score'] > recent_match['home_score']:
                                points += 3  # Win
                            elif recent_match['away_score'] == recent_match['home_score']:
                                points += 1  # Draw
                    
                    # Calculate averages
                    form = points / 5  # Points per game
                    goals_avg = goals_for / 5  # Goals per game
                    conceded_avg = goals_against / 5  # Conceded per game
                    
                    # Update the current match row
                    if match['home_team'] == team:
                        df.loc[idx, 'home_team_form_5g'] = form
                        df.loc[idx, 'home_team_goals_5g'] = goals_avg
                        df.loc[idx, 'home_team_conceded_5g'] = conceded_avg
                    else:
                        df.loc[idx, 'away_team_form_5g'] = form
                        df.loc[idx, 'away_team_goals_5g'] = goals_avg
                        df.loc[idx, 'away_team_conceded_5g'] = conceded_avg
        
        # Add form difference features
        df['form_difference'] = df['home_team_form_5g'] - df['away_team_form_5g']
        df['attack_difference'] = df['home_team_goals_5g'] - df['away_team_goals_5g']
        df['defense_difference'] = df['away_team_conceded_5g'] - df['home_team_conceded_5g']  # Lower is better
        
        print(f"✅ Added {6} form features")
        return df
    
    def add_head_to_head_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add head-to-head features."""
        print("🥊 Adding head-to-head features...")
        
        df['h2h_home_wins_last_5'] = 0
        df['h2h_draws_last_5'] = 0
        df['h2h_away_wins_last_5'] = 0
        df['h2h_avg_goals_last_5'] = 0.0
        
        for i, (idx, match) in enumerate(df.iterrows()):
            home_team = match['home_team']
            away_team = match['away_team']
            
            # Find last 5 meetings between these teams
            h2h_matches = df.iloc[:i][
                ((df.iloc[:i]['home_team'] == home_team) & (df.iloc[:i]['away_team'] == away_team)) |
                ((df.iloc[:i]['home_team'] == away_team) & (df.iloc[:i]['away_team'] == home_team))
            ].tail(5)  # Last 5 meetings
            
            if len(h2h_matches) > 0:
                home_wins = 0
                draws = 0
                away_wins = 0
                total_goals = 0
                
                for _, h2h_match in h2h_matches.iterrows():
                    total_goals += h2h_match['home_score'] + h2h_match['away_score']
                    
                    # Determine result from current home team's perspective
                    if h2h_match['home_team'] == home_team:
                        # Current home team was home in h2h
                        if h2h_match['home_score'] > h2h_match['away_score']:
                            home_wins += 1
                        elif h2h_match['home_score'] == h2h_match['away_score']:
                            draws += 1
                        else:
                            away_wins += 1
                    else:
                        # Current home team was away in h2h
                        if h2h_match['away_score'] > h2h_match['home_score']:
                            home_wins += 1
                        elif h2h_match['away_score'] == h2h_match['home_score']:
                            draws += 1
                        else:
                            away_wins += 1
                
                df.loc[idx, 'h2h_home_wins_last_5'] = home_wins
                df.loc[idx, 'h2h_draws_last_5'] = draws
                df.loc[idx, 'h2h_away_wins_last_5'] = away_wins
                df.loc[idx, 'h2h_avg_goals_last_5'] = total_goals / len(h2h_matches)
        
        print(f"✅ Added 4 head-to-head features")
        return df
    
    def add_league_strength_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add league strength features."""
        print("🏆 Adding league strength features...")
        
        # Calculate league averages
        league_stats = df.groupby('league').agg({
            'total_goals': 'mean',
            'over_2_5': 'mean',
            'btts': 'mean',
            'home_odds': 'mean',
            'away_odds': 'mean'
        })
        
        # Add league features
        df = df.merge(league_stats, left_on='league', right_index=True, suffixes=('', '_league_avg'))
        
        # League strength indicator (lower odds = stronger league)
        df['league_strength'] = 1.0 / ((df['home_odds_league_avg'] + df['away_odds_league_avg']) / 2)
        
        # How this match compares to league average
        df['goals_vs_league_avg'] = (df['home_team_goals_5g'] + df['away_team_goals_5g']) - df['total_goals_league_avg']
        
        print(f"✅ Added 6 league strength features")
        return df
    
    def create_optimized_models(self) -> dict:
        """Create optimized models with better hyperparameters."""
        print("🤖 Creating optimized models...")
        
        models = {}
        
        # Optimized XGBoost
        models['xgb_optimized'] = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )
        
        # Optimized LightGBM
        models['lgb_optimized'] = lgb.LGBMClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbose=-1
        )
        
        # Optimized Random Forest
        models['rf_optimized'] = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        
        # Voting Ensemble
        models['voting_ensemble'] = VotingClassifier([
            ('xgb', models['xgb_optimized']),
            ('lgb', models['lgb_optimized']),
            ('rf', models['rf_optimized'])
        ], voting='soft')
        
        return models
    
    def train_improved_models(self):
        """Train models with immediate improvements."""
        print("🚀 TRAINING IMPROVED MODELS")
        print("=" * 60)
        
        # Get real data
        print("📥 Loading real data...")
        real_data = self.real_data_trainer.combine_all_data_sources()
        
        if len(real_data) < 1000:
            print("❌ Not enough data for training")
            return
        
        print(f"✅ Loaded {len(real_data):,} games")
        
        # Add improved features
        print("\n🔧 Adding improved features...")
        enhanced_data = self.add_team_form_features(real_data)
        enhanced_data = self.add_head_to_head_features(enhanced_data)
        enhanced_data = self.add_league_strength_features(enhanced_data)
        
        print(f"✅ Enhanced dataset: {enhanced_data.shape[1]} features")
        
        # Prepare features (simplified version)
        print("\n📊 Preparing features for training...")
        
        # Select numeric features only
        feature_columns = [col for col in enhanced_data.columns 
                          if enhanced_data[col].dtype in ['int64', 'float64'] 
                          and col not in ['home_score', 'away_score', 'match_result', 'total_goals', 'over_2_5', 'btts']]
        
        X = enhanced_data[feature_columns].fillna(0)
        
        # Test on match_result prediction
        y = enhanced_data['match_result']
        
        # Remove rows with missing targets
        valid_rows = ~y.isna()
        X = X[valid_rows]
        y = y[valid_rows]
        
        print(f"📊 Training data: {X.shape[0]} samples, {X.shape[1]} features")
        
        # Create and test models
        models = self.create_optimized_models()
        
        print("\n🎯 Testing model performance...")
        results = {}
        
        for name, model in models.items():
            try:
                # Cross-validation
                scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
                avg_score = scores.mean()
                results[name] = avg_score
                
                print(f"   {name}: {avg_score:.3f} accuracy ({avg_score*100:.1f}%)")
                
            except Exception as e:
                print(f"   ❌ {name}: Error - {str(e)}")
        
        # Show improvement
        print(f"\n📈 IMPROVEMENT SUMMARY:")
        print(f"   🔥 Best Model: {max(results.items(), key=lambda x: x[1])[0]}")
        print(f"   🎯 Best Accuracy: {max(results.values()):.1f}%")
        print(f"   📊 Improvement: +{(max(results.values()) - 0.42)*100:.1f}% vs baseline")
        
        if max(results.values()) > 0.60:
            print(f"   🎉 TARGET ACHIEVED: 60%+ accuracy!")
        else:
            print(f"   💪 Progress made, need more features for 60%+")

def main():
    """Main function."""
    print("🚀 IMMEDIATE IMPROVEMENTS FOR BETTER PREDICTIONS")
    print("=" * 70)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Goal: Achieve 60%+ accuracy with current data")
    print("=" * 70)
    
    trainer = ImmediateImprovements()
    trainer.train_improved_models()
    
    print("\n💡 NEXT STEPS FOR EVEN BETTER PREDICTIONS:")
    print("   1. Add more historical data (5+ years)")
    print("   2. Include player-level statistics")
    print("   3. Add weather and venue data")
    print("   4. Implement ensemble methods")
    print("   5. Use hyperparameter optimization")
    print("=" * 70)

if __name__ == "__main__":
    main()
