from modules.controller.main import controller
from modules.utils.logger import logger
from modules.install.triggers import start_installation

@controller.on("install_check")
async def handle_install_check(event_data):
    """Handle installation verification"""
    data = event_data.get('data', {})
    status = data.get('status')
    if status == "missing":
        logger.info("Dependencies not fully installed. Starting installation...")
        await start_installation()
    else:
        logger.info("Installation verified.")

@controller.on("install_start")
async def handle_installation(event_data):
    """Handle installation process"""
    data = event_data.get('data', {})
    status = data.get('status')
    if status == "completed":
        logger.info("Installation completed successfully.")
    else:
        error = data.get('error', 'Unknown error')
        logger.error(f"Installation failed: {error}")
        raise RuntimeError(f"Installation failed: {error}") 