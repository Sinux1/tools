#!/usr/bin/env python3
"""!
@brief Main execution module for MacroHunter
@file main.py
"""

import sys
import logging
from pathlib import Path
from collections.abc import Sequence
from .version import FEATURES
from .cli import ArgumentParser, CommandLineArgs
from .hunter import MacroHunter

if FEATURES.enhanced_type_checks:
    from typing import NoReturn
else:
    from typing import Type, Union, List

def handle_fatal_error(error: Exception, verbose: bool = False) -> NoReturn:
    """!
    @brief Handle fatal errors with appropriate logging and exit
    
    @param error The exception that occurred
    @param verbose Whether to show detailed error information
    """
    logger = logging.getLogger("MacroHunter")
    
    if FEATURES.enhanced_error_groups:
        # Python 3.11+ enhanced error handling
        match error:
            case KeyboardInterrupt():
                logger.error("Scan cancelled by user")
            case FileNotFoundError() | PermissionError() as e:
                logger.error(f"File system error: {str(e)}")
            case _:
                logger.error(f"Fatal error: {str(error)}")
    else:
        # Python 3.9+ basic error handling
        if isinstance(error, KeyboardInterrupt):
            logger.error("Scan cancelled by user")
        elif isinstance(error, (FileNotFoundError, PermissionError)):
            logger.error(f"File system error: {str(error)}")
        else:
            logger.error(f"Fatal error: {str(error)}")

    if verbose:
        if FEATURES.improved_traceback:
            # Python 3.11+ improved traceback
            import traceback
            logger.debug("Detailed error information:", exc_info=True)
            traceback.print_exception(error)
        else:
            # Python 3.9+ basic traceback
            import traceback
            logger.debug(traceback.format_exc())
    
    sys.exit(1)

def collect_files(directory: Path, extensions: Sequence[str]) -> list[Path]:
    """!
    @brief Collect all files with supported extensions from directory
    
    @param directory Directory to scan
    @param extensions List of supported file extensions
    @return List of paths to process
    """
    files: list[Path] = []
    
    try:
        for ext in extensions:
            if FEATURES.enhanced_type_checks:
                # Python 3.10+ path handling
                files.extend(sorted(directory.glob(f"**/*{ext}")))
            else:
                # Python 3.9 compatibility
                files.extend(sorted(Path(directory).glob(f"**/*{ext}")))
    except Exception as e:
        logging.getLogger("MacroHunter").error(f"Error collecting files: {str(e)}")
        raise
        
    return files

def run_macro_hunter(args: CommandLineArgs) -> int:
    """!
    @brief Execute macro hunting operations based on provided arguments
    
    @param args Validated command line arguments
    @return int Exit code (0 for success, 1 for failure)
    """
    hunter = MacroHunter()
    
    try:
        # Configure verbose logging if requested
        if args.verbose:
            hunter.logger.setLevel(logging.DEBUG)
            hunter.logger.debug("Verbose logging enabled")
            if FEATURES.enhanced_logging:
                hunter.logger.debug(f"Using enhanced logging features")
        
        # Handle input path validation
        if args.input_file:
            if not hunter.validate_input_path(args.input_file, is_file=True):
                return 1
            input_path = hunter.normalize_path(args.input_file)
            hunter.logger.info(f"Scanning file: {input_path}")
        else:
            input_path = hunter.normalize_path(args.input_directory)
            if not hunter.validate_input_path(input_path, is_file=False):
                return 1
            hunter.logger.info(f"Scanning directory: {input_path}")
            
        # Setup output directory
        if not hunter.create_directory(args.output_directory):
            return 1
        output_dir = hunter.normalize_path(args.output_directory)
            
        # Log environment information in debug mode
        hunter.logger.debug(f"Operating System: {hunter.system}")
        hunter.logger.debug(f"Results directory: {output_dir}")
        
        # Process input based on type
        if args.input_file:
            if not hunter.process_file(input_path, output_dir):
                hunter.logger.error("File processing failed")
                return 1
        else:
            # Collect and process files
            try:
                files_to_process = collect_files(input_path, hunter.supported_extensions)
                
                if not files_to_process:
                    hunter.logger.warning("No supported files found to process")
                    return 0
                    
                hunter.logger.info(f"Processing {len(files_to_process)} files...")
                batch_results = hunter.batch_process(files_to_process)
                
                if not hunter.generate_report(batch_results, output_dir):
                    hunter.logger.error("Report generation failed")
                    return 1
                    
            except Exception as e:
                hunter.logger.error(f"Error during batch processing: {str(e)}")
                return 1
            
        hunter.logger.info("Processing completed successfully")
                
    except KeyboardInterrupt:
        handle_fatal_error(KeyboardInterrupt(), args.verbose)
    except Exception as e:
        handle_fatal_error(e, args.verbose)
    
    return 0

def main() -> int:
    """!
    @brief Main entry point for MacroHunter.
    
    @return int Exit code (0 for success, 1 for failure)
    """
    try:
        arg_parser = ArgumentParser()
        args = arg_parser.parse_args()
        return run_macro_hunter(args)
        
    except Exception as e:
        print(f"Error during startup: {str(e)}", file=sys.stderr)
        if FEATURES.improved_traceback:
            import traceback
            traceback.print_exception(e)
        return 1

if __name__ == "__main__":
    """!
    @brief MacroHunter script entry point.
    """
    sys.exit(main())
