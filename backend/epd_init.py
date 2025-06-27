#!/usr/bin/env python3

import sys
import os

# Add the lib directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))


def main():
    """Initialize the e-paper display"""
    try:
        from waveshare_epd.epd7in5b_V2 import EPD

        print("Initializing e-paper display...")
        epd = EPD()

        # Initialize for partial updates (like the counter script)
        if epd.init_part() == 0:
            print("EPD initialized successfully for partial updates")
            epd.Clear()
            print("Display cleared successfully")
            print("EPD initialization completed successfully")
        else:
            print("Failed to initialize EPD")
            sys.exit(1)

    except Exception as e:
        print(f"Error initializing EPD: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
