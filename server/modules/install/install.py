import sys
import subprocess
import os
import signal
from pathlib import Path

def get_venv_path() -> Path:
    """Get the virtual environment path"""
    return Path(__file__).parent.parent.parent / ".venv"

def is_venv_activated() -> bool:
    """Check if we're running in the correct virtual environment"""
    venv_path = get_venv_path()
    if sys.platform == "win32":
        expected_python = venv_path / "Scripts" / "python.exe"
    else:
        expected_python = venv_path / "bin" / "python"
    
    return Path(sys.executable).resolve() == expected_python.resolve()

def create_venv_if_needed():
    """Create virtual environment if it doesn't exist"""
    venv_path = get_venv_path()
    if not venv_path.exists():
        print("Creating virtual environment...")
        import venv
        venv.create(venv_path, with_pip=True, upgrade_deps=True)

def get_venv_python():
    """Get the path to the virtual environment's Python executable"""
    venv_path = get_venv_path()
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"

def get_venv_pip():
    """Get the path to the virtual environment's pip executable"""
    venv_path = get_venv_path()
    if sys.platform == "win32":
        return venv_path / "Scripts" / "pip.exe"
    return venv_path / "bin" / "pip"

def install_dependencies_in_venv():
    """Install dependencies in the current venv"""
    pip_path = get_venv_pip()
    if not pip_path.exists():
        raise RuntimeError(f"pip not found at {pip_path}")
        
    # Install from requirements.txt
    req_file = Path(__file__).parent.parent.parent / "requirements.txt"
    cmd = [str(pip_path), "install", "-r", str(req_file)]
    
    print("Installing dependencies from requirements.txt")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"pip install failed: {result.stderr}")
        
    print("Dependencies installed successfully")

def activate_venv(install_deps=False):
    """Activate the virtual environment and restart the script"""
    venv_path = get_venv_path()
    
    if not venv_path.exists():
        create_venv_if_needed()

    python_path = get_venv_python()
    if not python_path.exists():
        raise RuntimeError(f"Virtual environment Python not found at {python_path}")

    print("Activating virtual environment...")
    
    # If we need to install dependencies, do it first in the venv
    if install_deps:
        cmd_install = [str(python_path), "-c", 
                      "from modules.install.install import install_dependencies_in_venv; install_dependencies_in_venv()"]
        subprocess.run(cmd_install, check=True)
    
    # Create activation command
    cmd = [str(python_path)] + sys.argv
    shell = sys.platform == "win32"

    try:
        # Start new process with venv Python
        process = subprocess.Popen(cmd, shell=shell)
        
        # Wait for the process to complete or Ctrl+C
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\nStopping server...")
            if sys.platform == "win32":
                # On Windows, create a Ctrl+C event
                process.send_signal(signal.CTRL_C_EVENT)
            else:
                # On Unix, send SIGINT
                process.send_signal(signal.SIGINT)
            # Wait for graceful shutdown
            process.wait()
            print("Server stopped.")
        
        # Exit with the same code as the subprocess
        sys.exit(process.returncode)
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to activate virtual environment: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

def verify_installation() -> bool:
    """
    Verify virtual environment and basic package installation
    Returns True if everything is properly set up, False otherwise
    """
    try:
        # First check if we're in the correct venv
        if not is_venv_activated():
            print("Not running in virtual environment")
            return False
            
        # Quick check for a required package
        try:
            import colorlog
            return True
        except ImportError:
            return False
            
    except Exception as e:
        print(f"Error verifying installation: {e}")
        return False

def install_dependencies():
    """Install all required dependencies from requirements.txt"""
    try:
        # If we're not in the venv, activate it and install dependencies
        if not is_venv_activated():
            activate_venv(install_deps=True)
        else:
            # If we're already in the venv, just install dependencies
            install_dependencies_in_venv()
            
    except Exception as e:
        print(f"Failed to install dependencies: {e}")
        raise