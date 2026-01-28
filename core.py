"""
Core module for Hades save backup tool - backward compatibility layer.

This file maintains backward compatibility by re-exporting all functions
from the refactored modular structure.
"""

# Import all constants and functions from the new modular structure
from .core import *  # noqa: F401,F403
