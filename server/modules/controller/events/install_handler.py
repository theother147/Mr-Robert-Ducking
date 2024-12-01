from modules.controller.main import controller
from modules.utils.logger import logger
from modules.controller.triggers.install_trigger import start_installation

@controller.on("install_check")
async def handle_install_check(data):
    """Handle installation verification"""
    status = data.get('data', {}).get('status')
    if status == "missing":
        logger.info("Dependencies not fully installed. Starting installation...")
        await start_installation()
    else:
        logger.info("Installation verified.")

@controller.on("install_start")
async def handle_installation(data):
    """Handle installation process"""
    status = data.get('data', {}).get('status')
    if status == "completed":
        logger.info("Installation completed successfully.")
    else:
        error = data.get('data', {}).get('error', 'Unknown error')
        logger.error(f"Installation failed: {error}")
        raise RuntimeError(f"Installation failed: {error}") 