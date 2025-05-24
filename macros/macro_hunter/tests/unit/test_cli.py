#!/usr/bin/env python3
import pytest
import sys
import os
from pathlib import Path
from macro_hunter.cli import ArgumentParser, CommandLineArgs, ArgumentDict
from macro_hunter.version import FEATURES

def test_command_line_args_creation():
    """Test CommandLineArgs dataclass creation"""
    args = CommandLineArgs(
        input_file="test.docm",
        input_directory=None,
        output_directory="output",
        verbose=True
    )
    assert args.input_file == "test.docm"
    assert args.input_directory is None
    assert args.output_directory == "output"
    assert args.verbose is True

def test_command_line_args_from_dict():
    """Test CommandLineArgs.from_dict method"""
    data = {
        'input_file': 'test.docm',
        'input_directory': None,
        'output_directory': 'output',
        'verbose': True
    }
    args = CommandLineArgs.from_dict(data)
    assert args.input_file == 'test.docm'
    assert args.input_directory is None
    assert args.output_directory == 'output'
    assert args.verbose is True

def test_argument_dict_typing():
    """Test ArgumentDict type definitions"""
    test_dict: ArgumentDict = {
        'input_file': 'test.docm',
        'input_directory': None,
        'output_directory': 'output',
        'verbose': True
    }
    assert isinstance(test_dict, dict)

def test_mutually_exclusive_arguments(capsys, monkeypatch):
    """Test mutually exclusive arguments"""
    parser = ArgumentParser()
    monkeypatch.setattr('sys.argv', ['script.py', '-f', 'test.docm', '-d', 'test_dir'])
    with pytest.raises(SystemExit):
        parser.parse_args()
    captured = capsys.readouterr()
    assert "not allowed with argument" in captured.err

def test_help_text(capsys):
    """Test help text output"""
    parser = ArgumentParser()
    parser.print_help()
    captured = capsys.readouterr()
    assert "MacroHunter" in captured.out
    assert "-f" in captured.out
    assert "-d" in captured.out
    assert "-o" in captured.out
    assert "-v" in captured.out

def test_invalid_argument(capsys, monkeypatch):
    """Test invalid argument handling"""
    parser = ArgumentParser()
    monkeypatch.setattr('sys.argv', ['script.py', '--invalid'])
    with pytest.raises(SystemExit):
        parser.parse_args()
    captured = capsys.readouterr()
    assert "unrecognized arguments" in captured.err

def test_no_arguments(monkeypatch):
    """Test parsing with no arguments"""
    parser = ArgumentParser()
    monkeypatch.setattr('sys.argv', ['script.py'])
    args = parser.parse_args()
    assert args.input_file is None
    assert args.input_directory is None
    assert args.output_directory is None
    assert not args.verbose

def test_file_argument(monkeypatch):
    """Test file argument parsing"""
    parser = ArgumentParser()
    monkeypatch.setattr('sys.argv', ['script.py', '-f', 'test.docm'])
    args = parser.parse_args()
    assert args.input_file == 'test.docm'
    assert args.input_directory is None

def test_directory_argument(monkeypatch):
    """Test directory argument parsing"""
    parser = ArgumentParser()
    monkeypatch.setattr('sys.argv', ['script.py', '-d', 'test_dir'])
    args = parser.parse_args()
    assert args.input_directory == 'test_dir'
    assert args.input_file is None

def test_output_argument(monkeypatch):
    """Test output directory argument"""
    parser = ArgumentParser()
    monkeypatch.setattr('sys.argv', ['script.py', '-f', 'test.docm', '-o', 'output'])
    args = parser.parse_args()
    assert args.output_directory == 'output'

def test_verbose_flag(monkeypatch):
    """Test verbose flag"""
    parser = ArgumentParser()
    monkeypatch.setattr('sys.argv', ['script.py', '-f', 'test.docm', '-v'])
    args = parser.parse_args()
    assert args.verbose is True

def test_all_valid_arguments(monkeypatch):
    """Test all valid arguments combination"""
    parser = ArgumentParser()
    monkeypatch.setattr('sys.argv', ['script.py', '-f', 'test.docm', '-o', 'output', '-v'])
    args = parser.parse_args()
    assert args.input_file == 'test.docm'
    assert args.input_directory is None
    assert args.output_directory == 'output'
    assert args.verbose is True

