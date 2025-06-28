# E-Paper Display Web Interface

A web-based interface for controlling e-paper displays on Raspberry Pi, featuring a Vue.js frontend and FastAPI backend with Transport NSW API integration.

## Project Structure

```
e-paper-main/
├── frontend/          # Vue.js web application
│   ├── src/          # Vue source code
│   ├── dist/         # Built frontend (generated)
│   └── package.json  # Frontend dependencies
├── backend/          # Python FastAPI server
│   ├── server.py     # Main server file
│   ├── lib/          # Waveshare e-paper library + Transport API
│   ├── epd_*.py      # E-paper display scripts
│   ├── .env.example  # Environment variables template
│   ├── test_transport_simple.py  # Transport API test script
│   └── requirements.txt # Python dependencies
├── install.sh        # Automated setup script
└── README.md         # This file
```

## Features

- Web-based interface for e-paper display control
- Real-time display updates
- Region-based updates for efficient rendering
- Transport NSW API integration for live train/bus information
- Weather widget support
- Automatic service management with systemd

## Prerequisites

- Raspberry Pi (tested on Pi 4)
- Python 3.7+
- Node.js 16+
- npm
- Transport NSW API key (optional, for transport features)

## Quick Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/e-paper-canvas.git
   cd e-paper-canvas
   ```

2. **Run the automated setup:**

   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Set up Transport API (optional):**

   ```bash
   cd backend
   python setup_transport.py
   ```

4. **Access the web interface:**
   - Frontend: http://your-pi-ip:5173
   - Backend API: http://your-pi-ip:8000

## Transport API Setup

To enable transport widgets with live train/bus information:

1. **Get a Transport NSW API key:**

   - Visit [Transport NSW Developer Portal](https://opendata.transport.nsw.gov.au/)
   - Register for an account
   - Create a new application
   - Copy your API key

2. **Create a `.env` file in the backend directory:**

   ```bash
   cd backend
   cp .env.example .env
   ```

   Then edit the `.env` file and replace `your_api_key_here` with your actual Transport NSW API key.

3. **Test the integration:**

   ```bash
   python test_transport_simple.py
   ```

4. **Customize the journey:**
   - Edit `RHODES_STOP_ID` and `CENTRAL_STOP_ID` in `backend/server.py`
   - Common stops: Central (10101100), Rhodes (213891), Town Hall (10101200)

## Widgets

The system supports several widget types:

- **Transport Widget**: Shows next train/bus departures with real-time data
- **Weather Widget**: Displays current weather conditions
- **Time Widget**: Shows current time and date

Widgets can be added, moved, and removed through the web interface.

## Uninstallation

To remove the services and clean up the installation:

```bash
chmod +x uninstall.sh
./uninstall.sh
```

This will:

- Stop and remove systemd services
- Remove Python virtual environment
- Remove built frontend files
- Optionally remove node_modules
- Clean up generated files

## Service Management

- **Start services:** `sudo systemctl start e-paper-backend@$USER e-paper-frontend@$USER`
- **Stop services:** `sudo systemctl stop e-paper-backend@$USER e-paper-frontend@$USER`
- **Check status:** `sudo systemctl status e-paper-backend@$USER e-paper-frontend@$USER`
- **View logs:** `sudo journalctl -u e-paper-backend@$USER -f`

## Development

- **Run backend in development:** `cd backend && python server.py`
- **Run frontend in development:** `cd frontend && npm run dev`

## Configuration

The project uses a centralized configuration file (`config.sh`) that contains all service names, ports, and paths. This makes it easy to modify settings without editing multiple files.

Key configuration variables:

- `BACKEND_SERVICE_NAME`: "e-paper-backend"
- `FRONTEND_SERVICE_NAME`: "e-paper-frontend"
- `BACKEND_PORT`: "8000"
- `FRONTEND_PORT`: "5173"

## Troubleshooting

### Hardware Access Issues

If you encounter SPI/GPIO access problems:

1. Ensure SPI is enabled: `sudo raspi-config` → Interface Options → SPI
2. Add your user to the `spi` and `gpio` groups:
   ```bash
   sudo usermod -a -G spi,gpio $USER
   ```
3. Reboot: `sudo reboot`

### Service Issues

- Check service logs: `sudo journalctl -u e-paper-backend@$USER -f`
- Verify paths in service files: `sudo systemctl cat e-paper-backend@$USER`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
