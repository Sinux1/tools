#!/usr/bin/env python3
import sys

if sys.version_info < (3, 9):
    raise RuntimeError(
        "This script requires Python 3.9 or higher. "
        f"You are using Python {sys.version_info.major}.{sys.version_info.minor}"
    )

import os
import platform
import subprocess
import multiprocessing
from pathlib import Path
from time import time
from enum import IntEnum

class ResourceLimits(IntEnum):
    KB_TO_MB = 1024
    BYTES_TO_MB = 1024 * 1024
    MIN_MEMORY_PER_WORKER = 1024
    MIN_WORKERS = 2
    MAX_MEMORY_PERCENT = 75
    MIN_FREE_MEMORY = 2048

def should_parallelize():
    # Determine if parallel testing would be beneficial
    cpu_count = multiprocessing.cpu_count()
    mem_info = {}
    
    try:
        if platform.system() == 'Linux':
            with open('/proc/meminfo') as f:
                for line in f:
                    if 'MemAvailable' in line:
                        mem_info['available'] = int(line.split()[1]) / ResourceLimits.KB_TO_MB
                        break
        elif platform.system() == 'Darwin':
            mem = subprocess.run(['sysctl', '-n', 'hw.memsize'], capture_output=True, text=True)
            mem_info['available'] = int(mem.stdout) / ResourceLimits.BYTES_TO_MB
        elif platform.system() == 'Windows':
            import psutil
            mem_info['available'] = psutil.virtual_memory().available / ResourceLimits.BYTES_TO_MB
    except Exception as e:
        print(f"Warning: Couldn't determine memory info: {e}")
        return False, ResourceLimits.MIN_WORKERS

    if 'available' in mem_info:
        available_mem = mem_info['available']
        max_mem_to_use = (available_mem * ResourceLimits.MAX_MEMORY_PERCENT) / 100
        usable_mem = max(0, max_mem_to_use - ResourceLimits.MIN_FREE_MEMORY)
        max_workers_by_mem = int(usable_mem / ResourceLimits.MIN_MEMORY_PER_WORKER)
        workers = min(cpu_count, max_workers_by_mem)
        return workers >= ResourceLimits.MIN_WORKERS, max(ResourceLimits.MIN_WORKERS, workers)
    
    return False, ResourceLimits.MIN_WORKERS

def find_venvs():
    # Find all virtual environments in venvs directory
    venvs_dir = Path('venvs')
    if not venvs_dir.exists():
        print("No venvs directory found. Run setup_venvs.py first.")
        return []
    
    return [d for d in venvs_dir.iterdir() if d.is_dir() and d.name.startswith('py')]

def get_python_path(venv_path):
    # Get Python executable path for a virtual environment
    if platform.system() == 'Windows':
        return venv_path / 'Scripts' / 'python.exe'
    return venv_path / 'bin' / 'python'

def run_tests_in_venv(venv_path, parallel=False, workers=1):
    # Run pytest in the specified virtual environment
    python_path = get_python_path(venv_path)
    if not python_path.exists():
        print(f"Python not found in {venv_path}")
        return False, 0
    
    print(f"\nRunning tests in {venv_path.name}")
    print("=" * 80)
    
    try:
        pytest_args = [
            str(python_path),
            '-m',
            'pytest',
            'tests',
            '-v',
            '--cov=.',
            '--cov-report=term-missing',
            f'--cov-report=html:coverage_reports/{venv_path.name}'
        ]
        
        if parallel:
            pytest_args.extend(['-n', str(workers)])
        
        start_time = time()
        result = subprocess.run(pytest_args, check=False)
        execution_time = time() - start_time
        
        success = result.returncode == 0
        print(f"Tests in {venv_path.name}: {'PASSED' if success else 'FAILED'}")
        print(f"Execution time: {execution_time:.2f} seconds")
        
        return success, execution_time
        
    except Exception as e:
        print(f"Error running tests in {venv_path.name}: {e}")
        return False, 0

def main():
    Path('coverage_reports').mkdir(exist_ok=True)
    
    should_parallel, num_workers = should_parallelize()
    if should_parallel:
        print(f"Enabling parallel test execution with {num_workers} workers")
    else:
        print("Using sequential test execution")
    
    venvs = find_venvs()
    if not venvs:
        print("No virtual environments found!")
        return 1
    
    print(f"Found virtual environments: {', '.join(v.name for v in venvs)}")
    
    results = {}
    for venv in venvs:
        success, execution_time = run_tests_in_venv(venv, parallel=should_parallel, workers=num_workers)
        results[venv.name] = {'success': success, 'time': execution_time}
    
    print("\nTest Summary")
    print("=" * 80)
    for venv_name, result in results.items():
        status = 'PASSED' if result['success'] else 'FAILED'
        print(f"{venv_name}: {status} (Time: {result['time']:.2f}s)")
    
    return 0 if all(r['success'] for r in results.values()) else 1

if __name__ == '__main__':
    try:
        import psutil
    except ImportError:
        print("Installing psutil for memory detection...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'psutil'])
        import psutil
    
    sys.exit(main())
