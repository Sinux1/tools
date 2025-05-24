#!/usr/bin/env python3
"""!
@brief Version checking and feature flags for MacroHunter
@file version.py
"""

import sys
from typing import NamedTuple

class FeatureFlags(NamedTuple):
    """!
    @brief Feature flags based on Python version and actual feature availability
    """
    enhanced_logging: bool
    improved_traceback: bool
    enhanced_type_checks: bool
    tomllib_available: bool
    enhanced_error_groups: bool

def check_feature_availability() -> FeatureFlags:
    """Check actual feature availability rather than just version"""
    
    # Initialize all flags
    enhanced_logging = False
    improved_traceback = False
    enhanced_type_checks = False
    tomllib_available = False
    enhanced_error_groups = False

    # Test enhanced logging
    try:
        import logging
        enhanced_logging = hasattr(logging, 'getLevelNamesMapping')
    except ImportError:
        pass

    # Test traceback improvements
    try:
        import traceback
        improved_traceback = hasattr(traceback, 'format_exception_only')
    except ImportError:
        pass

    # Test type checking
    try:
        from typing import Union
        enhanced_type_checks = hasattr(Union, '__or__')
    except ImportError:
        pass

    # Test tomllib
    try:
        import tomllib
        tomllib_available = True
    except ImportError:
        try:
            import tomli
            tomllib_available = True
        except ImportError:
            pass

    # Test error groups
    try:
        code = """
try:
    exc = ValueError("test")
    raise ExceptionGroup("test group", [exc])
except (NameError, TypeError, ValueError):
    pass
except ExceptionGroup:
    pass
"""
        exec(code)
        enhanced_error_groups = True
    except (SyntaxError, ValueError):
        enhanced_error_groups = False

    return FeatureFlags(
        enhanced_logging=enhanced_logging,
        improved_traceback=improved_traceback,
        enhanced_type_checks=enhanced_type_checks,
        tomllib_available=tomllib_available,
        enhanced_error_groups=enhanced_error_groups
    )

def check_version() -> None:
    """!
    @brief Verify Python version compatibility
    
    @raises RuntimeError if Python version is < 3.9
    """
    if sys.version_info < (3, 9):
        raise RuntimeError(
            "MacroHunter requires Python 3.9 or higher. "
            f"You are using Python {sys.version_info.major}.{sys.version_info.minor}"
        )

# Initialize feature flags based on actual availability
FEATURES = check_feature_availability()
