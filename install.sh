#!/bin/bash

# E-Paper Display Web Interface - Automated Installer
# This script sets up the complete environment for running the e-paper display interface

set -e  # Exit on any error

# Source configuration file
source "$(dirname "$0")/config.sh"

echo "=========================================="
echo "E-Paper Display Web Interface Installer"
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

# Get the current directory (where the script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_status "Installing from: $SCRIPT_DIR"

# Check if we're on a Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    print_warning "This doesn't appear to be a Raspberry Pi. Some features may not work."
fi

# Check prerequisites
print_status "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.7+ first."
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 16+ first."
    print_status "You can install it with: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs"
    exit 1
fi

# Check npm
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm first."
    exit 1
fi

print_status "Prerequisites check passed!"

# Create virtual environment if it doesn't exist
if [ ! -d "$BACKEND_DIR/$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$BACKEND_DIR/$VENV_DIR"
    print_status "Virtual environment created."
else
    print_status "Virtual environment already exists."
fi

# Activate virtual environment and install dependencies
print_status "Installing Python dependencies..."
source "$BACKEND_DIR/$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$BACKEND_DIR/requirements.txt"

# Install and build Vue app
print_status "Installing and building Vue app..."
cd "$FRONTEND_DIR"
npm install
npm run build
cd ..

# Create service files with correct paths
print_status "Creating systemd service files..."
sed "s|/path/to/your/e-paper-main|$SCRIPT_DIR|g" "$BACKEND_SERVICE_TEMPLATE" > "${BACKEND_SERVICE_NAME}@$USER.service"
sed "s|/path/to/your/e-paper-main|$SCRIPT_DIR|g" "$FRONTEND_SERVICE_TEMPLATE" > "${FRONTEND_SERVICE_NAME}@$USER.service"

# Install systemd services
print_status "Installing systemd services..."
sudo cp "${BACKEND_SERVICE_NAME}@$USER.service" "$SYSTEMD_DIR/"
sudo cp "${FRONTEND_SERVICE_NAME}@$USER.service" "$SYSTEMD_DIR/"

# Enable services for current user
print_status "Enabling services for user: $USER"
sudo systemctl enable "${BACKEND_SERVICE_NAME}@$USER.service"
sudo systemctl enable "${FRONTEND_SERVICE_NAME}@$USER.service"

# Reload systemd and enable services
sudo systemctl daemon-reload

# Check if SPI is enabled
print_status "Checking SPI configuration..."
if ! grep -q "spidev" /proc/devices; then
    print_warning "SPI may not be enabled. Run 'sudo raspi-config' and enable SPI under Interface Options."
fi

# Add user to necessary groups for hardware access
print_status "Setting up hardware access permissions..."
sudo usermod -a -G spi,gpio,dialout $USER 2>/dev/null || print_warning "Could not add user to spi/gpio/dialout groups"
print_status "Note: You may need to reboot for group changes to take effect"

# Start services
print_status "Starting services..."
sudo systemctl start "${BACKEND_SERVICE_NAME}@$USER.service"
sudo systemctl start "${FRONTEND_SERVICE_NAME}@$USER.service"

# Check service status
print_status "Checking service status..."
if systemctl is-active --quiet "${BACKEND_SERVICE_NAME}@$USER"; then
    print_status "Python server is running ✓"
else
    print_error "Python server failed to start"
    sudo systemctl status "${BACKEND_SERVICE_NAME}@$USER" --no-pager
fi

if systemctl is-active --quiet "${FRONTEND_SERVICE_NAME}@$USER"; then
    print_status "Vue frontend is running ✓"
else
    print_error "Vue frontend failed to start"
    sudo systemctl status "${FRONTEND_SERVICE_NAME}@$USER" --no-pager
fi

# Get IP address for access instructions
IP_ADDRESS=$(hostname -I | awk '{print $1}')

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Your e-paper display interface is now running:"
echo "• Frontend: http://$IP_ADDRESS:$FRONTEND_PORT"
echo "• Backend API: http://$IP_ADDRESS:$BACKEND_PORT"
echo ""
echo "Service Management:"
echo "• Check status: sudo systemctl status ${BACKEND_SERVICE_NAME}@$USER ${FRONTEND_SERVICE_NAME}@$USER"
echo "• View logs: sudo journalctl -u ${BACKEND_SERVICE_NAME}@$USER -f"
echo "• Restart: sudo systemctl restart ${BACKEND_SERVICE_NAME}@$USER ${FRONTEND_SERVICE_NAME}@$USER"
echo ""
echo "If you encounter hardware access issues:"
echo "1. Enable SPI: sudo raspi-config → Interface Options → SPI"
echo "2. Reboot: sudo reboot"
echo ""
print_status "Installation completed successfully!" 