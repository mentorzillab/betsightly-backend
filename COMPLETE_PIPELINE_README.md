# 🚀 Complete Prediction Pipeline

This is the **master script** that combines all functionality for fetching fixtures, training models, and generating predictions in one unified workflow.

## 📋 What It Does

1. **🔍 Checks Model Availability** - Verifies if trained ML models exist
2. **🎯 Trains Models If Needed** - Uses GitHub dataset to train missing models
3. **🌐 Fetches Today's Fixtures** - Gets live fixtures from APIFootball.com
4. **🤖 Generates Predictions** - Runs fixtures through trained ML models
5. **💾 Stores Results** - Saves predictions to database for frontend consumption

## 🎯 Quick Start

### Option 1: Simple Daily Run
```bash
# Run daily predictions (easiest way)
python run_daily_predictions.py
```

### Option 2: Full Control
```bash
# Run complete pipeline with all options
python complete_prediction_pipeline.py

# Run for specific date
python complete_prediction_pipeline.py --date 2024-01-15

# Force model retraining
python complete_prediction_pipeline.py --force-retrain

# Run for tomorrow with retraining
python complete_prediction_pipeline.py --date 2024-01-16 --force-retrain
```

### Option 3: Individual Operations
```bash
# Only check model availability
python complete_prediction_pipeline.py --check-models-only

# Only train models
python complete_prediction_pipeline.py --train-only

# Only fetch fixtures
python complete_prediction_pipeline.py --fetch-only

# Cache management
python complete_prediction_pipeline.py --cache-status
python complete_prediction_pipeline.py --clear-cache
python complete_prediction_pipeline.py --clear-cache-date 2024-01-15
```

## 🧪 Testing

Before running the full pipeline, test your setup:

```bash
# Run test suite
python test_complete_pipeline.py

# Test fixture caching specifically
python test_fixture_caching.py
```

This will verify:
- ✅ API connections work
- ✅ Models are available or can be trained
- ✅ Fixture fetching works
- ✅ Fixture caching is working
- ✅ All dependencies are installed

## 📊 Expected Output

### Successful Run
```
🚀 COMPLETE PREDICTION PIPELINE
============================================================
📅 Target Date: 2024-01-15
🔄 Force Retrain: False
============================================================

🎯 STEP 1: Model Training Check
----------------------------------------
🔍 Checking model availability...
✅ Found xgboost/match_result
✅ Found xgboost/over_2_5
... (more models)
📊 Model availability: 18/20 (90.0%)
✅ Sufficient models available, skipping training

🌐 STEP 2: Fixture Fetching
----------------------------------------
🌐 Fetching fixtures for 2024-01-15 from APIFootball...
✅ Fetched 45 fixtures from APIFootball
📊 Found 32 upcoming fixtures

🎯 STEP 3: Prediction Generation
----------------------------------------
🎯 Generating predictions for 32 fixtures...
1/32: Arsenal vs Chelsea
✅ Prediction generated successfully
... (more predictions)
📊 Prediction summary: 30 successful, 2 failed

💾 STEP 4: Database Storage
----------------------------------------
💾 Storing 30 predictions in database...
✅ Successfully stored 30 predictions in database

🎉 PIPELINE COMPLETED SUCCESSFULLY!
============================================================
📊 Summary:
   Fixtures processed: 32
   Predictions generated: 30
   Success rate: 93.8%
🌐 Frontend endpoints now have fresh data:
   GET /api/daily-predictions/today
   GET /api/accumulators/today
============================================================
```

## 💾 Smart Fixture Caching

The pipeline includes **intelligent fixture caching** to reduce API calls:

### 🎯 **How It Works**
- **First fetch**: Gets fixtures from APIFootball API and saves to cache
- **Subsequent fetches**: Uses cached data (valid for 6 hours)
- **Automatic cleanup**: Removes old cache files automatically
- **Cache validation**: Checks if cached data is still valid

### 📊 **Cache Management**
```bash
# Check cache status
python complete_prediction_pipeline.py --cache-status

# Clear all cache
python complete_prediction_pipeline.py --clear-cache

# Clear specific date
python complete_prediction_pipeline.py --clear-cache-date 2024-01-15
```

