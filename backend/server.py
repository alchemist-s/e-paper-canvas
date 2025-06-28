#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import base64
import logging
import tempfile
import asyncio
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
import uvicorn
from lib.transport_api import TransportNSWAPI
from datetime import datetime

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # dotenv not installed, continue without it
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="E-Paper Web Display Server")

# Add CORS middleware to allow web app to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local network deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Transport NSW API
# You'll need to set this environment variable with your API key
TRANSPORT_API_KEY = os.getenv("TRANSPORT_API_KEY", "")
if TRANSPORT_API_KEY:
    transport_api = TransportNSWAPI(TRANSPORT_API_KEY)
    logger.info("Transport NSW API initialized successfully")
else:
    logger.warning("TRANSPORT_API_KEY not set - transport features will be disabled")
    transport_api = None

# Default stop ID for Central Station (you can change this)
DEFAULT_STOP_ID = "200011"  # Central Station

# Journey configuration for Rhodes to Central
RHODES_STOP_ID = "213891"  # Rhodes Station
CENTRAL_STOP_ID = "10101100"  # Central Station


class RegionUpdate(BaseModel):
    """Represents a region update with bounding box and image data"""

    x: int
    y: int
    width: int
    height: int
    image_data: str  # Base64 encoded image for this region

    @field_validator("x", "y", "width", "height", mode="before")
    @classmethod
    def coerce_to_int(cls, v):
        """Coerce float values to integers"""
        if v is not None:
            return int(float(v))
        return v


class RegionUpdateRequest(BaseModel):
    """Request containing multiple region updates"""

    regions: List[RegionUpdate]


class ScreenshotRequest(BaseModel):
    """Legacy full image update request"""

    image_data: str  # Base64 encoded image


async def process_region_update(region: RegionUpdate) -> bool:
    """Process a single region update using subprocess"""
    try:
        # Create a temporary file for the region image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            # Decode base64 image data
            image_data = base64.b64decode(
                region.image_data.split(",")[1]
                if "," in region.image_data
                else region.image_data
            )

            # Write the region image to temporary file
            temp_file.write(image_data)
            temp_file_path = temp_file.name

        # Build the command for region update
        cmd = [
            "python3",
            "epd_updater.py",
            temp_file_path,
            "--region",
            str(region.x),
            str(region.y),
            str(region.width),
            str(region.height),
        ]

        logger.info(f"Running region update command: {' '.join(cmd)}")

        # Run the subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd(),
        )

        # Wait for the process to complete
        stdout, stderr = await process.communicate()

        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except:
            pass

        if process.returncode == 0:
            logger.info(
                f"Region update successful: ({region.x}, {region.y}) {region.width}x{region.height}"
            )
            if stdout:
                logger.info(f"Region update output: {stdout.decode()}")
            return True
        else:
            logger.error(f"Region update failed with return code {process.returncode}")
            if stderr:
                logger.error(f"Region update stderr: {stderr.decode()}")
            return False

    except Exception as e:
        logger.error(f"Error processing region update: {e}")
        return False


@app.on_event("startup")
async def startup_event():
    """Initialize the e-paper display on startup"""
    try:
        # Initialize the EPD display
        logger.info("Initializing e-paper display...")
        result = await asyncio.create_subprocess_exec(
            "python3",
            "epd_init.py",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd(),
        )

        stdout, stderr = await result.communicate()

        if result.returncode == 0:
            logger.info("E-paper display initialized successfully")
            if stdout:
                logger.info(f"EPD init output: {stdout.decode()}")
        else:
            logger.error(
                f"EPD initialization failed with return code {result.returncode}"
            )
            if stderr:
                logger.error(f"EPD init stderr: {stderr.decode()}")

    except Exception as e:
        logger.error(f"Failed to initialize e-paper display: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up the e-paper display on shutdown"""
    try:
        logger.info("Putting e-paper display to sleep...")
        result = await asyncio.create_subprocess_exec(
            "python3",
            "epd_sleep.py",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd(),
        )

        stdout, stderr = await result.communicate()

        if result.returncode == 0:
            logger.info("E-paper display put to sleep successfully")
        else:
            logger.error(f"Failed to put EPD to sleep: {stderr.decode()}")

    except Exception as e:
        logger.error(f"Error putting display to sleep: {e}")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "running", "display_connected": True}


