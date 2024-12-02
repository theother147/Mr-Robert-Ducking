from modules.controller.main import controller
from .main import WebSocketAPI

@controller.emits("server_start")
async def start_server() -> dict:
    """Start the WebSocket server"""
    api = await WebSocketAPI.get_instance()
    return {
        "status": "running",
        "api": api,
        "type": "server"
    }

@controller.emits("server_stop")
async def stop_server(api: WebSocketAPI) -> dict:
    """Stop the WebSocket server"""
    await api.shutdown()
    return {
        "status": "stopped",
        "type": "server"
    } 