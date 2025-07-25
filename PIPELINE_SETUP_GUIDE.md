# 🚀 Complete Prediction Pipeline - Setup Guide

## ✅ System Status: READY!

Your system has **28 trained models** and all required components. Here's how to use the complete prediction pipeline.

## 🎯 What You Now Have

### 📁 New Scripts Created
- **`complete_prediction_pipeline.py`** - Master script that does everything
- **`run_daily_predictions.py`** - Simple daily runner
- **`simple_pipeline_test.py`** - System readiness checker
- **`test_complete_pipeline.py`** - Full pipeline tester

### 🤖 Available Models (28 total)
- **XGBoost**: 10 models (match_result, over_2_5, btts, clean_sheets, etc.)
- **LightGBM**: 6 models (match_result, over_2_5, btts, clean_sheets)
- **Neural Network**: 8 models (match_result, over_2_5, btts, win_to_nil)
- **Random Forest**: 4 models (match_result, over_2_5, btts, win_to_nil)

## 🔧 Quick Setup

### 1. Set API Key (Required)
```bash
# Get your free API key from https://apifootball.com/
export APIFOOTBALL_API_KEY=your_api_key_here

# Or add to your .bashrc/.zshrc for permanent setup
echo 'export APIFOOTBALL_API_KEY=your_api_key_here' >> ~/.bashrc
```

### 2. Install Dependencies (If Needed)
```bash
# If you get import errors, install dependencies
pip install --break-system-packages -r requirements.txt

# Or use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 🚀 Usage Examples

### Daily Predictions (Simplest)
```bash
# Run daily predictions - does everything automatically
python run_daily_predictions.py
```

### Full Control
```bash
# Check if models are ready
python complete_prediction_pipeline.py --check-models-only

# Run complete pipeline for today
python complete_prediction_pipeline.py

# Run for specific date
python complete_prediction_pipeline.py --date 2024-01-15

# Force model retraining (if you want fresh models)
python complete_prediction_pipeline.py --force-retrain

# Only fetch fixtures (to see what's available)
python complete_prediction_pipeline.py --fetch-only
```

### Testing
```bash
# Quick system check
python simple_pipeline_test.py

# Full pipeline test (requires all dependencies)
python test_complete_pipeline.py
```

## 📊 Expected Workflow

### 1. System Check
```bash
python simple_pipeline_test.py
```
**Expected**: 5/6 tests pass (API key might be missing)

### 2. Set API Key
```bash
export APIFOOTBALL_API_KEY=your_key_here
```

### 3. Run Pipeline
```bash
python run_daily_predictions.py
```

### 4. Expected Output
```
🎯 DAILY PREDICTIONS RUNNER
==================================================
📅 2024-01-15 10:30:00
==================================================

🚀 Starting Complete Prediction Pipeline
============================================================
📅 Target Date: 2024-01-15
🔄 Force Retrain: False
============================================================

🎯 STEP 1: Model Training Check
----------------------------------------
✅ Sufficient models available, skipping training

🌐 STEP 2: Fixture Fetching
----------------------------------------
✅ Fetched 45 fixtures from APIFootball
📊 Found 32 upcoming fixtures

🎯 STEP 3: Prediction Generation
----------------------------------------
📊 Prediction summary: 30 successful, 2 failed

💾 STEP 4: Database Storage
----------------------------------------
✅ Successfully stored 30 predictions in database

🎉 SUCCESS! Daily predictions are ready!

🌐 Available endpoints:
   • GET /api/daily-predictions/today
   • GET /api/accumulators/today
   • GET /api/accumulators/2-odds
   • GET /api/accumulators/5-odds
   • GET /api/accumulators/10-odds
   • GET /api/accumulators/rollover

📊 Quick Stats:
   • Fixtures: 32
   • Predictions: 30
   • Success Rate: 93.8%
```

## 🔄 Automation Setup

### Daily Cron Job
```bash
# Edit crontab
crontab -e

# Add this line for daily 6 AM execution
0 6 * * * cd /home/buck/Desktop/betsightly-backend && python run_daily_predictions.py >> /var/log/predictions.log 2>&1
```

### Weekly Model Retraining
```bash
# Add this line for weekly retraining (Sundays at 2 AM)
0 2 * * 0 cd /home/buck/Desktop/betsightly-backend && python complete_prediction_pipeline.py --force-retrain >> /var/log/training.log 2>&1
```

## 🌐 Frontend Integration

After running the pipeline, your frontend can access:

```javascript
// Get today's predictions
fetch('/api/daily-predictions/today')

// Get accumulator categories
fetch('/api/accumulators/today')
fetch('/api/accumulators/2-odds')    // Low risk
fetch('/api/accumulators/5-odds')    // Medium risk  
fetch('/api/accumulators/10-odds')   // High risk
fetch('/api/accumulators/rollover')  // Rollover strategy
```

## 🚨 Troubleshooting

### Common Issues

1. **"No API key configured"**
   ```bash
   export APIFOOTBALL_API_KEY=your_key_here
   ```

2. **"Import errors"**
   ```bash
   pip install --break-system-packages -r requirements.txt
   ```

3. **"No fixtures found"**
   - Check if API key is valid
   - Try a different date
   - Check internet connection

4. **"Models not found"**
   ```bash
   # Force retrain models
   python complete_prediction_pipeline.py --train-only
   ```

## 🎯 What This Replaces

Your new pipeline **replaces** these individual scripts:
- ❌ `generate_daily_predictions.py`
- ❌ `generate_predictions_for_frontend.py`  
- ❌ `generate_predictions_comprehensive_games.py`
- ❌ `ml_pipeline_streamlined.py` (for daily use)

But **enhances** your existing services:
- ✅ Uses `services/apifootball_service.py`
- ✅ Uses `api/endpoints/ml_predictions.py`
- ✅ Uses `train_models_github_dataset.py`
- ✅ Stores in `services/daily_predictions_service.py`

## 🎉 Success Indicators

You'll know it's working when:
- ✅ Models are loaded (28 available)
- ✅ Fixtures are fetched from APIFootball
- ✅ Predictions generated with >80% success rate
- ✅ Data stored in database
- ✅ Frontend endpoints return fresh data

## 🚀 Ready to Go!

**Your system is ready!** Just set your API key and run:

```bash
# Set API key
export APIFOOTBALL_API_KEY=your_key_here

# Run daily predictions
python run_daily_predictions.py
```

That's it! Your complete prediction pipeline will:
1. ✅ Check models (28 already available)
2. ✅ Fetch today's fixtures from APIFootball
3. ✅ Generate predictions using trained models
4. ✅ Store results for frontend consumption

---

**Need help?** Check the logs or run `python simple_pipeline_test.py` to diagnose issues.