@app.post("/update-regions")
async def update_regions(request: RegionUpdateRequest):
    """Update the e-paper display with specific regions using subprocess"""
    try:
        logger.info(f"Processing {len(request.regions)} region updates")

        # Process each region iteratively using subprocess
        successful_updates = 0
        for i, region in enumerate(request.regions):
            logger.info(
                f"Processing region {i+1}/{len(request.regions)}: ({region.x}, {region.y}) {region.width}x{region.height}"
            )

            success = await process_region_update(region)
            if success:
                successful_updates += 1
            else:
                logger.warning(f"Failed to update region {i+1}")

        logger.info(
            f"Region updates completed: {successful_updates}/{len(request.regions)} successful"
        )
        return {
            "status": "success",
            "message": f"Updated {successful_updates}/{len(request.regions)} regions",
        }

    except Exception as e:
        logger.error(f"Error updating regions: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update regions: {str(e)}"
        )


@app.post("/update-display")
async def update_display(request: ScreenshotRequest):
    """Legacy endpoint for full image updates using subprocess"""
    try:
        # Create a temporary file for the full image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            # Decode base64 image data
            image_data = base64.b64decode(
                request.image_data.split(",")[1]
                if "," in request.image_data
                else request.image_data
            )

            # Write the image to temporary file
            temp_file.write(image_data)
            temp_file_path = temp_file.name

        # Build the command for full image update
        cmd = ["python3", "epd_updater.py", temp_file_path]

        logger.info(f"Running full image update command: {' '.join(cmd)}")

        # Run the subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd(),
        )

        # Wait for the process to complete
        stdout, stderr = await process.communicate()

        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except:
            pass

        if process.returncode == 0:
            logger.info("Full image update completed successfully")
            if stdout:
                logger.info(f"Update output: {stdout.decode()}")

            return {"status": "success", "message": "Display updated"}
        else:
            logger.error(
                f"Full image update failed with return code {process.returncode}"
            )
            if stderr:
                logger.error(f"Update stderr: {stderr.decode()}")
            raise HTTPException(status_code=500, detail="Failed to update display")

    except Exception as e:
        logger.error(f"Error updating display: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update display: {str(e)}"
        )


@app.get("/status")
async def get_status():
    """Get current display status"""
    return {
        "display_connected": True,
    }


# Transport API endpoints
@app.get("/transport/departures")
async def get_transport_departures(
    stop_id: str = DEFAULT_STOP_ID, max_results: int = 5
):
    """Get transport departures for a specific stop"""
    if not transport_api:
        raise HTTPException(status_code=503, detail="Transport API not configured")

    try:
        # Get departures using the departure monitor endpoint (matches official schema)
        departures_data = transport_api.get_departures_via_departure_monitor(
            stop_id, max_results=max_results
        )

        # Extract stopEvents from the DepartureMonitorResponse
        stop_events = departures_data.get("stopEvents", [])
        formatted_departures = []

        for event in stop_events[:max_results]:
            transportation = event.get("transportation", {})
            location = event.get("location", {})

            # Get departure times
            departure_time_planned = event.get("departureTimePlanned")
            departure_time_estimated = event.get("departureTimeEstimated")

            # Calculate minutes until departure
            minutes_until_departure = 0
            departure_time_str = "N/A"

            if departure_time_estimated or departure_time_planned:
                try:
                    departure_time = departure_time_estimated or departure_time_planned
                    dep_time = datetime.fromisoformat(
                        departure_time.replace("Z", "+00:00")
                    )
                    current_time = datetime.now(dep_time.tzinfo)
                    time_diff = dep_time - current_time
                    minutes_until_departure = max(
                        0, int(time_diff.total_seconds() / 60)
                    )
                    departure_time_str = dep_time.strftime("%H:%M")
                except Exception as e:
                    logger.warning(f"Could not parse departure time: {e}")

            # Extract destination information
            destination_info = transportation.get("destination", {})
            destination_name = destination_info.get("name", "N/A")

            # Extract platform information
            platform = "N/A"
            if location and location.get("properties"):
                platform = location.get("properties", {}).get("platform", "N/A")

            # Extract transport mode information
            product_info = transportation.get("product", {})
            transport_mode = product_info.get("name", "Unknown")
            transport_class = product_info.get("class", 0)

            # Determine status
            is_realtime = transportation.get("isRealtimeControlled", False)
            status = "On Time" if is_realtime else "Scheduled"

            formatted_departure = {
                "time": departure_time_str,
                "minutesUntilDeparture": minutes_until_departure,
                "line": transportation.get("number", ""),
                "destination": destination_name,
                "platform": platform,
                "transportMode": transport_mode,
                "transportClass": transport_class,
                "status": status,
                "isRealtime": is_realtime,
                "operator": transportation.get("operator", {}).get("name", ""),
                "description": transportation.get("description", ""),
            }
            formatted_departures.append(formatted_departure)

        return {
            "stop_id": stop_id,
            "departures": formatted_departures,
            "count": len(formatted_departures),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error fetching transport departures: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch transport data: {str(e)}"
        )


