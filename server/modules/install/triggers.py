from modules.controller.main import controller
from .install import verify_installation, install_dependencies
from modules.utils.logger import logger

@controller.emits("install_check")
async def check_installation() -> dict:
    """Check if all dependencies are installed"""
    is_installed = verify_installation()
    return {
        "status": "verified" if is_installed else "missing",
        "type": "installation"
    }

@controller.emits("install_start")
async def start_installation() -> dict:
    """Start the installation process"""
    try:
        install_dependencies()
        return {
            "status": "completed",
            "type": "installation"
        }
    except Exception as e:
        logger.error(f"Installation failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "type": "installation"
        } 