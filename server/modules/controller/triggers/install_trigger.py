from modules.controller.main import controller
from modules.install.install import verify_installation, install_dependencies
from modules.utils.logger import logger

@controller.emits("install_check")
async def check_installation() -> tuple[str, dict]:
    """Check if all dependencies are installed"""
    is_installed = verify_installation()
    return ("installation", {"status": "verified" if is_installed else "missing"})

@controller.emits("install_start")
async def start_installation() -> tuple[str, dict]:
    """Start the installation process"""
    try:
        install_dependencies()
        return ("installation", {"status": "completed"})
    except Exception as e:
        logger.error(f"Installation failed: {e}")
        return ("installation", {"status": "failed", "error": str(e)}) 