@app.get("/transport/summary")
async def get_transport_summary():
    """Get a simplified transport summary for the widget - Rhodes to Central journey"""
    if not transport_api:
        raise HTTPException(status_code=503, detail="Transport API not configured")

    try:
        # Get departures from Rhodes station to get multiple trains
        departures_data = transport_api.get_departures_via_departure_monitor(
            RHODES_STOP_ID, max_results=3
        )

        # Extract stopEvents from the DepartureMonitorResponse
        stop_events = departures_data.get("stopEvents", [])

        if not stop_events:
            return {
                "nextTrain": "No trains",
                "destination": "Central",
                "platform": "N/A",
                "status": "No service",
                "minutesUntilArrival": 0,
                "followingTrain": "No trains",
                "followingMinutesUntilArrival": 0,
            }

        # Get the first two departures
        next_departure = None
        following_departure = None

        for event in stop_events:
            transportation = event.get("transportation", {})
            destination_info = transportation.get("destination", {})
            destination_name = destination_info.get("name", "")

            # Only include trains going to Central
            if "Central" in destination_name:
                if next_departure is None:
                    next_departure = event
                elif following_departure is None:
                    following_departure = event
                    break

        # Process next departure
        next_train_data = {
            "nextTrain": "No trains",
            "destination": "Central",
            "platform": "N/A",
            "status": "No service",
            "minutesUntilArrival": 0,
        }

        if next_departure:
            departure_time_planned = next_departure.get("departureTimePlanned")
            departure_time_estimated = next_departure.get("departureTimeEstimated")

            if departure_time_estimated or departure_time_planned:
                try:
                    departure_time = departure_time_estimated or departure_time_planned
                    dep_time = datetime.fromisoformat(
                        departure_time.replace("Z", "+00:00")
                    )
                    current_time = datetime.now(dep_time.tzinfo)
                    time_diff = dep_time - current_time
                    minutes_until_departure = max(
                        0, int(time_diff.total_seconds() / 60)
                    )
                    departure_time_str = dep_time.strftime("%H:%M")

                    next_train_data = {
                        "nextTrain": departure_time_str,
                        "destination": "Central",
                        "platform": "N/A",
                        "status": (
                            "On Time"
                            if transportation.get("isRealtimeControlled", False)
                            else "Scheduled"
                        ),
                        "minutesUntilArrival": minutes_until_departure,
                    }
                except Exception as e:
                    logger.warning(f"Could not parse next departure time: {e}")

        # Process following departure
        following_train_data = {
            "followingTrain": "No trains",
            "followingMinutesUntilArrival": 0,
        }

        if following_departure:
            departure_time_planned = following_departure.get("departureTimePlanned")
            departure_time_estimated = following_departure.get("departureTimeEstimated")

            if departure_time_estimated or departure_time_planned:
                try:
                    departure_time = departure_time_estimated or departure_time_planned
                    dep_time = datetime.fromisoformat(
                        departure_time.replace("Z", "+00:00")
                    )
                    current_time = datetime.now(dep_time.tzinfo)
                    time_diff = dep_time - current_time
                    minutes_until_departure = max(
                        0, int(time_diff.total_seconds() / 60)
                    )
                    departure_time_str = dep_time.strftime("%H:%M")

                    following_train_data = {
                        "followingTrain": departure_time_str,
                        "followingMinutesUntilArrival": minutes_until_departure,
                    }
                except Exception as e:
                    logger.warning(f"Could not parse following departure time: {e}")

        # Combine the data
        return {**next_train_data, **following_train_data}

    except Exception as e:
        logger.error(f"Error fetching transport summary: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch transport summary: {str(e)}"
        )


