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
        # The region_image is already the cropped region, not the full e-paper image
        # So we don't need to extract a region from it - we use it directly

        # Calculate the region boundaries on the e-paper display
        x_min, y_min = x, y
        x_max, y_max = x + width, y + height

        # Ensure all values are integers
        x_min = int(x_min)
        y_min = int(y_min)
        x_max = int(x_max)
        y_max = int(y_max)

        # Store original region size
        original_width = x_max - x_min
        original_height = y_max - y_min

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
                x_max = x_max // 8 * 8 + 8

        # Calculate aligned region size
        aligned_width = x_max - x_min
        aligned_height = y_max - y_min

        print(f"Original region: ({x},{y}) {width}x{height}")
        print(
            f"Aligned region: ({x_min},{y_min}) to ({x_max},{y_max}) = {aligned_width}x{aligned_height}"
        )

        # The region_image should already be the correct size, but let's verify
        if region_image.size != (original_width, original_height):
            print(
                f"WARNING: Region image size {region_image.size} doesn't match expected size ({original_width}, {original_height})"
            )
            region_image = region_image.resize(
                (original_width, original_height), Image.Resampling.LANCZOS
            )

        # Convert to 1-bit (black and white)
        if region_image.mode != "1":
            region_image = region_image.convert("1")

        # Create a white background image of the aligned region size
        aligned_image = Image.new("1", (aligned_width, aligned_height), 1)  # 1 = white

        # Calculate offset to center the region image within the aligned area
        offset_x = (aligned_width - original_width) // 2
        offset_y = (aligned_height - original_height) // 2

        print(f"Image offset: ({offset_x}, {offset_y})")
        print(f"Region image size: {region_image.size}")
        print(f"Aligned image size: {aligned_image.size}")

        # Paste the region image onto the aligned background
        aligned_image.paste(region_image, (offset_x, offset_y))

        # Calculate buffer size for the aligned region
        width_bytes = aligned_width // 8
        if aligned_width % 8 != 0:
            width_bytes += 1

        print(f"Buffer size: {width_bytes} bytes x {aligned_height} rows")

        # First, clear the region to black
        black_buffer = bytearray([0x00] * width_bytes * aligned_height)
        print(f"Clearing region to black...")
        epd.display_Partial(black_buffer, x_min, y_min, x_max, y_max)

        # Second, clear the region to white
        white_buffer = bytearray([0xFF] * width_bytes * aligned_height)
        print(f"Clearing region to white...")
        epd.display_Partial(white_buffer, x_min, y_min, x_max, y_max)

        # Convert aligned image to buffer
        buffer = bytearray(aligned_image.tobytes("raw"))

        # Verify buffer size
        expected_buffer_size = width_bytes * aligned_height
        actual_buffer_size = len(buffer)
        print(
            f"Buffer verification: expected {expected_buffer_size} bytes, got {actual_buffer_size} bytes"
        )

        if actual_buffer_size != expected_buffer_size:
            print(f"WARNING: Buffer size mismatch! This may cause display issues.")
            # Adjust buffer size if needed
            if actual_buffer_size > expected_buffer_size:
                buffer = buffer[:expected_buffer_size]
            else:
                buffer.extend([0xFF] * (expected_buffer_size - actual_buffer_size))

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
