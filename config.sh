#!/bin/bash

# E-Paper Display Configuration
# This file contains all the configuration variables used throughout the project

# Service names
BACKEND_SERVICE_NAME="e-paper-backend"
FRONTEND_SERVICE_NAME="e-paper-frontend"

# Project structure
PROJECT_NAME="e-paper-canvas"
FRONTEND_DIR="frontend"
BACKEND_DIR="backend"

# Ports
BACKEND_PORT="8000"
FRONTEND_PORT="5173"

# Python virtual environment
VENV_DIR="venv"

# Template files
BACKEND_SERVICE_TEMPLATE="${BACKEND_SERVICE_NAME}@.service"
FRONTEND_SERVICE_TEMPLATE="${FRONTEND_SERVICE_NAME}@.service"

# Generated service files (will be created with user suffix)
BACKEND_SERVICE_FILE="${BACKEND_SERVICE_NAME}@\${USER}.service"
FRONTEND_SERVICE_FILE="${FRONTEND_SERVICE_NAME}@\${USER}.service"

# Systemd service paths
SYSTEMD_DIR="/etc/systemd/system"

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

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Get the current directory (where the script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Export variables so they can be used by other scripts
export BACKEND_SERVICE_NAME
export FRONTEND_SERVICE_NAME
export PROJECT_NAME
export FRONTEND_DIR
export BACKEND_DIR
export BACKEND_PORT
export FRONTEND_PORT
export VENV_DIR
export BACKEND_SERVICE_TEMPLATE
export FRONTEND_SERVICE_TEMPLATE
export SYSTEMD_DIR
export SCRIPT_DIR 