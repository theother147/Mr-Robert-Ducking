from modules.controller.main import controller

@controller.emits("check_environment")
async def check_env() -> tuple[str, dict]:
    """Check and ensure correct environment"""
    return ("environment", {"status": "checking"}) 