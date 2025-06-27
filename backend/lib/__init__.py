# E-Paper Display Library
# This package provides modular display implementations for e-paper displays

__version__ = "1.0.0"
__author__ = "Al Shahed"

# Import main classes for easier access
from .display_interface import DisplayInterface
from .display_factory import DisplayFactory
from .hardware_display import HardwareDisplay
from .simulation_display import SimulationDisplay

__all__ = ["DisplayInterface", "DisplayFactory", "HardwareDisplay", "SimulationDisplay"]
