"""
Enhanced Database Schema for Prediction Caching and Fixture Management System
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Index, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import json

# Import the existing Base from database.py
from database import Base

class CachedFixture(Base):
    """Store all fetched fixtures as backup"""
    __tablename__ = 'cached_fixtures'
    
    id = Column(Integer, primary_key=True)
    fixture_id = Column(String(50), unique=True, nullable=False)  # APIFootball fixture ID
    home_team = Column(String(100), nullable=False)
    away_team = Column(String(100), nullable=False)
    league_name = Column(String(100), nullable=False)
    league_id = Column(String(50))
    country = Column(String(50))
    fixture_date = Column(DateTime, nullable=False)
    status = Column(String(20), default='upcoming')
    
    # Betting odds
    home_odds = Column(Float)
    draw_odds = Column(Float)
    away_odds = Column(Float)
    
    # Match results (filled after completion)
    home_score = Column(Integer)
    away_score = Column(Integer)
    match_result = Column(String(10))  # 'home', 'away', 'draw'
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    api_source = Column(String(50), default='apifootball')
    raw_data = Column(Text)  # Store complete API response as JSON
    
    # Relationships
    predictions = relationship("CachedPrediction", back_populates="fixture")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_fixture_date', 'fixture_date'),
        Index('idx_fixture_status', 'status'),
        Index('idx_fixture_teams', 'home_team', 'away_team'),
    )

class CachedPrediction(Base):
    """Store all generated predictions with full metadata"""
    __tablename__ = 'cached_predictions'
    
    id = Column(Integer, primary_key=True)
    fixture_id = Column(String(50), ForeignKey('cached_fixtures.fixture_id'), nullable=False)
    prediction_date = Column(DateTime, nullable=False)
    
    # Prediction details
    prediction_type = Column(String(30), nullable=False)  # match_result, over_under, etc.
    prediction_value = Column(String(20), nullable=False)  # 0, 1, 2 for match_result
    confidence = Column(Float, nullable=False)
    model_type = Column(String(30), nullable=False)  # xgboost, lightgbm, random_forest
    model_name = Column(String(50))  # specific model identifier
    
    # Feature metadata
    feature_count = Column(Integer, default=62)
    feature_version = Column(String(20), default='enhanced_v1')
    
    # Prediction outcome tracking
    actual_result = Column(String(20))  # Filled after match completion
    is_correct = Column(Boolean)  # True if prediction matches actual result
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    generation_time_ms = Column(Float)  # Time taken to generate prediction
    
    # Relationships
    fixture = relationship("CachedFixture", back_populates="predictions")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_prediction_date', 'prediction_date'),
        Index('idx_prediction_type', 'prediction_type'),
        Index('idx_fixture_prediction', 'fixture_id', 'prediction_type'),
        Index('idx_model_type', 'model_type'),
    )

class PredictionBatch(Base):
    """Track daily prediction generation batches"""
    __tablename__ = 'enhanced_prediction_batches'
    
    id = Column(Integer, primary_key=True)
    batch_date = Column(DateTime, nullable=False, unique=True)
    
    # Batch statistics
    total_fixtures = Column(Integer, default=0)
    successful_predictions = Column(Integer, default=0)
    failed_predictions = Column(Integer, default=0)
    
    # Timing information
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Status tracking
    status = Column(String(20), default='running')  # running, completed, failed
    error_message = Column(Text)
    
    # Model information
    models_used = Column(Integer, default=18)
    feature_count = Column(Integer, default=62)
    
    # Indexes
    __table_args__ = (
        Index('idx_batch_date', 'batch_date'),
        Index('idx_batch_status', 'status'),
    )

class AccumulatorCache(Base):
    """Cache generated accumulator combinations"""
    __tablename__ = 'accumulator_cache'
    
    id = Column(Integer, primary_key=True)
    prediction_date = Column(DateTime, nullable=False)
    accumulator_type = Column(String(20), nullable=False)  # 2_odds, 5_odds, 10_odds, rollover
    
    # Accumulator details
    is_selected = Column(Boolean, default=False)
    total_odds = Column(Float)
    game_count = Column(Integer)
    average_confidence = Column(Float)
    diversity_score = Column(Float)
    
    # Risk assessment
    risk_level = Column(String(20))  # very_low, low, medium, high
    recommended_stake = Column(Float)
    
    # Accumulator data
    games_data = Column(Text)  # JSON array of games
    selection_reason = Column(Text)
    
    # Outcome tracking
    actual_result = Column(String(20))  # won, lost, pending
    actual_payout = Column(Float)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_accumulator_date_type', 'prediction_date', 'accumulator_type'),
        Index('idx_accumulator_selected', 'is_selected'),
    )

class PredictionAnalytics(Base):
    """Store prediction performance analytics"""
    __tablename__ = 'prediction_analytics'
    
    id = Column(Integer, primary_key=True)
    analysis_date = Column(DateTime, nullable=False)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    
    # Overall statistics
    total_predictions = Column(Integer, default=0)
    correct_predictions = Column(Integer, default=0)
    accuracy_rate = Column(Float, default=0.0)
    
    # By prediction type
    match_result_accuracy = Column(Float)
    over_under_accuracy = Column(Float)
    btts_accuracy = Column(Float)
    clean_sheet_accuracy = Column(Float)
    win_to_nil_accuracy = Column(Float)
    
    # By model type
    xgboost_accuracy = Column(Float)
    lightgbm_accuracy = Column(Float)
    random_forest_accuracy = Column(Float)
    
    # Confidence correlation
    high_confidence_accuracy = Column(Float)  # 90%+ confidence
    medium_confidence_accuracy = Column(Float)  # 70-90% confidence
    low_confidence_accuracy = Column(Float)  # <70% confidence
    
    # Accumulator performance
    accumulator_success_rate = Column(Float)
    average_accumulator_odds = Column(Float)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_analytics_date_period', 'analysis_date', 'period_type'),
    )
