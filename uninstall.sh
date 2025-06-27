#!/bin/bash

# E-Paper Display Web Interface - Uninstaller
# This script removes the e-paper display services and cleans up the installation

set -e  # Exit on any error

# Source configuration file
source "$(dirname "$0")/config.sh"

echo "=========================================="
echo "E-Paper Display Web Interface Uninstaller"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_status "Uninstalling from: $SCRIPT_DIR"

# Get current user
CURRENT_USER=$(whoami)
print_status "Uninstalling services for user: $CURRENT_USER"

# Stop services
print_status "Stopping services..."
sudo systemctl stop "${BACKEND_SERVICE_NAME}@$CURRENT_USER" "${FRONTEND_SERVICE_NAME}@$CURRENT_USER" 2>/dev/null || print_warning "Services were not running"

# Disable services
print_status "Disabling services..."
sudo systemctl disable "${BACKEND_SERVICE_NAME}@$CURRENT_USER" "${FRONTEND_SERVICE_NAME}@$CURRENT_USER" 2>/dev/null || print_warning "Services were not enabled"

# Remove service files
print_status "Removing service files..."
sudo rm -f "$SYSTEMD_DIR/${BACKEND_SERVICE_NAME}@$CURRENT_USER.service"
sudo rm -f "$SYSTEMD_DIR/${FRONTEND_SERVICE_NAME}@$CURRENT_USER.service"

# Reload systemd
print_status "Reloading systemd..."
sudo systemctl daemon-reload

# Remove virtual environment
if [ -d "$BACKEND_DIR/$VENV_DIR" ]; then
    print_status "Removing Python virtual environment..."
    rm -rf "$BACKEND_DIR/$VENV_DIR"
else
    print_status "Virtual environment not found, skipping..."
fi

# Remove built frontend
if [ -d "$FRONTEND_DIR/dist" ]; then
    print_status "Removing built frontend..."
    rm -rf "$FRONTEND_DIR/dist"
else
    print_status "Built frontend not found, skipping..."
fi

# Remove node_modules (optional - ask user)
read -p "Do you want to remove node_modules? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d "$FRONTEND_DIR/node_modules" ]; then
        print_status "Removing node_modules..."
        rm -rf "$FRONTEND_DIR/node_modules"
    else
        print_status "node_modules not found, skipping..."
    fi
else
    print_status "Keeping node_modules..."
fi

# Remove generated service files
print_status "Removing generated service files..."
rm -f "${BACKEND_SERVICE_NAME}@$CURRENT_USER.service"
rm -f "${FRONTEND_SERVICE_NAME}@$CURRENT_USER.service"

# Verify services are removed
print_status "Verifying services are removed..."
if ! systemctl list-unit-files | grep -q "${BACKEND_SERVICE_NAME}@$CURRENT_USER"; then
    print_status "✓ Backend service removed successfully"
else
    print_error "✗ Backend service still exists"
fi

if ! systemctl list-unit-files | grep -q "${FRONTEND_SERVICE_NAME}@$CURRENT_USER"; then
    print_status "✓ Frontend service removed successfully"
else
    print_error "✗ Frontend service still exists"
fi

echo ""
echo "=========================================="
echo "Uninstallation Complete!"
echo "=========================================="
echo ""
echo "The following have been removed:"
echo "• Systemd services (${BACKEND_SERVICE_NAME}@$CURRENT_USER, ${FRONTEND_SERVICE_NAME}@$CURRENT_USER)"
echo "• Python virtual environment ($BACKEND_DIR/$VENV_DIR)"
echo "• Built frontend ($FRONTEND_DIR/dist)"
echo "• Generated service files"
echo ""
echo "The following remain:"
echo "• Source code ($FRONTEND_DIR/, $BACKEND_DIR/)"
echo "• Configuration files (package.json, requirements.txt)"
echo "• This uninstall script"
echo ""
print_status "Uninstallation completed successfully!" 