### 🚀 **Benefits**
- ✅ **Saves API quota** - Reduces repeated calls
- ✅ **Faster responses** - Cached data loads instantly
- ✅ **Offline capability** - Works with cached data when API is down
- ✅ **Smart expiration** - Cache expires after 6 hours for fresh data

## 🔧 Configuration

### Required Environment Variables
```bash
# APIFootball.com API key
APIFOOTBALL_API_KEY=your_api_key_here

# Optional: Football-Data.org API key (fallback)
FOOTBALL_DATA_API_KEY=your_api_key_here
```

### Model Requirements
The pipeline checks for these models:
- **XGBoost**: match_result, over_2_5, btts, clean_sheet_home, clean_sheet_away
- **LightGBM**: match_result, over_2_5, btts, clean_sheet_home, clean_sheet_away  
- **Neural Network**: match_result, over_2_5, btts
- **Random Forest**: match_result, over_2_5, btts

If 70%+ of models are available, the pipeline proceeds. Otherwise, it trains missing models.

## 🌐 Frontend Integration

After successful execution, these endpoints have fresh data:

```bash
# Daily predictions
GET /api/daily-predictions/today

# Accumulator categories
GET /api/accumulators/today
GET /api/accumulators/2-odds    # Low-risk bets
GET /api/accumulators/5-odds    # Medium-risk bets  
GET /api/accumulators/10-odds   # High-risk bets
GET /api/accumulators/rollover  # Rollover strategy
```

## 🔄 Automation

### Daily Cron Job
```bash
# Add to crontab for daily 6 AM execution
0 6 * * * cd /path/to/betsightly-backend && python run_daily_predictions.py
```

### Weekly Model Retraining
```bash
# Retrain models every Sunday at 2 AM
0 2 * * 0 cd /path/to/betsightly-backend && python complete_prediction_pipeline.py --force-retrain
```

## 🚨 Error Handling

The pipeline handles common issues:
- **No API Key**: Falls back to sample data
- **Missing Models**: Automatically trains from GitHub dataset
- **No Fixtures**: Gracefully exits with warning
- **Prediction Failures**: Continues with successful predictions
- **Database Issues**: Logs errors and continues

## 📈 Performance

- **Model Training**: 5-15 minutes (first time only)
- **Fixture Fetching**: 10-30 seconds
- **Prediction Generation**: 1-3 minutes for 50 fixtures
- **Database Storage**: 5-10 seconds

## 🔍 Troubleshooting

### Common Issues

1. **"No API key configured"**
   ```bash
   export APIFOOTBALL_API_KEY=your_key_here
   ```

2. **"Model training failed"**
   ```bash
   # Check if GitHub dataset is accessible
   python train_models_github_dataset.py
   ```

3. **"No fixtures found"**
   ```bash
   # Test API connection
   python test_complete_pipeline.py
   ```

4. **"Database storage failed"**
   ```bash
   # Check database connection
   python -c "from database import get_db; print('DB OK')"
   ```

## 🎯 Integration with Existing Scripts

This pipeline **replaces** these individual scripts:
- ✅ `generate_daily_predictions.py`
- ✅ `generate_predictions_for_frontend.py`
- ✅ `ml_pipeline_streamlined.py`
- ✅ `train_models_github_dataset.py`

But **works with** these services:
- ✅ `services/apifootball_service.py`
- ✅ `api/endpoints/ml_predictions.py`
- ✅ `services/daily_predictions_service.py`

## 🎉 Success Indicators

Pipeline is working correctly when you see:
- ✅ Models loaded or trained successfully
- ✅ Fixtures fetched from APIFootball
- ✅ Predictions generated with >80% success rate
- ✅ Data stored in database
- ✅ Frontend endpoints return fresh predictions

---

**🚀 Ready to run? Start with:**
```bash
python test_complete_pipeline.py  # Test first
python run_daily_predictions.py   # Then run daily predictions
```
