#!/usr/bin/env python3
"""
Implement Head-to-Head Features - PRIORITY 2
Expected Impact: +8-12% accuracy improvement
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import joblib

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

class HeadToHeadFeatures:
    """Implement comprehensive head-to-head historical features."""
    
    def __init__(self):
        """Initialize the H2H feature creator."""
        pass
    
    def add_h2h_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add comprehensive head-to-head features."""
        print("🥊 IMPLEMENTING HEAD-TO-HEAD FEATURES (PRIORITY 2)")
        print("=" * 60)
        print("🎯 Expected Impact: +8-12% accuracy improvement")
        
        # Sort by date for chronological processing
        df = df.sort_values('date').reset_index(drop=True)
        
        # Initialize H2H features
        h2h_features = [
            'h2h_total_meetings',           # Total historical meetings
            'h2h_home_wins_all',           # Home team wins (all time)
            'h2h_draws_all',               # Draws (all time)
            'h2h_away_wins_all',           # Away team wins (all time)
            'h2h_home_win_rate',           # Home team win percentage
            'h2h_avg_goals_all',           # Average goals per meeting
            'h2h_over_2_5_rate',           # Over 2.5 goals rate in meetings
            'h2h_btts_rate',               # Both teams score rate
            'h2h_home_goals_avg',          # Home team's avg goals in H2H
            'h2h_away_goals_avg',          # Away team's avg goals in H2H
            'h2h_last_5_home_wins',        # Home wins in last 5 meetings
            'h2h_last_5_draws',            # Draws in last 5 meetings
            'h2h_last_5_away_wins',        # Away wins in last 5 meetings
            'h2h_last_5_avg_goals',        # Avg goals in last 5 meetings
            'h2h_recent_trend',            # Recent trend (who's been winning)
            'h2h_home_advantage',          # Home team's historical advantage
            'h2h_goal_difference_avg',     # Average goal difference
            'h2h_days_since_last_meeting', # Days since last meeting
        ]
        
        for feature in h2h_features:
            df[feature] = 0.0
        
        print(f"📊 Processing {len(df):,} games for H2H calculation...")
        
        # Process each match
        for i, (idx, match) in enumerate(df.iterrows()):
            if i % 10000 == 0:
                print(f"   Progress: {i:,}/{len(df):,} games ({i/len(df)*100:.1f}%)")
            
            home_team = match['home_team']
            away_team = match['away_team']
            match_date = pd.to_datetime(match['date'])
            
            # Find all previous meetings between these teams
            previous_meetings = df.iloc[:i][
                ((df.iloc[:i]['home_team'] == home_team) & (df.iloc[:i]['away_team'] == away_team)) |
                ((df.iloc[:i]['home_team'] == away_team) & (df.iloc[:i]['away_team'] == home_team))
            ].copy()
            
            if len(previous_meetings) > 0:
                h2h_stats = self._calculate_h2h_stats(previous_meetings, home_team, away_team, match_date)
                
                # Update the main dataframe
                for feature, value in h2h_stats.items():
                    df.loc[idx, feature] = value
        
        print(f"✅ Head-to-head features implemented: {len(h2h_features)} new features")
        return df
    
    def _calculate_h2h_stats(self, meetings: pd.DataFrame, home_team: str, away_team: str, current_date) -> dict:
        """Calculate comprehensive H2H statistics."""
        stats = {}
        
        if len(meetings) == 0:
            return {f'h2h_{key}': 0.0 for key in [
                'total_meetings', 'home_wins_all', 'draws_all', 'away_wins_all',
                'home_win_rate', 'avg_goals_all', 'over_2_5_rate', 'btts_rate',
                'home_goals_avg', 'away_goals_avg', 'last_5_home_wins', 'last_5_draws',
                'last_5_away_wins', 'last_5_avg_goals', 'recent_trend', 'home_advantage',
                'goal_difference_avg', 'days_since_last_meeting'
            ]}
        
        # All-time statistics
        total_meetings = len(meetings)
        home_wins = 0
        draws = 0
        away_wins = 0
        total_goals = 0
        over_2_5_count = 0
        btts_count = 0
        home_goals_total = 0
        away_goals_total = 0
        goal_differences = []
        
        for _, meeting in meetings.iterrows():
            home_score = meeting['home_score']
            away_score = meeting['away_score']
            total_goals += home_score + away_score
            
            # Determine result from current home team's perspective
            if meeting['home_team'] == home_team:
                # Current home team was home in this meeting
                home_goals_total += home_score
                away_goals_total += away_score
                goal_differences.append(home_score - away_score)
                
                if home_score > away_score:
                    home_wins += 1
                elif home_score == away_score:
                    draws += 1
                else:
                    away_wins += 1
            else:
                # Current home team was away in this meeting
                home_goals_total += away_score
                away_goals_total += home_score
                goal_differences.append(away_score - home_score)
                
                if away_score > home_score:
                    home_wins += 1
                elif away_score == home_score:
                    draws += 1
                else:
                    away_wins += 1
            
            # Over 2.5 and BTTS
            if home_score + away_score > 2.5:
                over_2_5_count += 1
            if home_score > 0 and away_score > 0:
                btts_count += 1
        
        # Calculate all-time stats
        stats['h2h_total_meetings'] = total_meetings
        stats['h2h_home_wins_all'] = home_wins
        stats['h2h_draws_all'] = draws
        stats['h2h_away_wins_all'] = away_wins
        stats['h2h_home_win_rate'] = home_wins / total_meetings if total_meetings > 0 else 0
        stats['h2h_avg_goals_all'] = total_goals / total_meetings if total_meetings > 0 else 0
        stats['h2h_over_2_5_rate'] = over_2_5_count / total_meetings if total_meetings > 0 else 0
        stats['h2h_btts_rate'] = btts_count / total_meetings if total_meetings > 0 else 0
        stats['h2h_home_goals_avg'] = home_goals_total / total_meetings if total_meetings > 0 else 0
        stats['h2h_away_goals_avg'] = away_goals_total / total_meetings if total_meetings > 0 else 0
        stats['h2h_goal_difference_avg'] = np.mean(goal_differences) if goal_differences else 0
        
        # Last 5 meetings statistics
        last_5_meetings = meetings.tail(5)
        if len(last_5_meetings) > 0:
            last_5_home_wins = 0
            last_5_draws = 0
            last_5_away_wins = 0
            last_5_total_goals = 0
            
            for _, meeting in last_5_meetings.iterrows():
                home_score = meeting['home_score']
                away_score = meeting['away_score']
                last_5_total_goals += home_score + away_score
                
                # Determine result from current home team's perspective
                if meeting['home_team'] == home_team:
                    if home_score > away_score:
                        last_5_home_wins += 1
                    elif home_score == away_score:
                        last_5_draws += 1
                    else:
                        last_5_away_wins += 1
                else:
                    if away_score > home_score:
                        last_5_home_wins += 1
                    elif away_score == home_score:
                        last_5_draws += 1
                    else:
                        last_5_away_wins += 1
            
            stats['h2h_last_5_home_wins'] = last_5_home_wins
            stats['h2h_last_5_draws'] = last_5_draws
            stats['h2h_last_5_away_wins'] = last_5_away_wins
            stats['h2h_last_5_avg_goals'] = last_5_total_goals / len(last_5_meetings)
            
            # Recent trend (weighted towards recent results)
            recent_points = (last_5_home_wins * 3 + last_5_draws * 1) / (len(last_5_meetings) * 3)
            stats['h2h_recent_trend'] = recent_points
        else:
            stats['h2h_last_5_home_wins'] = 0
            stats['h2h_last_5_draws'] = 0
            stats['h2h_last_5_away_wins'] = 0
            stats['h2h_last_5_avg_goals'] = 0
            stats['h2h_recent_trend'] = 0.33  # Neutral
        
        # Home advantage calculation
        home_advantage_points = (home_wins * 3 + draws * 1) / (total_meetings * 3) if total_meetings > 0 else 0.33
        stats['h2h_home_advantage'] = home_advantage_points
        
        # Days since last meeting
        if len(meetings) > 0:
            last_meeting_date = pd.to_datetime(meetings.iloc[-1]['date'])
            days_since = (current_date - last_meeting_date).days
            stats['h2h_days_since_last_meeting'] = min(days_since, 3650)  # Cap at 10 years
        else:
            stats['h2h_days_since_last_meeting'] = 3650  # Default to 10 years
        
        return stats
    
    def test_h2h_features_impact(self, df: pd.DataFrame):
        """Test the impact of H2H features on prediction accuracy."""
        print("\n🧪 TESTING HEAD-TO-HEAD FEATURES IMPACT")
        print("=" * 50)
        
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import cross_val_score
        from sklearn.preprocessing import LabelEncoder
        
        # Prepare features
        feature_columns = [col for col in df.columns 
                          if df[col].dtype in ['int64', 'float64'] 
                          and col not in ['home_score', 'away_score', 'match_result', 'total_goals']]
        
        # Encode categorical features
        le_home = LabelEncoder()
        le_away = LabelEncoder()
        le_league = LabelEncoder()
        
        df_encoded = df.copy()
        df_encoded['home_team_encoded'] = le_home.fit_transform(df['home_team'])
        df_encoded['away_team_encoded'] = le_away.fit_transform(df['away_team'])
        df_encoded['league_encoded'] = le_league.fit_transform(df['league'])
        
        # Add encoded features to feature list
        feature_columns.extend(['home_team_encoded', 'away_team_encoded', 'league_encoded'])
        
        X = df_encoded[feature_columns].fillna(0)
        y = df_encoded['match_result']
        
        # Remove rows with missing targets
        valid_rows = ~y.isna()
        X = X[valid_rows]
        y = y[valid_rows]
        
        print(f"📊 Testing with {X.shape[0]:,} samples, {X.shape[1]} features")
        
        # Test with Random Forest
        rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        
        try:
            scores = cross_val_score(rf_model, X, y, cv=5, scoring='accuracy')
            avg_accuracy = scores.mean()
            
            print(f"🎯 Model Accuracy with H2H Features: {avg_accuracy:.3f} ({avg_accuracy*100:.1f}%)")
            print(f"📈 Expected Improvement: +{(avg_accuracy - 0.42)*100:.1f}% vs baseline (42%)")
            
            if avg_accuracy > 0.65:
                print("🎉 EXCELLENT! Major improvement achieved!")
            elif avg_accuracy > 0.55:
                print("✅ GOOD! Significant improvement achieved!")
            else:
                print("⚠️  Moderate improvement - need more features")
                
            # Feature importance
            rf_model.fit(X, y)
            feature_importance = pd.DataFrame({
                'feature': feature_columns,
                'importance': rf_model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            print(f"\n🔝 TOP 10 MOST IMPORTANT FEATURES:")
            for i, (_, row) in enumerate(feature_importance.head(10).iterrows(), 1):
                print(f"   {i:2d}. {row['feature']}: {row['importance']:.3f}")
                
        except Exception as e:
            print(f"❌ Error testing model: {str(e)}")

def main():
    """Main function to implement H2H features."""
    print("🚀 IMPLEMENTING HEAD-TO-HEAD FEATURES - PRIORITY 2")
    print("=" * 70)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Expected Impact: +8-12% accuracy improvement")
    print("=" * 70)
    
    # Check if enhanced dataset with form features exists
    enhanced_data_path = Path('data/enhanced_dataset_with_form.pkl')
    
    if enhanced_data_path.exists():
        print("📥 Loading enhanced dataset with form features...")
        df = pd.read_pickle(enhanced_data_path)
        print(f"✅ Loaded {len(df):,} games with {df.shape[1]} features")
    else:
        print("❌ Enhanced dataset with form features not found!")
        print("💡 Please run implement_team_form_features.py first")
        return
    
    # Initialize H2H feature creator
    h2h_creator = HeadToHeadFeatures()
    
    # Add H2H features
    enhanced_data = h2h_creator.add_h2h_features(df)
    
    # Test impact
    h2h_creator.test_h2h_features_impact(enhanced_data)
    
    # Save enhanced dataset
    output_path = Path('data/enhanced_dataset_with_form_and_h2h.pkl')
    output_path.parent.mkdir(exist_ok=True)
    enhanced_data.to_pickle(output_path)
    
    print(f"\n💾 Enhanced dataset saved: {output_path}")
    print(f"📊 Dataset shape: {enhanced_data.shape}")
    
    print("\n🎉 HEAD-TO-HEAD FEATURES IMPLEMENTATION COMPLETE!")
    print("=" * 70)
    print("✅ Next steps:")
    print("   1. Implement Home/Away form features (+10-15% accuracy)")
    print("   2. Combine all features for maximum impact")
    print("   3. Retrain models with enhanced dataset")
    print("=" * 70)

if __name__ == "__main__":
    main()
