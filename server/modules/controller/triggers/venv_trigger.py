import sys
from pathlib import Path
from modules.controller.main import controller

def get_venv_path():
    """Get the virtual environment path"""
    return Path(__file__).parent.parent.parent.parent / ".venv"

def is_correct_venv():
    """Check if we're running in the correct virtual environment"""
    venv_path = get_venv_path()
    if sys.platform == "win32":
        expected_python = venv_path / "Scripts" / "python.exe"
    else:
        expected_python = venv_path / "bin" / "python"
    
    return Path(sys.executable).resolve() == expected_python.resolve()

@controller.emits("venv_status")
def check_venv() -> tuple[str, str]:
    """Check virtual environment status"""
    status = "active" if is_correct_venv() else "inactive"
    return ("venv", status)

@controller.emits("venv_create")
def create_venv() -> tuple[str, str]:
    """Create virtual environment"""
    venv_path = get_venv_path()
    if not venv_path.exists():
        import venv
        venv.create(venv_path, with_pip=True)
    return ("venv", str(venv_path))

@controller.emits("venv_restart")
def restart_in_venv() -> tuple[str, str]:
    """Restart application in virtual environment"""
    venv_path = get_venv_path()
    if sys.platform == "win32":
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        python_path = venv_path / "bin" / "python"
    return ("venv", str(python_path)) 