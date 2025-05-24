#!/usr/bin/env python3
import os
import sys
import platform
import subprocess
import venv
from pathlib import Path

def find_python_versions():
    """Find available Python versions 3.9, 3.10, 3.11"""
    versions = {}
    python_commands = [
        (f'python{v}', f'python{v}.exe', f'py -{v}') 
        for v in ('3.9', '3.10', '3.11')
    ]
    
    for cmds in python_commands:
        for cmd in cmds:
            try:
                # Check if command exists and get version
                result = subprocess.run(
                    [cmd, '--version'], 
                    capture_output=True, 
                    text=True
                )
                if result.returncode == 0:
                    version = result.stdout.split()[1]
                    short_ver = '.'.join(version.split('.')[:2])
                    versions[short_ver] = cmd
                    break
            except FileNotFoundError:
                continue
    
    return versions

def setup_venv(python_cmd, version, venvs_dir):
    """Setup virtual environment for specific Python version"""
    venv_path = venvs_dir / f'py{version.replace(".", "")}'
    print(f'Setting up {python_cmd} environment in {venv_path}...')
    
    try:
        venv.create(venv_path, with_pip=True)
        
        # Get activation script path
        if platform.system() == 'Windows':
            activate_script = venv_path / 'Scripts' / 'python.exe'
        else:
            activate_script = venv_path / 'bin' / 'python'
            
        # Install requirements
        subprocess.run([
            str(activate_script),
            '-m', 'pip', 'install', '--upgrade', 'pip'
        ])
        subprocess.run([
            str(activate_script),
            '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])
        
        print(f'Successfully set up {python_cmd} environment')
        return True
        
    except Exception as e:
        print(f'Error setting up {python_cmd} environment: {e}')
        return False

def main():
    # Create venvs directory
    venvs_dir = Path('venvs')
    venvs_dir.mkdir(exist_ok=True)
    
    # Find Python versions
    print('Detecting Python versions...')
    versions = find_python_versions()
    
    if not versions:
        print('No supported Python versions found!')
        return 1
        
    print(f'Found Python versions: {", ".join(versions.keys())}')
    
    # Setup virtual environments
    success = []
    for version, cmd in versions.items():
        if setup_venv(cmd, version, venvs_dir):
            success.append(version)
    
    # Print activation instructions
    print('\nTo activate environments:')
    for version in success:
        venv_name = f'py{version.replace(".", "")}'
        if platform.system() == 'Windows':
            print(f'venvs\\{venv_name}\\Scripts\\activate.bat  # For Python {version}')
        else:
            print(f'source venvs/{venv_name}/bin/activate  # For Python {version}')
    
    return 0

if __name__ == '__main__':
    sys.exit(main())