#!/usr/bin/env python3

import sys
import os
from PIL import Image
import argparse

# Add the lib directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))

# E-Paper display dimensions
EPD_WIDTH = 800
EPD_HEIGHT = 480


def update_single_region(epd, region_image, x, y, width, height):
    """Update a single region of the e-paper display"""
    try:
        # Prepare the region image
        region_image = prepare_image_for_epd(region_image)

        # Ensure the region image matches the expected size
        if region_image.size != (width, height):
            region_image = region_image.resize(
                (width, height), Image.Resampling.LANCZOS
            )

        # Calculate the region boundaries
        x_min, y_min = x, y
        x_max, y_max = x + width, y + height

        # Ensure all values are integers
        x_min = int(x_min)
        y_min = int(y_min)
        x_max = int(x_max)
        y_max = int(y_max)

        # Align region boundaries to 8-byte boundaries for e-paper
        if (
            (x_min % 8 + x_max % 8 == 8 and x_min % 8 > x_max % 8)
            or x_min % 8 + x_max % 8 == 0
            or (x_max - x_min) % 8 == 0
        ):
            x_min = x_min // 8 * 8
            x_max = x_max // 8 * 8
        else:
            x_min = x_min // 8 * 8
            if x_max % 8 == 0:
                x_max = x_max // 8 * 8
            else:
                x_max = x_max // 8 * 8 + 1

        print(f"Updating region: ({x_min},{y_min}) to ({x_max},{y_max})")

        # Calculate buffer size
        width_bytes = (x_max - x_min) // 8
        height = y_max - y_min

        # First, clear the region to black
        black_buffer = bytearray([0x00] * width_bytes * height)
        print(f"Clearing region to black...")
        epd.display_Partial(black_buffer, x_min, y_min, x_max, y_max)

        # Second, clear the region to white
        white_buffer = bytearray([0xFF] * width_bytes * height)
        print(f"Clearing region to white...")
        epd.display_Partial(white_buffer, x_min, y_min, x_max, y_max)

        # Convert to 1-bit and get buffer (for partial updates, don't invert bytes)
        region_image_1bit = region_image.convert("1")
        buffer = bytearray(region_image_1bit.tobytes("raw"))

        # Third, display the actual content
        print(f"Displaying content...")
        epd.display_Partial(buffer, x_min, y_min, x_max, y_max)

        return True

    except Exception as e:
        print(f"Failed to update region ({x}, {y}) {width}x{height}: {e}")
        import traceback

        traceback.print_exc()
        return False


def prepare_image_for_epd(image):
    """Convert image to e-paper format (black and white, correct dimensions)"""
    print(f"Original image size: {image.size}, mode: {image.mode}")

    # Resize to e-paper dimensions
    image = image.resize((EPD_WIDTH, EPD_HEIGHT), Image.Resampling.LANCZOS)
    print(f"Resized image size: {image.size}")

    # Convert to 1-bit (black and white)
    if image.mode != "1":
        image = image.convert("1")

    print(f"Final image size: {image.size}, mode: {image.mode}")

    return image


def main():
    """Main function to handle image updates"""
    parser = argparse.ArgumentParser(
        description="Update e-paper display with images or regions"
    )
    parser.add_argument("image_path", help="Path to the image file")
    parser.add_argument(
        "--region",
        nargs=4,
        type=int,
        metavar=("X", "Y", "WIDTH", "HEIGHT"),
        help="Update a specific region (x, y, width, height)",
    )

    args = parser.parse_args()

    new_image_path = args.image_path
    region_coords = args.region

    print(f"New image: {new_image_path}")
    if region_coords:
        print(
            f"Region update: ({region_coords[0]}, {region_coords[1]}) {region_coords[2]}x{region_coords[3]}"
        )

    # Load the new image
    try:
        new_image = Image.open(new_image_path)
        print(f"Successfully loaded new image: {new_image_path}")
    except Exception as e:
        print(f"Error loading new image: {e}")
        sys.exit(1)

    # Initialize e-paper display
    try:
        from waveshare_epd.epd7in5b_V2 import EPD

        print("Initializing e-paper display...")
        epd = EPD()

        if region_coords:
            # Region update mode
            print("Region update mode - using partial update initialization")
            if epd.init_part() == 0:
                print("EPD initialized successfully for partial updates")
            else:
                print("Failed to initialize EPD")
                sys.exit(1)

            # Update the specific region
            x, y, width, height = region_coords
            success = update_single_region(epd, new_image, x, y, width, height)

            if success:
                print("Region update completed successfully")
            else:
                print("Region update failed")
                sys.exit(1)

        else:
            # Full image update mode
            # Prepare image for e-paper
            new_epd_image = prepare_image_for_epd(new_image)

            # Use fast initialization for full image updates
            print("Full image - using fast initialization")
            if epd.init_Fast() == 0:
                print("EPD initialized successfully with fast mode")
            else:
                print("Failed to initialize EPD")
                sys.exit(1)

            # Display full image
            print("Displaying full image")
            buffer = epd.getbuffer(new_epd_image)
            # Create a blank red buffer (no red content) - same as counter example
            red_buffer = [0x00] * (int(EPD_WIDTH / 8) * EPD_HEIGHT)
            epd.display(buffer, red_buffer)
            print("Full image displayed successfully")

        # Keep display awake for faster subsequent updates
        print("Update completed - display remains active")

    except Exception as e:
        print(f"Error with e-paper: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
