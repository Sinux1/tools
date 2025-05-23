#!/usr/bin/env python3
"""!
@brief MacroHunter - A cross-platform tool for detecting and analyzing macros in documents
@file macro_hunter.py
@author Sinux
@date 42 minutes past the last Thursday of the epoch, or possibly next Tuesday 
       (time is relative when hunting malicious macros across the galaxy)

This tool scans files and directories for documents containing macros, helping analysts
identify and examine their contents. Much like the Babel fish, it translates mysterious
macro-laden documents into something a bit more comprehensible. Remember: DON'T PANIC,
and always carry a copy of MacroHunter (preferably in your towel).
"""

import argparse
import sys
import os
from pathlib import Path
import platform
import logging
from typing import Union

class MacroHunter:
    """!
    @brief Main class for hunting and analyzing macros in documents.
    """

    def __init__(self):
        """!
        @brief Initialize the MacroHunter instance.
        """
        self.system = platform.system()
        self.setup_logging()
        self.supported_extensions = ['.doc', '.docm', '.xls', '.xlsm', '.ppt', '.pptm']
        self.current_dir = Path.cwd()

    def setup_logging(self) -> None:
        """!
        @brief Configure logging system for macro hunting operations.
        """
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger("MacroHunter")

    def normalize_path(self, path: Union[str, Path, None]) -> Path:
        """!
        @brief Normalize document or directory paths for consistent handling.
        
        @param path Path to normalize, or None to use current directory
        @return Path Normalized absolute path
        @throws Exception If path cannot be normalized
        """
        try:
            if path is None:
                return self.current_dir
            return Path(path).resolve()
        except Exception as e:
            self.logger.error(f"Path normalization error: {str(e)}")
            raise

    def validate_input_path(self, input_path: Union[str, Path, None], is_file: bool = False) -> bool:
        """!
        @brief Validate that target scan path exists and is accessible.
        
        @param input_path Path to validate, or None for current directory
        @param is_file Whether the path should be a file (True) or directory (False)
        @return bool True if path is valid and accessible
        """
        try:
            path = self.normalize_path(input_path)
            if not path.exists():
                self.logger.error(f"Path does not exist: {path}")
                return False
            if not os.access(path, os.R_OK):
                self.logger.error(f"Path is not readable: {path}")
                return False
            if is_file and not path.is_file():
                self.logger.error(f"Path is not a file: {path}")
                return False
            if not is_file and not path.is_dir():
                self.logger.error(f"Path is not a directory: {path}")
                return False
            return True
        except Exception as e:
            self.logger.error(f"Input validation error: {str(e)}")
            return False

    def create_directory(self, directory_path: Union[str, Path, None]) -> bool:
        """!
        @brief Create output directory for scan results and extracted macros.
        
        @param directory_path Path where results will be stored, or None for current directory
        @return bool True if directory was created/exists and is writable
        """
        try:
            dir_path = self.normalize_path(directory_path)
            if directory_path is not None:  # Only create if not using current directory
                dir_path.mkdir(parents=True, exist_ok=True)
            
            if not os.access(dir_path, os.W_OK):
                self.logger.error(f"Results directory is not writable: {dir_path}")
                return False
                
            self.logger.info(f"Using results directory: {dir_path}")
            return True
            
        except PermissionError as e:
            self.logger.error(f"Permission denied creating results directory {directory_path}: {str(e)}")
            return False
        except OSError as e:
            self.logger.error(f"OS error creating results directory {directory_path}: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error creating results directory {directory_path}: {str(e)}")
            return False

def main() -> int:
    """!
    @brief Main entry point for MacroHunter.
    """
    hunter = MacroHunter()
    
    parser = argparse.ArgumentParser(
        description='MacroHunter - Your towel in the galaxy of suspicious macros'
    )
    
    # Create mutually exclusive group for input file/directory
    input_group = parser.add_mutually_exclusive_group()
    
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
    
    parser.add_argument(
        '-o', '--output',
        help='Output directory for results (default: current directory)',
        type=str,
        default=None
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    try:
        args = parser.parse_args()
        
        if args.verbose:
            hunter.logger.setLevel(logging.DEBUG)
        
        # Validate input path (file or directory)
        if args.file:
            if not hunter.validate_input_path(args.file, is_file=True):
                return 1
            input_path = hunter.normalize_path(args.file)
            hunter.logger.info(f"Scanning file: {input_path}")
        else:
            input_path = hunter.normalize_path(args.directory)  # None defaults to current dir
            if not hunter.validate_input_path(input_path, is_file=False):
                return 1
            hunter.logger.info(f"Scanning directory: {input_path}")
            
        # Setup output directory
        if not hunter.create_directory(args.output):
            return 1
        output_dir = hunter.normalize_path(args.output)
            
        hunter.logger.debug(f"Operating System: {hunter.system}")
        hunter.logger.debug(f"Results directory: {output_dir}")
        
        # TODO: Implement macro scanning and analysis logic
        
    except KeyboardInterrupt:
        hunter.logger.error("Scan cancelled by user")
        return 1
    except Exception as e:
        hunter.logger.error(f"Error: {str(e)}")
        if args.verbose:
            import traceback
            hunter.logger.debug(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    """!
    @brief MacroHunter entry point.
    """
    sys.exit(main())
