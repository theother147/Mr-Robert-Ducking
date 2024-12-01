from modules.controller.main import controller
from modules.api.main import WebSocketAPI

@controller.emits("check_environment")
async def check_env() -> tuple[str, dict]:
    """Check and ensure correct environment"""
    return ("environment", {"status": "checking"})

@controller.emits("server_start")
async def start_server() -> tuple[str, dict]:
    """Start the WebSocket server"""
    api = await WebSocketAPI.get_instance()
    return ("server", {"status": "running", "api": api})

@controller.emits("server_stop")
async def stop_server(api: WebSocketAPI) -> tuple[str, dict]:
    """Stop the WebSocket server"""
    await api.shutdown()
    return ("server", {"status": "stopped"}) 