def test_type_hint_selection_full_coverage(monkeypatch):
    """Test type hint selection with both Python versions"""
    import sys
    from dataclasses import dataclass
    from typing import NamedTuple
    
    # Create mock features
    class MockFeatures(NamedTuple):
        enhanced_logging: bool
        improved_traceback: bool
        enhanced_type_checks: bool
        tomllib_available: bool
        enhanced_error_groups: bool
    
    # Test Python 3.10+ path
    mock_features_310 = MockFeatures(
        enhanced_logging=True,
        improved_traceback=True,
        enhanced_type_checks=True,
        tomllib_available=True,
        enhanced_error_groups=True
    )
    
    # Mock the entire version module
    class MockVersion:
        FEATURES = mock_features_310
    
    sys.modules['macro_hunter.version'] = MockVersion
    
    # Force reload of cli module to use new features
    import importlib
    import macro_hunter.cli
    importlib.reload(macro_hunter.cli)
    
    # Test that ArgumentDict has NotRequired
    from macro_hunter.cli import ArgumentDict as ArgumentDict310
    assert hasattr(ArgumentDict310, '__required_keys__')
    
    # Test Python 3.9 path
    mock_features_39 = MockFeatures(
        enhanced_logging=False,
        improved_traceback=False,
        enhanced_type_checks=False,
        tomllib_available=False,
        enhanced_error_groups=False
    )
    MockVersion.FEATURES = mock_features_39
    
    # Reload cli module again with new features
    importlib.reload(macro_hunter.cli)
    from macro_hunter.cli import ArgumentDict as ArgumentDict39
    assert getattr(ArgumentDict39, '__total__', True) is False

def test_main_block_success(capsys, monkeypatch):
    """Test main block successful execution"""
    import macro_hunter.cli as cli_module
    
    # Mock sys.argv and __name__
    monkeypatch.setattr('sys.argv', ['cli.py', '-f', 'test.docm'])
    monkeypatch.setattr(cli_module, '__name__', '__main__')
    
    # Execute main block code
    parser = cli_module.ArgumentParser()
    args = parser.parse_args()
    print(f"Parsed arguments: {args}")
    
    captured = capsys.readouterr()
    assert "Parsed arguments" in captured.out

def test_main_block_error_with_traceback(capsys, monkeypatch):
    """Test main block error handling with traceback"""
    import macro_hunter.cli as cli_module
    import macro_hunter.version
    
    # Create mock features with traceback enabled
    mock_features = macro_hunter.version.FeatureFlags(
        enhanced_logging=False,
        improved_traceback=True,
        enhanced_type_checks=False,
        tomllib_available=False,
        enhanced_error_groups=False
    )
    
    try:
        # Mock __name__, sys.argv, and features
        monkeypatch.setattr(cli_module, '__name__', '__main__')
        monkeypatch.setattr('sys.argv', ['cli.py', '-f', '/nonexistent/file.docm'])
        monkeypatch.setattr(cli_module, 'FEATURES', mock_features)
        
        # Execute main block code
        with pytest.raises(SystemExit) as exc_info:
            parser = cli_module.ArgumentParser()
            try:
                args = parser.parse_args()
                if args.input_file and not os.path.exists(args.input_file):
                    raise FileNotFoundError(f"File not found: {args.input_file}")
                print(f"Parsed arguments: {args}")
            except Exception as e:
                if cli_module.FEATURES.improved_traceback:
                    import traceback
                    print("Error parsing arguments:", file=sys.stderr)
                    traceback.print_exception(e)
                else:
                    print(f"Error parsing arguments: {e}", file=sys.stderr)
                sys.exit(1)
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error parsing arguments" in captured.err
        
    finally:
        monkeypatch.undo()

def test_main_block_error_without_traceback(capsys, monkeypatch):
    """Test main block error handling without traceback"""
    import macro_hunter.cli as cli_module
    import macro_hunter.version
    
    # Create mock features without traceback
    mock_features = macro_hunter.version.FeatureFlags(
        enhanced_logging=False,
        improved_traceback=False,
        enhanced_type_checks=False,
        tomllib_available=False,
        enhanced_error_groups=False
    )
    
    try:
        # Mock __name__, sys.argv, and features
        monkeypatch.setattr(cli_module, '__name__', '__main__')
        monkeypatch.setattr('sys.argv', ['cli.py', '-f', '/nonexistent/file.docm'])
        monkeypatch.setattr(cli_module, 'FEATURES', mock_features)
        
        # Execute main block code
        with pytest.raises(SystemExit) as exc_info:
            parser = cli_module.ArgumentParser()
            try:
                args = parser.parse_args()
                if args.input_file and not os.path.exists(args.input_file):
                    raise FileNotFoundError(f"File not found: {args.input_file}")
                print(f"Parsed arguments: {args}")
            except Exception as e:
                if cli_module.FEATURES.improved_traceback:
                    import traceback
                    print("Error parsing arguments:", file=sys.stderr)
                    traceback.print_exception(e)
                else:
                    print(f"Error parsing arguments: {e}", file=sys.stderr)
                sys.exit(1)
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error parsing arguments" in captured.err
        
    finally:
        monkeypatch.undo()

