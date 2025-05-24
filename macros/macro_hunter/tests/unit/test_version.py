#!/usr/bin/env python3
import pytest
import sys
import logging
import traceback
from typing import Union
from macro_hunter.version import (
    check_version,
    check_feature_availability,
    FeatureFlags,
    FEATURES
)

# Store original import
original_import = __import__

class MockVersionInfo:
    """Mock sys.version_info for testing"""
    def __init__(self, major, minor):
        self.major = major
        self.minor = minor
        
    def __lt__(self, other):
        if isinstance(other, tuple):
            return (self.major, self.minor) < other[:2]
        return NotImplemented
        
    def __ge__(self, other):
        if isinstance(other, tuple):
            return (self.major, self.minor) >= other[:2]
        return NotImplemented

def safe_import(name, *args, **kwargs):
    """Safe import mock that prevents recursion"""
    if name == 'tomllib':
        raise ImportError("Mock tomllib import failure")
    if name == 'tomli':
        return type('MockTomli', (), {})()
    if name == 'logging':
        raise ImportError("Mock logging import failure")
    return original_import(name, *args, **kwargs)

def test_feature_detection_logging_import_error(monkeypatch):
    """Test logging feature detection when import fails"""
    def raise_import_error(*args, **kwargs):
        raise ImportError("Forced import error")
    
    monkeypatch.setattr('builtins.__import__', raise_import_error)
    flags = check_feature_availability()
    assert flags.enhanced_logging == False

def test_feature_detection_traceback_import_error(monkeypatch):
    """Test traceback feature detection when import fails"""
    def selective_import(name, *args, **kwargs):
        if name == 'traceback':
            raise ImportError("Forced traceback import error")
        return original_import(name, *args, **kwargs)
    
    monkeypatch.setattr('builtins.__import__', selective_import)
    flags = check_feature_availability()
    assert flags.improved_traceback == False

def test_feature_detection_typing_import_error(monkeypatch):
    """Test typing feature detection when import fails"""
    def selective_import(name, *args, **kwargs):
        if name == 'typing':
            raise ImportError("Forced typing import error")
        return original_import(name, *args, **kwargs)
    
    monkeypatch.setattr('builtins.__import__', selective_import)
    flags = check_feature_availability()
    assert flags.enhanced_type_checks == False

def test_feature_detection_error_groups_syntax_error(monkeypatch):
    """Test error groups detection with syntax error"""
    def exec_raising(*args, **kwargs):
        raise SyntaxError("Forced syntax error")
    
    monkeypatch.setattr('builtins.exec', exec_raising)
    flags = check_feature_availability()
    assert flags.enhanced_error_groups == False

def test_feature_detection_error_groups_value_error(monkeypatch):
    """Test error groups detection with value error"""
    def exec_raising(*args, **kwargs):
        raise ValueError("Forced value error")
    
    monkeypatch.setattr('builtins.exec', exec_raising)
    flags = check_feature_availability()
    assert flags.enhanced_error_groups == False

def test_tomllib_import_chain(monkeypatch):
    """Test complete tomllib import chain failure"""
    def selective_import(name, *args, **kwargs):
        if name in ['tomllib', 'tomli']:
            raise ImportError(f"Forced {name} import error")
        return original_import(name, *args, **kwargs)
    
    monkeypatch.setattr('builtins.__import__', selective_import)
    flags = check_feature_availability()
    assert flags.tomllib_available == False

def test_version_check_valid():
    """Test that current Python version passes check"""
    check_version()

def test_version_check_invalid(monkeypatch):
    """Test that old Python versions are rejected"""
    monkeypatch.setattr(sys, 'version_info', MockVersionInfo(3, 8))
    
    with pytest.raises(RuntimeError) as exc_info:
        check_version()
    assert "requires Python 3.9 or higher" in str(exc_info.value)

def test_feature_flags_structure():
    """Test that FeatureFlags contains all expected attributes"""
    flags = FeatureFlags(
        enhanced_logging=True,
        improved_traceback=True,
        enhanced_type_checks=True,
        tomllib_available=True,
        enhanced_error_groups=True
    )
    
    assert hasattr(flags, 'enhanced_logging')
    assert hasattr(flags, 'improved_traceback')
    assert hasattr(flags, 'enhanced_type_checks')
    assert hasattr(flags, 'tomllib_available')
    assert hasattr(flags, 'enhanced_error_groups')

def test_feature_detection_logging(monkeypatch):
    """Test enhanced logging detection"""
    monkeypatch.setattr(logging, 'getLevelNamesMapping', lambda: None)
    flags = check_feature_availability()
    assert flags.enhanced_logging == True

    monkeypatch.delattr(logging, 'getLevelNamesMapping', raising=False)
    flags = check_feature_availability()
    assert flags.enhanced_logging == False

def test_logging_import_failure(monkeypatch):
    """Test behavior when logging module can't be imported"""
    monkeypatch.setattr('builtins.__import__', safe_import)
    flags = check_feature_availability()
    assert flags.enhanced_logging == False

def test_feature_detection_traceback(monkeypatch):
    """Test improved traceback detection"""
    monkeypatch.setattr(traceback, 'format_exception_only', lambda: None)
    flags = check_feature_availability()
    assert flags.improved_traceback == True

    monkeypatch.delattr(traceback, 'format_exception_only', raising=False)
    flags = check_feature_availability()
    assert flags.improved_traceback == False

def test_feature_detection_type_checks(monkeypatch):
    """Test enhanced type checks detection"""
    flags = check_feature_availability()
    assert isinstance(flags.enhanced_type_checks, bool)

def test_feature_detection_tomllib():
    """Test tomllib availability detection"""
    flags = check_feature_availability()
    assert isinstance(flags.tomllib_available, bool)

def test_tomllib_import_fallback(monkeypatch):
    """Test tomllib fallback to tomli"""
    monkeypatch.setattr('builtins.__import__', safe_import)
    flags = check_feature_availability()
    assert flags.tomllib_available == True

def test_feature_detection_error_groups():
    """Test error groups detection"""
    flags = check_feature_availability()
    assert isinstance(flags.enhanced_error_groups, bool)

def test_features_global_variable():
    """Test that FEATURES global variable is properly initialized"""
    assert isinstance(FEATURES, FeatureFlags)
    expected_flags = check_feature_availability()
    assert FEATURES == expected_flags

def test_feature_flags_immutability():
    """Test that FeatureFlags instances are immutable"""
    flags = check_feature_availability()
    with pytest.raises(AttributeError):
        flags.enhanced_logging = False
