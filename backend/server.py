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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
