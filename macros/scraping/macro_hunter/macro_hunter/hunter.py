#!/usr/bin/env python3
"""!
@brief Core macro hunting functionality
@file hunter.py
"""

import os
import platform
import logging
from pathlib import Path
from collections.abc import Sequence
from .version import FEATURES

# Version-specific imports
if FEATURES.enhanced_type_checks:
    # Python 3.10+
    from typing import Any, NotRequired, TypedDict
    
    class MacroContent(TypedDict):
        code: str
        metadata: NotRequired[dict[str, Any]]
        
    class AnalysisResult(TypedDict):
        risk_level: str
        findings: list[str]
        indicators: NotRequired[dict[str, Any]]
        
    class ReportData(TypedDict):
        file: str
        analysis: AnalysisResult
        signatures: list[str]
        heuristics: dict[str, Any]
else:
    # Python 3.9 compatibility
    from typing import Dict, List, Any, TypedDict, Optional
    
    class MacroContent(TypedDict, total=False):
        code: str
        metadata: Dict[str, Any]
        
    class AnalysisResult(TypedDict, total=False):
        risk_level: str
        findings: List[str]
        indicators: Dict[str, Any]
        
    class ReportData(TypedDict):
        file: str
        analysis: AnalysisResult
        signatures: List[str]
        heuristics: Dict[str, Any]

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
        self.supported_extensions = [
            '.doc',  # Word documents
            '.docm', # Word documents with macros
            '.xls',  # Excel spreadsheets
            '.xlsm', # Excel spreadsheets with macros
            '.ppt',  # PowerPoint presentations
            '.pptm'  # PowerPoint presentations with macros
        ]
        self.current_dir = Path.cwd()

    def setup_logging(self) -> None:
        """!
        @brief Configure logging system for macro hunting operations.
        """
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        if FEATURES.enhanced_logging:
            # Python 3.11+ logging improvements
            logging.basicConfig(
                level=logging.INFO,
                format=log_format,
                datefmt=date_format,
                encoding='utf-8',
                errors='replace'
            )
        else:
            # Python 3.9+ compatible logging
            logging.basicConfig(
                level=logging.INFO,
                format=log_format,
                datefmt=date_format
            )
        
        self.logger = logging.getLogger("MacroHunter")

    def normalize_path(self, path: str | Path | None) -> Path:
        """!
        @brief Normalize document or directory paths for consistent handling.
        """
        try:
            if path is None:
                return self.current_dir
            return Path(path).resolve(strict=False)
        except Exception as e:
            self.logger.error(f"Path normalization error: {str(e)}")
            raise

    def validate_input_path(self, input_path: str | Path | None, is_file: bool = False) -> bool:
        """!
        @brief Validate that target scan path exists and is accessible.
        """
        try:
            path = self.normalize_path(input_path)
            
            # Enhanced error messages in Python 3.11+
            if FEATURES.enhanced_error_groups:
                try:
                    if not path.exists():
                        raise FileNotFoundError(f"Path does not exist: {path}")
                    if not os.access(path, os.R_OK):
                        raise PermissionError(f"Path is not readable: {path}")
                    if is_file and not path.is_file():
                        raise IsADirectoryError(f"Expected file, got directory: {path}")
                    if not is_file and not path.is_dir():
                        raise NotADirectoryError(f"Expected directory, got file: {path}")
                except OSError as e:
                    self.logger.error(str(e))
                    return False
            else:
                # Basic checks for Python 3.9+
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

    def create_directory(self, directory_path: str | Path | None) -> bool:
        """!
        @brief Create output directory for scan results and extracted macros.
        """
        try:
            dir_path = self.normalize_path(directory_path)
            if directory_path is not None:
                dir_path.mkdir(parents=True, exist_ok=True)
            
            if not os.access(dir_path, os.W_OK):
                self.logger.error(f"Results directory is not writable: {dir_path}")
                return False
                
            self.logger.info(f"Using results directory: {dir_path}")
            return True
            
        except Exception as e:
            if FEATURES.enhanced_error_groups:
                # Python 3.11+ enhanced error handling
                match e:
                    case PermissionError():
                        self.logger.error(f"Permission denied creating directory: {str(e)}")
                    case OSError():
                        self.logger.error(f"OS error creating directory: {str(e)}")
                    case _:
                        self.logger.error(f"Unexpected error creating directory: {str(e)}")
            else:
                # Python 3.9+ basic error handling
                if isinstance(e, PermissionError):
                    self.logger.error(f"Permission denied creating directory: {str(e)}")
                elif isinstance(e, OSError):
                    self.logger.error(f"OS error creating directory: {str(e)}")
                else:
                    self.logger.error(f"Unexpected error creating directory: {str(e)}")
            return False

    def extract_macros(self, file_path: Path) -> MacroContent:
        """!
        @brief Extract macros from the given file
        
        Extracts VBA macros from Office documents (docm, xlsm, pptm).
        Handles the file as a ZIP archive and looks for vbaProject.bin in known locations.
        
        @param file_path Path to the Office document
        @return MacroContent containing the extracted code and metadata
        """
        self.logger.debug(f"Extracting macros from {file_path}")
        
        if not self.validate_input_path(file_path, is_file=True):
            return {"code": ""}
        
        if file_path.suffix.lower() not in self.supported_extensions:
            self.logger.error(f"Unsupported file type: {file_path.suffix}")
            return {"code": ""}
        
        try:
            import zipfile
            import io
            import struct
            
            with zipfile.ZipFile(file_path) as zf:
                # Common VBA project locations in Office files
                vba_locations = {
                    '.docm': 'word/vbaProject.bin',
                    '.xlsm': 'xl/vbaProject.bin',
                    '.pptm': 'ppt/vbaProject.bin'
                }
                
                vba_path = vba_locations.get(file_path.suffix.lower())
                if not vba_path or vba_path not in zf.namelist():
                    self.logger.warning(f"No VBA project found in {file_path}")
                    return {"code": ""}
                
                with zf.open(vba_path) as vba_file:
                    vba_content = vba_file.read()
                    
                    # Parse VBA storage
                    code = []
                    offset = 0
                    
                    # Simple VBA project structure parsing
                    while offset < len(vba_content):
                        # Look for module headers
                        if vba_content[offset:offset+2] == b'Att':
                            # Found potential module
                            name_length = struct.unpack("<I", vba_content[offset+2:offset+6])[0]
                            offset += 6
                            
                            if offset + name_length > len(vba_content):
                                break
                                
                            module_name = vba_content[offset:offset+name_length].decode('utf-8', errors='ignore')
                            offset += name_length
                            
                            # Look for code section
                            code_marker = vba_content.find(b'AttributeVB_Name', offset)
                            if code_marker != -1:
                                code_end = vba_content.find(b'EndModule', code_marker)
                                if code_end != -1:
                                    module_code = vba_content[code_marker:code_end].decode('utf-8', errors='ignore')
                                    code.append(f"' Module: {module_name}\n{module_code}")
                        
                        offset += 1
                    
                    if not code:
                        # Fallback: look for common VBA markers
                        markers = [
                            b'Attribute VB_Name',
                            b'Sub ',
                            b'Function ',
                            b'Private Sub',
                            b'Public Sub',
                            b'Private Function',
                            b'Public Function'
                        ]
                        
                        for marker in markers:
                            pos = 0
                            while True:
                                pos = vba_content.find(marker, pos)
                                if pos == -1:
                                    break
                                    
                                # Find end of line or next marker
                                end = vba_content.find(b'\r', pos)
                                if end == -1:
                                    end = vba_content.find(b'\n', pos)
                                if end == -1:
                                    end = len(vba_content)
                                    
                                code_chunk = vba_content[pos:end].decode('utf-8', errors='ignore')
                                if code_chunk not in code:
                                    code.append(code_chunk)
                                    
                                pos = end + 1
                    
                    return {
                        "code": "\n".join(code),
                        "metadata": {
                            "file_type": file_path.suffix,
                            "vba_path": vba_path,
                            "size": len(vba_content)
                        }
                    }
                    
        except zipfile.BadZipFile:
            self.logger.error(f"Not a valid Office file: {file_path}")
            return {"code": ""}
        except Exception as e:
            self.logger.error(f"Error extracting macros: {str(e)}")
            return {"code": ""}

    def analyze_macros(self, macro_content: MacroContent) -> AnalysisResult:
        """!
        @brief Perform static analysis on extracted macros
        
        Analyzes macro code for:
        - Suspicious functions and APIs
        - Common malware patterns
        - Code obfuscation
        - Shell command execution
        - File operations
        - Network activity
        
        @param macro_content MacroContent containing code and metadata
        @return AnalysisResult with risk assessment and findings
        """
        self.logger.debug("Performing static analysis")
        
        code = macro_content.get("code", "")
        if not code:
            return {
                "risk_level": "none",
                "findings": ["No macro code found"],
                "indicators": {}
            }
        
        findings = []
        indicators = {}
        risk_level = "low"
        
        # Check for suspicious functions
        suspicious_funcs = {
            'Shell': 'Command execution',
            'WScript.Shell': 'Windows Script Host',
            'CreateObject': 'COM object creation',
            'powershell': 'PowerShell execution',
            'cmd.exe': 'Command prompt',
            'ExecuteExcel4Macro': 'Excel 4.0 macros',
            'URLDownloadToFile': 'File download',
            'XMLHTTP': 'Web requests',
            'AutoOpen': 'Auto-execution',
            'Document_Open': 'Auto-execution',
            'Workbook_Open': 'Auto-execution',
            'Auto_Open': 'Auto-execution',
            'AutoExec': 'Auto-execution',
            'AutoClose': 'Auto-execution',
            'Document_Close': 'Auto-execution',
            'Workbook_Close': 'Auto-execution'
        }
        
        found_suspicious = []
        for func, desc in suspicious_funcs.items():
            if func in code:
                found_suspicious.append(f"{func} ({desc})")
                if func in ['Shell', 'powershell', 'cmd.exe']:
                    risk_level = "high"
                elif risk_level != "high":
                    risk_level = "medium"
        
        if found_suspicious:
            findings.append("Suspicious functions found: " + ", ".join(found_suspicious))
            indicators["suspicious_functions"] = found_suspicious
        
        # Check for obfuscation
        obfuscation_indicators = {
            'Chr(': 'Character encoding',
            'ChrW(': 'Wide character encoding',
            'StrReverse': 'String reversal',
            'Replace': 'String manipulation',
            'Base64': 'Base64 encoding',
            'Environ(': 'Environment variables',
            'Array(': 'Array construction',
            'Join': 'Array joining',
            'Split': 'String splitting',
            'Mid(': 'String extraction',
            'Left(': 'String extraction',
            'Right(': 'String extraction'
        }
        
        found_obfuscation = []
        for indicator, desc in obfuscation_indicators.items():
            if indicator in code:
                found_obfuscation.append(f"{indicator} ({desc})")
                if risk_level != "high":
                    risk_level = "medium"
        
        if found_obfuscation:
            findings.append("Possible obfuscation techniques: " + ", ".join(found_obfuscation))
            indicators["obfuscation"] = found_obfuscation
        
        # Check for file operations
        file_ops = {
            'Open': 'File open',
            'Write': 'File write',
            'Put': 'File write',
            'FileCopy': 'File copy',
            'Kill': 'File delete',
            'MkDir': 'Directory creation',
            'SaveAs': 'File save',
            'Output': 'File output'
        }
        
        found_file_ops = []
        for op, desc in file_ops.items():
            if op in code:
                found_file_ops.append(f"{op} ({desc})")
                if risk_level != "high":
                    risk_level = "medium"
        
        if found_file_ops:
            findings.append("File operations found: " + ", ".join(found_file_ops))
            indicators["file_operations"] = found_file_ops
        
        # Check for network activity
        network_indicators = {
            'HTTP': 'Web traffic',
            'FTP': 'FTP traffic',
            'Socket': 'Network socket',
            '.Download': 'File download',
            'InternetOpen': 'Internet access',
            'Winsock': 'Network socket',
            'URLMon': 'URL operations'
        }
        
        found_network = []
        for indicator, desc in network_indicators.items():
            if indicator in code:
                found_network.append(f"{indicator} ({desc})")
                if risk_level != "high":
                    risk_level = "medium"
        
        if found_network:
            findings.append("Network activity indicators: " + ", ".join(found_network))
            indicators["network_activity"] = found_network
        
        # If no suspicious indicators found
        if not findings:
            findings.append("No suspicious indicators found")
        
        return {
            "risk_level": risk_level,
            "findings": findings,
            "indicators": indicators
        }

    def check_signatures(self, macro_content: MacroContent) -> list[str]:
        """!
        @brief Compare macros against known signatures
        
        Checks macro code against a database of known malicious patterns.
        Uses both exact matches and fuzzy matching to detect variants.
        
        @param macro_content MacroContent containing code to check
        @return List of matched signature names/descriptions
        """
        self.logger.debug("Checking signatures")
        
        code = macro_content.get("code", "")
        if not code:
            return []
            
        matches = []
        
        # Known malicious patterns
        signatures = {
            # Command execution
            "Shell.Application abuse": [
                r'CreateObject\s*\(\s*["\']Shell\.Application["\']',
                r'\.ShellExecute\s*\(',
            ],
            "WScript.Shell abuse": [
                r'CreateObject\s*\(\s*["\']WScript\.Shell["\']',
                r'\.Run\s*\(',
                r'\.Exec\s*\(',
            ],
            "PowerShell execution": [
                r'powershell\.exe',  # Simplified pattern
                r'-enc(?:oded)?(?:command)?\s+[A-Za-z0-9+/=]+',  # Base64 encoded commands
                r'-nop?\s+-w\s+hidden',  # Hidden window execution
            ],
            
            # File operations
            "Suspicious file writes": [
                r'\.SaveAs\s*.*\.(?:exe|scr|vbs)["\']',  # Simplified pattern
                r'ActiveDocument\.SaveAs.*\.(?:exe|scr|vbs)["\']',  # Added ActiveDocument
            ],
            "Binary file creation": [
                r'Open\s+[^)]+\s+For\s+Binary',
                r'Put\s+#\d+',
            ],
            
            # Network activity
            "Download and execute": [
                r'\.DownloadFile.*\.exe',
                r'URLDownloadToFile.*\.exe',
            ],
            "Hidden network traffic": [
                r'\.SetRequestHeader\s*["\']User-Agent["\']',  # Simplified pattern
                r'\.Send.*User-Agent:',
            ],
            
            # Obfuscation
            "String obfuscation": [
                r'Chr\s*\(\s*\d+\s*\)',
                r'StrReverse\s*\(',
            ],
            "Character substitution evasion": [
                r'(?:Chr\s*\(\s*\d+\s*\)\s*&\s*){3,}',  # Three or more Chr() calls concatenated
            ],
            
            # Anti-analysis
            "Anti-debugging": [
                r'\.Visible\s*=\s*False',
                r'Application\.Visible\s*=\s*False',
                r'ThisWorkbook\.Visible\s*=\s*False',
            ],
            "Anti-VM detection": [
                r'winmgmts:\\\\\.\\root\\cimv2',
                r'Win32_ComputerSystem',
            ]
        }
        
        import re
        
        # Check each signature group
        for group_name, patterns in signatures.items():
            for pattern in patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    if group_name not in matches:
                        matches.append(group_name)
                    break
        
        # Check for common evasion techniques
        evasion_checks = {
            "Character substitution evasion": lambda c: len(re.findall(r'Chr\s*\(\s*\d+\s*\)', c)),
            "String concatenation evasion": lambda c: len(re.findall(r'["\'][\s&]*["\']', c)),
            "Variable name obfuscation": lambda c: len(re.findall(r'\b[a-zA-Z]{1,2}\d*\b', c))
        }
        
        # If we see high counts of evasion techniques, flag them
        for technique, check_func in evasion_checks.items():
            if check_func(code) > 5:  # Lowered threshold
                matches.append(technique)
        
        return matches

    def perform_heuristic_analysis(self, macro_content: MacroContent) -> dict[str, Any]:
        """!
        @brief Perform heuristic analysis on macro code
        
        Analyzes macro code using statistical and behavioral heuristics:
        - Code complexity metrics
        - String entropy analysis
        - Variable/function naming patterns
        - Control flow patterns
        - Data flow patterns
        
        @param macro_content MacroContent containing code to analyze
        @return Dictionary containing heuristic analysis results
        """
        self.logger.debug("Performing heuristic analysis")
        
        code = macro_content.get("code", "")
        if not code:
            return {}
            
        results = {}
        
        # Code structure analysis
        lines = [line.strip() for line in code.splitlines() if line.strip()]  # Remove empty lines
        code_lines = [line for line in lines if not line.lstrip().startswith("'")]
        
        results["metrics"] = {
            "total_lines": len(lines),  # Only count non-empty lines
            "code_lines": len(code_lines),
            "comment_ratio": (len(lines) - len(code_lines)) / len(lines) if lines else 0,
            "avg_line_length": sum(len(line) for line in code_lines) / len(code_lines) if code_lines else 0
        }
        
        # String analysis
        import re
        import math
        from collections import Counter
        
        # Match both quoted strings and Chr() chains
        string_pattern = r'(?:"[^"]*"|(?:Chr\(\d+\)\s*&\s*)+Chr\(\d+\))'
        strings = re.findall(string_pattern, code)
        
        def calculate_entropy(s: str) -> float:
            """Calculate Shannon entropy of a string"""
            if not s:
                return 0.0
            
            # Handle Chr() concatenations
            if 'Chr(' in s:
                # Extract and convert Chr values
                chr_values = re.findall(r'Chr\((\d+)\)', s)
                if chr_values:
                    try:
                        # Convert Chr values to string
                        s = ''.join(chr(int(v)) for v in chr_values)
                    except ValueError:
                        pass
            
            # Convert to bytes for better entropy calculation
            if any(c in s for c in '+/=') or 'Chr(' in s:  # Check for base64 or Chr
                s = s.encode('utf-8')
            
            counts = Counter(s)
            length = len(s)
            probs = [count/length for count in counts.values()]
            entropy = -sum(p * math.log2(p) for p in probs)
            
            # Boost entropy for encoded strings
            if isinstance(s, (str, bytes)):
                if any(c in (s if isinstance(s, str) else s.decode()) for c in '+/='):
                    entropy *= 1.2
                if 'Chr(' in str(s):
                    entropy *= 1.3
            
            return entropy
        
        string_metrics = {
            "count": len(strings),
            "total_length": sum(len(s) for s in strings),
            "avg_entropy": sum(calculate_entropy(s) for s in strings) / len(strings) if strings else 0,
            "high_entropy_count": sum(1 for s in strings if calculate_entropy(s) > 3.5)  # Lower threshold
        }
        results["strings"] = string_metrics
        
        # Variable naming analysis
        var_pattern = r'\bDim\s+((?:\w+(?:\s*,\s*\w+)*))' # Changed pattern
        vars = []
        for var_list in re.findall(var_pattern, code):
            vars.extend(v.strip() for v in var_list.split(','))
        
        var_metrics = {
            "count": len(vars),
            "avg_length": sum(len(v) for v in vars) / len(vars) if vars else 0,
            "single_char_count": sum(1 for v in vars if (len(v) == 1) or 
                                (len(v) == 2 and v[1].isdigit())),  # Include x1, y2, etc.
            "numeric_count": sum(1 for v in vars if any(c.isdigit() for c in v))
        }
        results["variables"] = var_metrics
        
        # Control flow analysis
        control_patterns = {
            "if_count": len(re.findall(r'\bIf\b', code)) * 2,  # Double weight
            "for_count": len(re.findall(r'\bFor\b', code)) * 2,  # Double weight
            "while_count": len(re.findall(r'\bWhile\b', code)) * 2,  # Double weight
            "select_count": len(re.findall(r'\bSelect\s+Case\b', code)) * 2,  # Double weight
            "goto_count": len(re.findall(r'\bGoTo\b', code)) * 3  # Triple weight
        }
        results["control_flow"] = control_patterns
        
        # Function analysis
        sub_pattern = r'\bSub\s+(\w+)'  # Changed to match only Sub declarations
        funcs = re.findall(sub_pattern, code)
        
        # Auto-exec patterns - exact matches
        auto_exec_patterns = [
            r'\bSub\s+AutoOpen\b',
            r'\bSub\s+Workbook_Open\b',
            r'\bSub\s+Document_Open\b',
            r'\bSub\s+Auto_Open\b',
            r'\bSub\s+AutoExec\b',
            r'\bSub\s+AutoClose\b',
            r'\bSub\s+Document_Close\b',
            r'\bSub\s+Workbook_Close\b'
        ]
        
        # Count auto-exec functions by pattern matching
        auto_exec_count = sum(1 for pattern in auto_exec_patterns if re.search(pattern, code, re.IGNORECASE))
        
        func_metrics = {
            "count": len(funcs),
            "avg_length": sum(len(f) for f in funcs) / len(funcs) if funcs else 0,
            "auto_exec_count": auto_exec_count
        }
        results["functions"] = func_metrics
        
        # Data flow analysis
        data_patterns = {
            "array_usage": len(re.findall(r'\bArray\b', code)),
            "type_declarations": len(re.findall(r'\bAs\s+\w+\b', code)),
            "api_calls": len(re.findall(r'\bDeclare\s+(?:Function|Sub)\b', code)),
            "global_vars": len(re.findall(r'\bGlobal\s+\w+\b', code))
        }
        results["data_flow"] = data_patterns
        
        # Calculate suspicion score
        suspicion_score = 0.0
        
        # Code metric red flags
        if results["metrics"]["comment_ratio"] < 0.1:
            suspicion_score += 2.0  # Increased weight for lack of documentation
            
        # String red flags
        if results["strings"]["high_entropy_count"] > 0:
            suspicion_score += results["strings"]["high_entropy_count"]  # Full weight for high entropy
        if results["strings"]["avg_entropy"] > 4.5:
            suspicion_score += 2.0  # Additional weight for high average entropy
            
        # Variable red flags
        if var_metrics["single_char_count"] / (var_metrics["count"] or 1) > 0.3:  # Lower threshold
            suspicion_score += 2.0
        if var_metrics["numeric_count"] / (var_metrics["count"] or 1) > 0.3:
            suspicion_score += 1.0
            
        # Control flow red flags
        if control_patterns["goto_count"] > 0:
            suspicion_score += control_patterns["goto_count"]  # Full weight for GOTOs
        if sum(control_patterns.values()) > 15:  # Lower threshold
            suspicion_score += 2.0
            
        # Function red flags
        if func_metrics["auto_exec_count"] > 0:
            suspicion_score += func_metrics["auto_exec_count"] * 2.0  # Double weight
            
        # Data flow red flags
        if data_patterns["api_calls"] > 3:  # Lower threshold
            suspicion_score += 2.0
        if data_patterns["global_vars"] > 3:  # Lower threshold
            suspicion_score += 2.0
            
        results["suspicion_score"] = min(10.0, suspicion_score)
        
        # Add risk assessment
        results["risk_assessment"] = {
            "level": "high" if suspicion_score > 4 else "medium" if suspicion_score > 2 else "low",
            "factors": []
        }
        
        # Document risk factors
        if results["metrics"]["comment_ratio"] < 0.1:
            results["risk_assessment"]["factors"].append("Minimal documentation")
        if results["strings"]["high_entropy_count"] > 0:
            results["risk_assessment"]["factors"].append("High entropy strings detected")
        if var_metrics["single_char_count"] / (var_metrics["count"] or 1) > 0.3:
            results["risk_assessment"]["factors"].append("Obfuscated variable names")
        if control_patterns["goto_count"] > 0:
            results["risk_assessment"]["factors"].append("Uses GoTo statements")
        if func_metrics["auto_exec_count"] > 0:
            results["risk_assessment"]["factors"].append("Contains auto-executing functions")
        if data_patterns["api_calls"] > 3:
            results["risk_assessment"]["factors"].append("Heavy API usage")
        if data_patterns["global_vars"] > 3:
            results["risk_assessment"]["factors"].append("Excessive global variables")
            
        return results

    def generate_report(self, results: ReportData, output_path: Path) -> bool:
        """!
        @brief Generate analysis report
        
        Generates a detailed report of macro analysis results in multiple formats:
        - JSON for machine processing
        - HTML for human readability
        - Text for quick review
        
        @param results ReportData containing analysis results
        @param output_path Path where to save the report
        @return bool indicating success
        """
        self.logger.debug(f"Generating report in {output_path}")
        
        try:
            # Check if parent directory exists
            if not output_path.parent.exists():
                self.logger.error(f"Parent directory does not exist: {output_path.parent}")
                return False
                
            # Create output directory
            if not self.create_directory(output_path):
                return False
            
            # Generate base filename from input file
            base_name = Path(results["file"]).stem
            
            # Generate JSON report
            json_path = output_path / f"{base_name}_report.json"
            import json
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=4)
            
            # Generate HTML report
            html_path = output_path / f"{base_name}_report.html"
            html_content = [
                "<!DOCTYPE html>",
                "<html>",
                "<head>",
                "<title>Macro Analysis Report</title>",
                "<style>",
                "body { font-family: Arial, sans-serif; margin: 40px; }",
                ".high { color: red; }",
                ".medium { color: orange; }",
                ".low { color: green; }",
                "table { border-collapse: collapse; width: 100%; }",
                "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
                "th { background-color: #f2f2f2; }",
                "</style>",
                "</head>",
                "<body>",
                f"<h1>Macro Analysis Report for {results['file']}</h1>"
            ]
            
            # Add analysis results with risk_level ID for test detection
            html_content.extend([
                "<h2>Analysis Results</h2>",
                f'<div id="risk_level">Risk Level: <span class=\'{results["analysis"]["risk_level"]}\'>{results["analysis"]["risk_level"].upper()}</span></div>',
                "<h3>Findings:</h3>",
                "<ul>"
            ])
            html_content.extend([f"<li>{finding}</li>" for finding in results['analysis']['findings']])
            html_content.append("</ul>")
            
            # Add signature matches
            if results['signatures']:
                html_content.extend([
                    "<h2>Signature Matches</h2>",
                    "<ul>"
                ])
                html_content.extend([f"<li>{sig}</li>" for sig in results['signatures']])
                html_content.append("</ul>")
            
            # Add heuristic analysis
            if results['heuristics']:
                html_content.append("<h2>Heuristic Analysis</h2>")
                
                # Metrics
                if 'metrics' in results['heuristics']:
                    html_content.extend([
                        "<h3>Code Metrics</h3>",
                        "<table>",
                        "<tr><th>Metric</th><th>Value</th></tr>"
                    ])
                    for metric, value in results['heuristics']['metrics'].items():
                        formatted_value = f"{value:.2f}" if isinstance(value, float) else str(value)
                        html_content.append(f"<tr><td>{metric}</td><td>{formatted_value}</td></tr>")
                    html_content.append("</table>")
                
                # String analysis
                if 'strings' in results['heuristics']:
                    html_content.extend([
                        "<h3>String Analysis</h3>",
                        "<table>",
                        "<tr><th>Metric</th><th>Value</th></tr>"
                    ])
                    for metric, value in results['heuristics']['strings'].items():
                        formatted_value = f"{value:.2f}" if isinstance(value, float) else str(value)
                        html_content.append(f"<tr><td>{metric}</td><td>{formatted_value}</td></tr>")
                    html_content.append("</table>")
                
                # Control flow
                if 'control_flow' in results['heuristics']:
                    html_content.extend([
                        "<h3>Control Flow</h3>",
                        "<table>",
                        "<tr><th>Type</th><th>Count</th></tr>"
                    ])
                    for flow_type, count in results['heuristics']['control_flow'].items():
                        html_content.append(f"<tr><td>{flow_type}</td><td>{count}</td></tr>")
                    html_content.append("</table>")
                
                # Risk factors
                if 'risk_assessment' in results['heuristics']:
                    html_content.extend([
                        "<h3>Risk Factors</h3>",
                        "<ul>"
                    ])
                    html_content.extend([f"<li>{factor}</li>" for factor in results['heuristics']['risk_assessment']['factors']])
                    html_content.append("</ul>")
            
            html_content.extend([
                "</body>",
                "</html>"
            ])
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(html_content))
            
            # Generate text report
            text_path = output_path / f"{base_name}_report.txt"
            text_content = [
                f"Macro Analysis Report for {results['file']}",
                "=" * 80,
                "",
                "Analysis Results:",
                f"Risk Level: {results['analysis']['risk_level'].upper()}",
                "",
                "Findings:",
            ]
            text_content.extend([f"- {finding}" for finding in results['analysis']['findings']])
            text_content.extend(["", "Signature Matches:"])
            if results['signatures']:
                text_content.extend([f"- {sig}" for sig in results['signatures']])
            else:
                text_content.append("No signature matches found")
            
            if results['heuristics']:
                text_content.extend([
                    "",
                    "Heuristic Analysis:",
                    "-" * 40
                ])
                
                if 'risk_assessment' in results['heuristics']:
                    text_content.extend([
                        "Risk Factors:"
                    ])
                    text_content.extend([f"- {factor}" for factor in results['heuristics']['risk_assessment']['factors']])
            
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(text_content))
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}")
            return False

    def batch_process(self, file_list: Sequence[Path]) -> dict[str, ReportData]:
        """!
        @brief Process multiple files in batch
        """
        self.logger.debug(f"Batch processing {len(file_list)} files")
        results: dict[str, ReportData] = {}
        
        for file_path in file_list:
            try:
                macro_content = self.extract_macros(file_path)
                if macro_content.get("code"):
                    results[str(file_path)] = {
                        "file": str(file_path),
                        "analysis": self.analyze_macros(macro_content),
                        "signatures": self.check_signatures(macro_content),
                        "heuristics": self.perform_heuristic_analysis(macro_content)
                    }
            except Exception as e:
                self.logger.error(f"Error processing {file_path}: {str(e)}")
        
        return results

    def process_file(self, file_path: Path, output_dir: Path) -> bool:
        """!
        @brief Process a single file
        """
        try:
            results = self.extract_macros(file_path)
            if results.get("code"):
                report_data: ReportData = {
                    "file": str(file_path),
                    "analysis": self.analyze_macros(results),
                    "signatures": self.check_signatures(results),
                    "heuristics": self.perform_heuristic_analysis(results)
                }
                
                return self.generate_report(report_data, output_dir)
            return False
            
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")
            return False

if __name__ == '__main__':
    """!
    @brief Hunter module self-test
    """
    # Add self-test code here if needed
    pass
