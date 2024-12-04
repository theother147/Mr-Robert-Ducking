import sys
from pathlib import Path

def get_venv_path():
    """Get the virtual environment path"""
    return Path(__file__).parent.parent.parent / ".venv"

def is_correct_venv():
    """Check if we're running in the correct virtual environment"""
    venv_path = get_venv_path()
    if sys.platform == "win32":
        expected_python = venv_path / "Scripts" / "python.exe"
    else:
        expected_python = venv_path / "bin" / "python"
    
    return Path(sys.executable).resolve() == expected_python.resolve()

def check_venv() -> dict:
    """Check virtual environment status"""
    status = "active" if is_correct_venv() else "inactive"
    return {
        "status": status,
        "type": "venv"
    }

def create_venv() -> dict:
    """Create virtual environment"""
    venv_path = get_venv_path()
    if not venv_path.exists():
        import venv
        venv.create(venv_path, with_pip=True)
    return {
        "path": str(venv_path),
        "type": "venv"
    }

def get_venv_python():
    """Get the path to the virtual environment's Python executable"""
    venv_path = get_venv_path()
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python" 