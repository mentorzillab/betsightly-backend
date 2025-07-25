#!/usr/bin/env python3
"""
Train ML Models with REAL Football Data
Uses real data from GitHub datasets and APIFootball historical data.
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import requests
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from services.apifootball_service import APIFootballService
from train_models_github_dataset import GitHubDatasetTrainer

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class RealDataTrainer:
    """Train models using real football data from multiple sources."""
    
    def __init__(self):
        """Initialize the real data trainer."""
        self.apifootball_service = APIFootballService()
        self.github_trainer = GitHubDatasetTrainer()
        self.min_training_samples = 3000  # Minimum games needed for good predictions (lowered for quality data)
        
    def download_github_football_datasets(self) -> pd.DataFrame:
        """Download real football datasets from GitHub."""
        print("📥 Downloading real football datasets from GitHub...")
        
        datasets = []
        
        # Popular football datasets - multiple seasons for more data
        github_datasets = [
            # Premier League multiple seasons
            {
                'name': 'Premier League 2023-24',
                'url': 'https://www.football-data.co.uk/mmz4281/2324/E0.csv',
                'description': 'Premier League 2023-24 season'
            },
            {
                'name': 'Premier League 2022-23',
                'url': 'https://www.football-data.co.uk/mmz4281/2223/E0.csv',
                'description': 'Premier League 2022-23 season'
            },
            {
                'name': 'Premier League 2021-22',
                'url': 'https://www.football-data.co.uk/mmz4281/2122/E0.csv',
                'description': 'Premier League 2021-22 season'
            },
            # Championship multiple seasons
            {
                'name': 'Championship 2023-24',
                'url': 'https://www.football-data.co.uk/mmz4281/2324/E1.csv',
                'description': 'Championship 2023-24 season'
            },
            {
                'name': 'Championship 2022-23',
                'url': 'https://www.football-data.co.uk/mmz4281/2223/E1.csv',
                'description': 'Championship 2022-23 season'
            },
            # Other major leagues
            {
                'name': 'La Liga 2023-24',
                'url': 'https://www.football-data.co.uk/mmz4281/2324/SP1.csv',
                'description': 'Spanish La Liga 2023-24'
            },
            {
                'name': 'Bundesliga 2023-24',
                'url': 'https://www.football-data.co.uk/mmz4281/2324/D1.csv',
                'description': 'German Bundesliga 2023-24'
            },
            {
                'name': 'Serie A 2023-24',
                'url': 'https://www.football-data.co.uk/mmz4281/2324/I1.csv',
                'description': 'Italian Serie A 2023-24'
            }
        ]
        
        for dataset_info in github_datasets:
            try:
                print(f"   📊 Downloading: {dataset_info['name']}")
                df = pd.read_csv(dataset_info['url'])
                
                if len(df) > 0:
                    df['source'] = dataset_info['name']
                    datasets.append(df)
                    print(f"   ✅ Downloaded {len(df):,} records from {dataset_info['name']}")
                else:
                    print(f"   ⚠️  Empty dataset: {dataset_info['name']}")
                    
            except Exception as e:
                print(f"   ❌ Failed to download {dataset_info['name']}: {str(e)}")
                continue
        
        if datasets:
            # Combine all datasets
            combined_df = pd.concat(datasets, ignore_index=True, sort=False)
            print(f"✅ Combined {len(combined_df):,} total records from {len(datasets)} sources")
            return combined_df
        else:
            print("❌ No datasets downloaded successfully")
            return pd.DataFrame()
    
    def get_apifootball_historical_data(self, months_back: int = 6) -> pd.DataFrame:
        """Get historical data from APIFootball."""
        print(f"📥 Downloading {months_back} months of historical data from APIFootball...")
        
        historical_data = []
        
        # Get data for the last N months
        for i in range(months_back):
            try:
                # Calculate date range
                end_date = datetime.now() - timedelta(days=i*30)
                start_date = end_date - timedelta(days=30)
                
                date_str_start = start_date.strftime("%Y-%m-%d")
                date_str_end = end_date.strftime("%Y-%m-%d")
                
                print(f"   📅 Fetching data for {date_str_start} to {date_str_end}")
                
                # Get historical matches
                matches = self.apifootball_service.get_historical_matches(
                    from_date=date_str_start,
                    to_date=date_str_end
                )
                
                if matches:
                    historical_data.extend(matches)
                    print(f"   ✅ Retrieved {len(matches)} matches")
                else:
                    print(f"   ⚠️  No matches found for this period")
                    
            except Exception as e:
                print(f"   ❌ Error fetching data for month {i}: {str(e)}")
                continue
        
        if historical_data:
            df = pd.DataFrame(historical_data)
            print(f"✅ Total APIFootball historical data: {len(df):,} matches")
            return df
        else:
            print("❌ No historical data retrieved from APIFootball")
            return pd.DataFrame()
    
    def standardize_data_format(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """Standardize different data formats into a common format."""
        print(f"🔧 Standardizing data format for {source}...")
        
        try:
            standardized_df = pd.DataFrame()
            
            if source == 'apifootball':
                # APIFootball format - handle DataFrame properly
                try:
                    standardized_df['date'] = pd.to_datetime(df['date'] if 'date' in df.columns else df['match_date'], errors='coerce')
                    standardized_df['home_team'] = df['home_team'].astype(str) if 'home_team' in df.columns else df['match_hometeam_name'].astype(str)
                    standardized_df['away_team'] = df['away_team'].astype(str) if 'away_team' in df.columns else df['match_awayteam_name'].astype(str)
                    standardized_df['league'] = df['league_name'].astype(str) if 'league_name' in df.columns else df.get('league', 'Unknown')

                    # Handle scores - they might be strings or numbers
                    home_score_col = 'home_score' if 'home_score' in df.columns else 'match_hometeam_score'
                    away_score_col = 'away_score' if 'away_score' in df.columns else 'match_awayteam_score'

                    standardized_df['home_score'] = pd.to_numeric(df[home_score_col], errors='coerce').fillna(0)
                    standardized_df['away_score'] = pd.to_numeric(df[away_score_col], errors='coerce').fillna(0)

                    # Use default odds if not available
                    standardized_df['home_odds'] = df.get('home_odds', 2.0) if 'home_odds' in df.columns else 2.0
                    standardized_df['draw_odds'] = df.get('draw_odds', 3.0) if 'draw_odds' in df.columns else 3.0
                    standardized_df['away_odds'] = df.get('away_odds', 2.0) if 'away_odds' in df.columns else 2.0

                except KeyError as e:
                    print(f"   ⚠️  Missing column in APIFootball data: {e}")
                    print(f"   📋 Available columns: {list(df.columns)}")
                    # Return empty DataFrame if critical columns are missing
                    return pd.DataFrame()
                
            elif 'football-data' in source.lower():
                # Football-data.co.uk format
                standardized_df['date'] = pd.to_datetime(df.get('Date', ''), format='%d/%m/%Y', errors='coerce')
                standardized_df['home_team'] = df.get('HomeTeam', '')
                standardized_df['away_team'] = df.get('AwayTeam', '')
                standardized_df['league'] = source
                standardized_df['home_score'] = pd.to_numeric(df.get('FTHG', 0), errors='coerce')
                standardized_df['away_score'] = pd.to_numeric(df.get('FTAG', 0), errors='coerce')
                
                # Use betting odds if available
                standardized_df['home_odds'] = pd.to_numeric(df.get('B365H', 2.0), errors='coerce')
                standardized_df['draw_odds'] = pd.to_numeric(df.get('B365D', 3.0), errors='coerce')
                standardized_df['away_odds'] = pd.to_numeric(df.get('B365A', 2.0), errors='coerce')
                
            else:
                # Generic format - try to map common column names
                date_cols = ['date', 'Date', 'match_date', 'game_date']
                home_cols = ['home_team', 'HomeTeam', 'home', 'match_hometeam_name']
                away_cols = ['away_team', 'AwayTeam', 'away', 'match_awayteam_name']
                
                for col in date_cols:
                    if col in df.columns:
                        standardized_df['date'] = pd.to_datetime(df[col], errors='coerce')
                        break
                
                for col in home_cols:
                    if col in df.columns:
                        standardized_df['home_team'] = df[col]
                        break
                        
                for col in away_cols:
                    if col in df.columns:
                        standardized_df['away_team'] = df[col]
                        break
                
                standardized_df['league'] = source
                standardized_df['home_score'] = 0
                standardized_df['away_score'] = 0
                standardized_df['home_odds'] = 2.0
                standardized_df['draw_odds'] = 3.0
                standardized_df['away_odds'] = 2.0
            
            # Create derived features
            standardized_df['total_goals'] = standardized_df['home_score'] + standardized_df['away_score']
            standardized_df['over_2_5'] = (standardized_df['total_goals'] > 2.5).astype(int)
            standardized_df['over_1_5'] = (standardized_df['total_goals'] > 1.5).astype(int)
            standardized_df['over_3_5'] = (standardized_df['total_goals'] > 3.5).astype(int)
            standardized_df['btts'] = ((standardized_df['home_score'] > 0) & (standardized_df['away_score'] > 0)).astype(int)
            
            # Match result: 0=Home Win, 1=Draw, 2=Away Win
            standardized_df['match_result'] = np.where(
                standardized_df['home_score'] > standardized_df['away_score'], 0,
                np.where(standardized_df['home_score'] == standardized_df['away_score'], 1, 2)
            )
            
            # Clean sheets
            standardized_df['clean_sheet_home'] = (standardized_df['away_score'] == 0).astype(int)
            standardized_df['clean_sheet_away'] = (standardized_df['home_score'] == 0).astype(int)
            
            # Win to nil
            standardized_df['win_to_nil_home'] = ((standardized_df['home_score'] > standardized_df['away_score']) & (standardized_df['away_score'] == 0)).astype(int)
            standardized_df['win_to_nil_away'] = ((standardized_df['away_score'] > standardized_df['home_score']) & (standardized_df['home_score'] == 0)).astype(int)
            
            # Remove rows with missing essential data
            standardized_df = standardized_df.dropna(subset=['home_team', 'away_team'])
            standardized_df = standardized_df[standardized_df['home_team'] != '']
            standardized_df = standardized_df[standardized_df['away_team'] != '']
            
            print(f"✅ Standardized {len(standardized_df):,} records for {source}")
            return standardized_df
            
        except Exception as e:
            print(f"❌ Error standardizing data for {source}: {str(e)}")
            return pd.DataFrame()
    
    def combine_all_data_sources(self) -> pd.DataFrame:
        """Combine data from all sources into one training dataset."""
        print("🔄 COMBINING ALL REAL DATA SOURCES")
        print("=" * 60)
        
        all_datasets = []
        
        # 1. Get GitHub datasets
        github_data = self.download_github_football_datasets()
        if not github_data.empty:
            for source in github_data['source'].unique():
                source_data = github_data[github_data['source'] == source]
                standardized = self.standardize_data_format(source_data, source)
                if not standardized.empty:
                    all_datasets.append(standardized)
        
        # 2. Get APIFootball historical data (more months for more data)
        apifootball_data = self.get_apifootball_historical_data(months_back=6)
        if not apifootball_data.empty:
            standardized = self.standardize_data_format(apifootball_data, 'apifootball')
            if not standardized.empty:
                all_datasets.append(standardized)
        
        # 3. Combine all datasets
        if all_datasets:
            combined_df = pd.concat(all_datasets, ignore_index=True, sort=False)
            
            # Remove duplicates
            combined_df = combined_df.drop_duplicates(subset=['date', 'home_team', 'away_team'])
            
            # Sort by date
            combined_df = combined_df.sort_values('date')
            
            print(f"🎉 FINAL COMBINED DATASET:")
            print(f"   📊 Total Games: {len(combined_df):,}")
            print(f"   📅 Date Range: {combined_df['date'].min()} to {combined_df['date'].max()}")
            print(f"   🏆 Unique Teams: {len(set(combined_df['home_team'].unique()) | set(combined_df['away_team'].unique()))}")
            print(f"   🏆 Leagues: {combined_df['league'].nunique()}")
            
            return combined_df
        else:
            print("❌ No data sources available!")
            return pd.DataFrame()

def main():
    """Main training function."""
    print("🚀 TRAINING MODELS WITH REAL FOOTBALL DATA")
    print("=" * 70)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Initialize trainer
    trainer = RealDataTrainer()
    
    # Get real data
    real_data = trainer.combine_all_data_sources()
    
    if len(real_data) >= trainer.min_training_samples:
        print(f"✅ Sufficient data for training: {len(real_data):,} games")
        
        # Use the existing GitHub trainer with real data
        trainer.github_trainer.df = real_data
        
        # Train models
        print("\n🤖 Training ML models with real data...")
        trainer.github_trainer.train_all_models()
        
        print("\n🎉 SUCCESS! Models trained with real football data!")
        print("=" * 70)
        print("✅ Models are now ready for accurate predictions")
        print("🚀 Run: python run_daily_predictions.py")
        print("=" * 70)
        
    else:
        print(f"❌ Insufficient data: {len(real_data):,} games (need {trainer.min_training_samples:,})")
        print("💡 Try increasing the months_back parameter or adding more data sources")

if __name__ == "__main__":
    main()
