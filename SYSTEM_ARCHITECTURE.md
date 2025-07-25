# 🏗️ BETSIGHTLY SYSTEM ARCHITECTURE

## 📊 CURRENT SYSTEM OVERVIEW

### **CORE ESSENTIAL COMPONENTS (49 components)**

#### **🎯 Main Prediction Pipeline**
```
APIFootball.com → Enhanced ML Pipeline → Database → API Endpoints
```

**Core Files:**
- `ml_pipeline_streamlined.py` - Main ML pipeline with 18 models
- `services/enhanced_feature_extractor.py` - 62 advanced features
- `services/apifootball_service.py` - Data fetching from API
- `complete_prediction_pipeline.py` - End-to-end orchestration

#### **🗄️ Enhanced Caching System**
```
Predictions → Cache Service → Database → Retrieval Service → API
```

**Core Files:**
- `services/prediction_cache_service.py` - Caching with session management
- `services/prediction_retrieval_service.py` - Fast API responses
- `database_schema_enhanced.py` - Enhanced database tables
- `services/daily_predictions_service.py` - Legacy compatibility

#### **📊 Analytics and Tracking**
```
Match Results → Analytics Service → Performance Metrics → Database
```

**Core Files:**
- `services/prediction_analytics_service.py` - Result tracking
- `services/data_cleanup_service.py` - Automated cleanup
- `services/prediction_orchestrator.py` - Scheduling system

#### **🎲 Accumulator System**
```
Predictions → Accumulator Builder → Risk Assessment → API Endpoints
```

**Core Files:**
- `services/accumulator_builder.py` - Diverse accumulator generation
- `api/endpoints/accumulators.py` - Accumulator API endpoints

#### **🌐 API Layer**
```
FastAPI → Router → Endpoints → Services → Database
```

**Core Files:**
- `main.py` - FastAPI application
- `api/endpoints/daily_predictions.py` - Prediction endpoints
- `api/endpoints/health.py` - System health monitoring

#### **📱 Integration Layer**
```
Telegram Bot ← API ← Database
N8N Webhooks ← API ← Database
```

**Core Files:**
- `telegram_bot.py` - Telegram integration
- `run_telegram_bot.py` - Bot startup
- `start_with_telegram.py` - Combined startup

### **🗑️ REDUNDANT COMPONENTS (13 components)**

**Files to Remove:**
- `comprehensive_backup_20250725_115025/` - Old backup directory
- `test_comprehensive_caching_system.py` - Development test file
- All files in backup directories
- Old basic prediction services

### **🔗 INTEGRATION GAPS (7 components)**

**Components Needing Integration:**
- `api/endpoints/basketball_predictions.py` - Basketball system
- `api/endpoints/betting_codes.py` - Betting code management
- `api/endpoints/bookmakers.py` - Bookmaker integration
- `api/endpoints/dashboard.py` - Admin dashboard
- `api/endpoints/predictions.py` - Legacy prediction endpoint
- `api/endpoints/punters.py` - User management

### **❓ UNKNOWN COMPONENTS (64 components)**

**Requires Analysis:**
- `basketball/` directory - Complete basketball prediction system
- `ml/` directory - Advanced ML models and utilities
- `utils/` directory - Utility functions
- `schemas/` directory - Data validation schemas

## 🔄 DATA FLOW ARCHITECTURE

### **1. Daily Prediction Generation**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ APIFootball.com │───▶│ Enhanced ML      │───▶│ Prediction      │
│ (289 fixtures)  │    │ Pipeline         │    │ Cache Service   │
└─────────────────┘    │ (62 features,    │    └─────────────────┘
                       │  18 models)      │              │
                       └──────────────────┘              ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ API Endpoints   │◀───│ Retrieval        │◀───│ Enhanced        │
│ (Fast Response) │    │ Service          │    │ Database        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### **2. Accumulator Generation**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Cached          │───▶│ Accumulator      │───▶│ Risk Assessment │
│ Predictions     │    │ Builder          │    │ & Diversification│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ API Response    │◀───│ 4 Categories:    │◀───│ Database        │
│ (JSON)          │    │ 2/5/10/Rollover  │    │ Storage         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### **3. Analytics Pipeline**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Match Results   │───▶│ Analytics        │───▶│ Performance     │
│ (APIFootball)   │    │ Service          │    │ Metrics         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Accuracy        │◀───│ Daily/Weekly/    │◀───│ Database        │
│ Reports         │    │ Monthly Reports  │    │ Analytics       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🎯 INTEGRATION POINTS

### **✅ WORKING INTEGRATIONS**
1. **Enhanced ML Pipeline** → **Caching System** ✅
2. **Caching System** → **API Endpoints** ✅
3. **Analytics Service** → **Database** ✅
4. **Orchestrator** → **All Services** ✅

### **⚠️ INTEGRATION ISSUES**
1. **Database Session Management** - SQLAlchemy session conflicts
2. **API Endpoint Registration** - Enhanced endpoints need server restart
3. **Telegram Integration** - Needs connection to enhanced system
4. **N8N Webhooks** - Requires endpoint verification

### **🔧 MISSING INTEGRATIONS**
1. **Basketball System** → **Main Pipeline**
2. **Betting Codes** → **Accumulator System**
3. **Dashboard** → **Analytics System**
4. **User Management** → **Prediction System**

## 📋 COMPONENT DEPENDENCIES

### **High Priority Dependencies**
```
main.py
├── ml_pipeline_streamlined.py
├── services/prediction_cache_service.py
├── services/prediction_orchestrator.py
├── database_schema_enhanced.py
└── api/endpoints/ (all core endpoints)
```

### **Medium Priority Dependencies**
```
services/prediction_orchestrator.py
├── services/prediction_analytics_service.py
├── services/data_cleanup_service.py
└── services/prediction_retrieval_service.py
```

### **Integration Dependencies**
```
telegram_bot.py
├── services/daily_predictions_service.py
└── api/endpoints/daily_predictions.py

N8N Webhooks
├── api/endpoints/accumulators.py
└── services/prediction_retrieval_service.py
```

## 🎯 NEXT PHASE ACTIONS

### **Phase 2: System Integration**
1. Fix database session management in prediction caching
2. Register enhanced API endpoints properly
3. Create single main entry point
4. Connect Telegram/N8N to enhanced system

### **Phase 3: Optimization**
1. Implement confidence-based filtering (>85%)
2. Add risk assessment scoring
3. Create diversification algorithms
4. Add bankroll management

### **Phase 4: Cleanup**
1. Remove 13 redundant components
2. Archive backup directories
3. Clean up dead code references
4. Prepare for repository deployment
