#!/usr/bin/env python3
"""!
@brief Command line interface handling for MacroHunter
@file cli.py
"""

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from .version import FEATURES

# Use modern type hints if available
if FEATURES.enhanced_type_checks:
    # Python 3.10+
    from typing import NotRequired, TypedDict
    class ArgumentDict(TypedDict):
        input_file: NotRequired[str | None]
        input_directory: NotRequired[str | None]
        output_directory: NotRequired[str | None]
        verbose: bool
else:
    # Python 3.9 compatibility
    from typing import TypedDict, Optional
    class ArgumentDict(TypedDict, total=False):
        input_file: Optional[str]
        input_directory: Optional[str]
        output_directory: Optional[str]
        verbose: bool

@dataclass
class CommandLineArgs:
    """!
    @brief Data class for storing parsed command line arguments
    
    Provides a clean, typed interface for accessing command line arguments
    throughout the application.
    """
    input_file: str | None
    input_directory: str | None
    output_directory: str | None
    verbose: bool

    @classmethod
    def from_dict(cls, data: ArgumentDict) -> 'CommandLineArgs':
        """!
        @brief Create CommandLineArgs from a dictionary
        
        @param data Dictionary containing argument values
        @return CommandLineArgs instance
        """
        return cls(
            input_file=data.get('input_file'),
            input_directory=data.get('input_directory'),
            output_directory=data.get('output_directory'),
            verbose=data.get('verbose', False)
        )

class ArgumentParser:
    """!
    @brief Handles all command line argument parsing and validation
    
    Provides a clean interface for setting up and parsing command line arguments
    while keeping the logic separate from the main macro hunting functionality.
    """
    
    def __init__(self):
        """!
        @brief Initialize the argument parser with all needed arguments
        """
        self.parser = argparse.ArgumentParser(
            description='MacroHunter - Your towel in the galaxy of suspicious macros',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        self._setup_arguments()

    def _setup_arguments(self) -> None:
        """!
        @brief Configure all command line arguments
        
        Sets up the mutually exclusive input group and all other arguments.
        Input file and directory are mutually exclusive, output defaults to
        current directory if not specified.
        """
        # Create mutually exclusive group for input options
        input_group = self.parser.add_mutually_exclusive_group()
        
        input_group.add_argument(
            '-f', '--file',
            help='Input file to scan (mutually exclusive with -d)',
            type=str,
            default=None
        )
        
        input_group.add_argument(
            '-d', '--directory',
            help='Input directory to scan (mutually exclusive with -f)',
            type=str,
            default=None
        )
        
        self.parser.add_argument(
            '-o', '--output',
            help='Output directory for results (default: current directory)',
            type=str,
            default=None
        )
        
        self.parser.add_argument(
            '-v', '--verbose',
            help='Enable verbose output',
            action='store_true'
        )

    def parse_args(self) -> CommandLineArgs:
        """!
        @brief Parse and validate command line arguments
        
        Converts raw argparse namespace into a typed CommandLineArgs instance
        for better type safety and clarity throughout the application.
        
        @return CommandLineArgs Parsed and validated arguments
        @throws ArgumentError If arguments are invalid or conflicting
        """
        args = self.parser.parse_args()
        
        # Convert to dictionary with proper typing based on Python version
        args_dict: ArgumentDict = {
            'input_file': args.file,
            'input_directory': args.directory,
            'output_directory': args.output,
            'verbose': args.verbose
        }
        
        return CommandLineArgs.from_dict(args_dict)

    def print_help(self) -> None:
        """!
        @brief Print help message
        """
        self.parser.print_help()

if __name__ == '__main__':
    """!
    @brief CLI module self-test
    """
    parser = ArgumentParser()
    try:
        args = parser.parse_args()
        print(f"Parsed arguments: {args}")
    except Exception as e:
        if FEATURES.improved_traceback:
            import traceback
            print("Error parsing arguments:", file=sys.stderr)
            traceback.print_exception(e)
        else:
            print(f"Error parsing arguments: {e}", file=sys.stderr)
        sys.exit(1)
