# 🚀 Unified Football Prediction Pipeline

## 🎯 Overview

A comprehensive, production-ready football prediction system that combines machine learning with real-world data to generate high-quality predictions with automatic accumulator building.

## ✨ Key Features

### 🤖 Advanced Machine Learning
- **15 Optimal Models**: LightGBM, XGBoost, Random Forest, Neural Networks
- **126,042+ Training Matches**: Historical data from 2015-2025
- **Real Data Sources**: GitHub historical datasets + APIFootball live data
- **Automatic Model Selection**: Best performing models for each prediction type

### 🎯 Prediction Types
- **Match Result**: Home Win, Draw, Away Win
- **Over/Under 2.5 Goals**: Goal-based predictions
- **Both Teams to Score (BTTS)**: Scoring probability analysis
- **Clean Sheets**: Home/Away clean sheet predictions
- **Custom Odds Categories**: 2.0, 5.0, 10.0, 20.0 odds groupings

### 🔍 Quality Assurance
- **Strict Filtering**: Confidence ≥75%, Low-risk only
- **35.1% Pass Rate**: Only highest quality predictions included
- **Risk Management**: Very low and low risk predictions only
- **No Medium/High Risk**: Automatic filtering of risky predictions

### 🎰 Smart Accumulator Building
- **Automatic Categorization**: By odds ranges (2.0, 5.0, 10.0, 20.0)
- **Risk-Based Grouping**: Intelligent combination algorithms
- **Optimized Returns**: Balanced risk vs reward calculations

### 💾 Comprehensive Caching
- **Daily Fixture Caching**: Reuse fixtures to avoid API limits
- **Model Persistence**: No retraining required on subsequent runs
- **Metadata Tracking**: Model freshness and performance monitoring
- **Efficient Storage**: Optimized data structures for fast loading

## 🛠️ Installation & Setup

### Prerequisites
```bash
Python 3.8+
pip install -r requirements.txt
```

### Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd betsightly-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### API Configuration
Create a `.env` file:
```bash
APIFOOTBALL_API_KEY=your_api_key_here
```

## 🚀 Usage

### Basic Usage
```bash
# Run with default settings (75% confidence)
python unified_prediction_pipeline.py

# Higher confidence threshold
python unified_prediction_pipeline.py --min-confidence 80

# Specific date
python unified_prediction_pipeline.py --date 2025-08-07
```

### Command Line Options
- `--min-confidence`: Minimum confidence threshold (default: 75)
- `--date`: Specific date for predictions (default: today)
- `--help`: Show all available options

## 📊 Performance Metrics

### Training Data
- **126,042 matches** from 2015-2025
- **Multiple leagues**: Premier League, La Liga, Serie A, Bundesliga, Ligue 1
- **Comprehensive features**: Team form, H2H records, venue performance

### Quality Metrics
- **35.1% prediction pass rate** with strict filtering
- **75%+ confidence** on all included predictions
- **Low-risk only** classification system
- **Real-time model performance** tracking

### Speed & Efficiency
- **Fast loading**: Pre-trained models load in seconds
- **Efficient caching**: Daily fixtures reused
- **No retraining**: Models persist between runs
- **Optimized processing**: Batch prediction capabilities

## 🏗️ Architecture

### Core Components
1. **`unified_prediction_pipeline.py`** - Main orchestrator
2. **`optimal_trainer.py`** - Advanced model training system
3. **`daily_fixture_manager.py`** - Fixture caching and management
4. **`smart_model_manager.py`** - Model lifecycle management
5. **`comprehensive_model_trainer.py`** - Multi-algorithm training

### Data Flow
```
GitHub Historical Data → Model Training → APIFootball Live Data → 
Predictions → Quality Filtering → Accumulator Building → Results
```

### Model Types
- **LightGBM**: Fast gradient boosting for structured data
- **XGBoost**: Extreme gradient boosting with regularization
- **Random Forest**: Ensemble learning with decision trees
- **Neural Networks**: Deep learning for complex patterns

## 📁 Project Structure

```
betsightly-backend/
├── unified_prediction_pipeline.py    # Main pipeline
├── optimal_trainer.py               # Model training
├── daily_fixture_manager.py         # Fixture management
├── smart_model_manager.py           # Model lifecycle
├── comprehensive_model_trainer.py   # Training algorithms
├── services/                        # Core services
├── ml/                             # Machine learning modules
├── data/                           # Data storage (excluded from git)
├── models/                         # Trained models (excluded from git)
├── cache/                          # Caching system (excluded from git)
└── requirements.txt                # Dependencies
```

## 🔧 Configuration

### Model Training
Models are automatically trained on first run using:
- GitHub historical datasets (2015-2025)
- APIFootball recent data (last 12 months)
- Optimal hyperparameter selection
- Cross-validation for model selection

### Caching Strategy
- **Fixtures**: Cached daily to avoid API limits
- **Models**: Persisted after training
- **Predictions**: Cached with metadata
- **Performance**: Tracked over time

## 🎯 Production Deployment

### Requirements
- Python 3.8+
- 4GB+ RAM for model loading
- APIFootball API key
- Stable internet connection

### Recommended Setup
- Run daily via cron job
- Monitor prediction accuracy
- Regular model retraining (monthly)
- Backup cache and models

## 📈 Future Enhancements

- Real-time odds integration
- Advanced ensemble methods
- Player-level statistics
- Weather data integration
- Live match updates

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Implement changes
4. Add tests
5. Submit pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check existing documentation
2. Review error logs
3. Create GitHub issue
4. Provide detailed reproduction steps

---

**Built with ❤️ for accurate football predictions**