@app.get("/transport/stops/search")
async def search_stops(query: str, type_sf: str = "any"):
    """Search for transport stops"""
    if not transport_api:
        raise HTTPException(status_code=503, detail="Transport API not configured")

    try:
        # Use the stop_finder endpoint with proper parameters
        stops_data = transport_api.find_stop(query, stop_type=type_sf)

        # Extract locations from StopFinderResponse
        locations = stops_data.get("locations", [])

        # Format the response to be more useful
        formatted_stops = []
        for location in locations:
            # Get assigned stops if available
            assigned_stops = location.get("assignedStops", [])

            formatted_location = {
                "id": location.get("id", ""),
                "name": location.get("name", ""),
                "disassembledName": location.get("disassembledName", ""),
                "type": location.get("type", ""),
                "coord": location.get("coord", []),
                "isBest": location.get("isBest", False),
                "matchQuality": location.get("matchQuality", 0),
                "modes": location.get("modes", []),
                "assignedStops": [
                    {
                        "id": stop.get("id", ""),
                        "name": stop.get("name", ""),
                        "distance": stop.get("distance", 0),
                        "duration": stop.get("duration", 0),
                        "modes": stop.get("modes", []),
                    }
                    for stop in assigned_stops
                ],
            }
            formatted_stops.append(formatted_location)

        return {
            "query": query,
            "type": type_sf,
            "locations": formatted_stops,
            "count": len(formatted_stops),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error searching stops: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search stops: {str(e)}")


@app.get("/transport/alerts")
async def get_service_alerts(
    stop_id: str = None, modes: str = None, date: str = None, current_only: bool = True
):
    """Get service alerts and disruptions"""
    if not transport_api:
        raise HTTPException(status_code=503, detail="Transport API not configured")

    try:
        # Parse modes parameter if provided
        mode_list = None
        if modes:
            mode_list = [
                int(m.strip()) for m in modes.split(",") if m.strip().isdigit()
            ]

        # Parse date if provided
        date_obj = None
        if date:
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
                )

        # Get service alerts
        alerts_data = transport_api.get_service_alerts(
            date=date_obj, modes=mode_list, stop_id=stop_id
        )

        # Extract alerts from AdditionalInfoResponse
        infos = alerts_data.get("infos", {})
        current_alerts = infos.get("current", []) if current_only else []
        historic_alerts = infos.get("historic", []) if not current_only else []

        # Combine alerts based on filter
        all_alerts = current_alerts + historic_alerts

        # Format alerts for response
        formatted_alerts = []
        for alert in all_alerts:
            formatted_alert = {
                "id": alert.get("id", ""),
                "type": alert.get("type", ""),
                "priority": alert.get("priority", ""),
                "subtitle": alert.get("subtitle", ""),
                "content": alert.get("content", ""),
                "url": alert.get("url", ""),
                "urlText": alert.get("urlText", ""),
                "version": alert.get("version", 1),
                "timestamps": alert.get("timestamps", {}),
                "affected": alert.get("affected", {}),
            }
            formatted_alerts.append(formatted_alert)

        return {
            "stop_id": stop_id,
            "modes": mode_list,
            "date": date,
            "current_only": current_only,
            "alerts": formatted_alerts,
            "count": len(formatted_alerts),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error fetching service alerts: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch service alerts: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
