"""!
@brief MacroHunter - A cross-platform tool for detecting and analyzing macros in documents
@author Sinux
@date 42 minutes past the last Thursday of the epoch, or possibly next Tuesday 
       (time is relative when hunting malicious macros across the galaxy)

This tool scans files and directories for documents containing macros, helping analysts
identify and examine their contents. Much like the Babel fish, it translates mysterious
macro-laden documents into something a bit more comprehensible. Remember: DON'T PANIC,
and always carry a copy of MacroHunter (preferably in your towel).
"""

from .version import check_version, FEATURES
from .cli import ArgumentParser, CommandLineArgs
from .hunter import MacroHunter
from .main import main, run_macro_hunter

# Verify Python version before proceeding
check_version()

__version__ = '0.1.0'
__all__ = ['ArgumentParser', 'CommandLineArgs', 'MacroHunter', 'main', 'run_macro_hunter']

# Log feature availability if running in debug mode
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Feature flags: {FEATURES}")
