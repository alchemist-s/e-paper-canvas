#!/bin/bash

# E-Paper Display Restart Script
# This script stops systemd services, rebuilds the Vue app, and restarts the services

set -e  # Exit on any error

# Source configuration file
source "$(dirname "$0")/config.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get the current directory (where the script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_status "Restarting from: $SCRIPT_DIR"

# Function to stop systemd services
stop_services() {
    print_status "Stopping e-paper systemd services..."
    
    # Stop backend service
    if systemctl list-units --full --all | grep -q "$BACKEND_SERVICE_NAME"; then
        sudo systemctl stop "${BACKEND_SERVICE_NAME}@$USER.service"
        print_success "Stopped $BACKEND_SERVICE_NAME service"
    else
        print_warning "$BACKEND_SERVICE_NAME service not found"
    fi
    
    # Stop frontend service
    if systemctl list-units --full --all | grep -q "$FRONTEND_SERVICE_NAME"; then
        sudo systemctl stop "${FRONTEND_SERVICE_NAME}@$USER.service"
        print_success "Stopped $FRONTEND_SERVICE_NAME service"
    else
        print_warning "$FRONTEND_SERVICE_NAME service not found"
    fi
    
    print_success "All systemd services stopped"
}

# Function to rebuild Vue app
rebuild_frontend() {
    print_status "Installing and building Vue app..."
    
    cd "$FRONTEND_DIR"
    npm install
    npm run build
    cd ..
    
    print_success "Vue app built successfully"
}

# Function to restart systemd services
restart_services() {
    print_status "Restarting e-paper systemd services..."
    
    # Restart backend service
    if systemctl list-units --full --all | grep -q "$BACKEND_SERVICE_NAME"; then
        sudo systemctl restart "${BACKEND_SERVICE_NAME}@$USER.service"
        print_success "Restarted $BACKEND_SERVICE_NAME service"
    else
        print_warning "$BACKEND_SERVICE_NAME service not found"
    fi
    
    # Restart frontend service
    if systemctl list-units --full --all | grep -q "$FRONTEND_SERVICE_NAME"; then
        sudo systemctl restart "${FRONTEND_SERVICE_NAME}@$USER.service"
        print_success "Restarted $FRONTEND_SERVICE_NAME service"
    else
        print_warning "$FRONTEND_SERVICE_NAME service not found"
    fi
    
    # Wait a moment for services to start
    sleep 3
    
    # Check service status
    print_status "Checking service status..."
    if systemctl is-active --quiet "${BACKEND_SERVICE_NAME}@$USER"; then
        print_success "Python server is running ✓"
    else
        print_error "Python server failed to start"
        sudo systemctl status "${BACKEND_SERVICE_NAME}@$USER" --no-pager
    fi

    if systemctl is-active --quiet "${FRONTEND_SERVICE_NAME}@$USER"; then
        print_success "Vue frontend is running ✓"
    else
        print_error "Vue frontend failed to start"
        sudo systemctl status "${FRONTEND_SERVICE_NAME}@$USER" --no-pager
    fi
}

# Main execution
main() {
    print_status "Starting e-paper display restart process..."
    
    # Stop systemd services
    stop_services
    
    # Rebuild frontend
    rebuild_frontend
    
    # Restart systemd services
    restart_services
    
    # Get IP address for access instructions
    IP_ADDRESS=$(hostname -I | awk '{print $1}')
    
    print_success "Restart process completed!"
    print_status "Your e-paper display interface is now running:"
    print_status "• Frontend: http://$IP_ADDRESS:$FRONTEND_PORT"
    print_status "• Backend API: http://$IP_ADDRESS:$BACKEND_PORT"
    print_status "• Check status: sudo systemctl status ${BACKEND_SERVICE_NAME}@$USER ${FRONTEND_SERVICE_NAME}@$USER"
}

# Run main function
main "$@" 