#!/bin/bash

# 🎯 Betsightly Enhanced Prediction System - Deployment Script
# Automated setup and deployment for production environment

set -e  # Exit on any error

echo "🚀 BETSIGHTLY ENHANCED PREDICTION SYSTEM DEPLOYMENT"
echo "=" * 60
echo "📅 Deployment Date: $(date)"
echo "=" * 60

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Python 3.8+ is installed
check_python() {
    print_info "Checking Python version..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_status "Python $PYTHON_VERSION found"
        
        # Check if version is 3.8 or higher
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            print_status "Python version is compatible (3.8+)"
        else
            print_error "Python 3.8+ required. Current version: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.8+"
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    print_info "Creating virtual environment..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_status "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_status "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_info "Installing dependencies..."
    
    # Upgrade pip first
    pip install --upgrade pip
    
    # Install from requirements file
    if [ -f "requirements_enhanced.txt" ]; then
        pip install -r requirements_enhanced.txt
        print_status "Enhanced dependencies installed"
    elif [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_status "Standard dependencies installed"
    else
        print_error "No requirements file found"
        exit 1
    fi
}

# Setup environment variables
setup_environment() {
    print_info "Setting up environment variables..."
    
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating template..."
        cat > .env << EOF
# APIFootball.com API Key (Required)
APIFOOTBALL_API_KEY=your_api_key_here

# Telegram Integration (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# N8N Webhook (Optional)
N8N_WEBHOOK_URL=your_n8n_webhook_url

# Database Configuration
DATABASE_URL=sqlite:///./football.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Environment
ENVIRONMENT=production
DEBUG=false

# Logging
LOG_LEVEL=INFO
LOG_FILE=betsightly_system.log
EOF
        print_warning "Please edit .env file with your actual API keys and configuration"
    else
        print_status ".env file already exists"
    fi
}

# Initialize database
initialize_database() {
    print_info "Initializing enhanced database..."
    
    if python initialize_enhanced_database.py; then
        print_status "Database initialized successfully"
    else
        print_error "Database initialization failed"
        exit 1
    fi
}

# Test system functionality
test_system() {
    print_info "Testing system functionality..."
    
    # Test system status
    if python main_prediction_system.py --mode status; then
        print_status "System status check passed"
    else
        print_error "System status check failed"
        exit 1
    fi
}

# Create systemd service (Linux only)
create_systemd_service() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_info "Creating systemd service..."
        
        CURRENT_DIR=$(pwd)
        USER=$(whoami)
        
        sudo tee /etc/systemd/system/betsightly.service > /dev/null << EOF
[Unit]
Description=Betsightly Enhanced Prediction System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$CURRENT_DIR/venv/bin
ExecStart=$CURRENT_DIR/venv/bin/python main_prediction_system.py --mode server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        sudo systemctl enable betsightly.service
        print_status "Systemd service created and enabled"
    else
        print_warning "Systemd service creation skipped (not Linux)"
    fi
}

# Create startup scripts
create_startup_scripts() {
    print_info "Creating startup scripts..."
    
    # Daily predictions script
    cat > run_daily_predictions.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python main_prediction_system.py --mode daily
EOF
    chmod +x run_daily_predictions.sh
    
    # Start server script
    cat > start_server.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python main_prediction_system.py --mode server
EOF
    chmod +x start_server.sh
    
    # Start scheduler script
    cat > start_scheduler.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python main_prediction_system.py --mode scheduler
EOF
    chmod +x start_scheduler.sh
    
    print_status "Startup scripts created"
}

# Setup cron jobs
setup_cron_jobs() {
    print_info "Setting up cron jobs..."
    
    CURRENT_DIR=$(pwd)
    
    # Create cron job for daily predictions
    (crontab -l 2>/dev/null; echo "0 6 * * * cd $CURRENT_DIR && ./run_daily_predictions.sh >> logs/daily_predictions.log 2>&1") | crontab -
    
    print_status "Cron jobs configured"
    print_info "Daily predictions will run at 6:00 AM every day"
}

# Create logs directory
create_logs_directory() {
    print_info "Creating logs directory..."
    mkdir -p logs
    print_status "Logs directory created"
}

# Main deployment function
main() {
    echo
    print_info "Starting Betsightly Enhanced Prediction System deployment..."
    echo
    
    # Run deployment steps
    check_python
    create_venv
    install_dependencies
    setup_environment
    create_logs_directory
    initialize_database
    test_system
    create_startup_scripts
    create_systemd_service
    setup_cron_jobs
    
    echo
    print_status "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!"
    echo
    print_info "Next steps:"
    echo "1. Edit .env file with your API keys"
    echo "2. Start the server: ./start_server.sh"
    echo "3. Generate predictions: ./run_daily_predictions.sh"
    echo "4. Start scheduler: ./start_scheduler.sh"
    echo
    print_info "API will be available at: http://localhost:8000"
    print_info "API documentation: http://localhost:8000/docs"
    echo
    print_info "System logs: logs/betsightly_system.log"
    print_info "Daily prediction logs: logs/daily_predictions.log"
    echo
}

# Run main function
main "$@"
