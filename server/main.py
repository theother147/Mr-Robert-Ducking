# Description: Main entry point for the server. Starts the WebSocket server and listens for incoming requests.
import sys
import asyncio
from pathlib import Path
import subprocess
import importlib.util


# Add server directory to Python path
server_dir = Path(__file__).parent
sys.path.insert(0, str(server_dir))

def is_package_installed(package_name: str) -> bool:
    """Check if a Python package is installed"""
    return importlib.util.find_spec(package_name) is not None

def verify_basic_dependencies() -> bool:
    """Verify that basic dependencies are installed"""
    required_packages = ['colorlog', 'websockets']
    return all(is_package_installed(pkg) for pkg in required_packages)

def install_basic_dependencies():
    """Install basic dependencies using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "colorlog", "websockets"])
        return True
    except subprocess.CalledProcessError:
        return False

def ensure_basic_environment():
    """Ensure basic environment is set up before proceeding"""
    try:
        if not verify_basic_dependencies():
            print("Installing basic dependencies...")
            if not install_basic_dependencies():
                print("Failed to install basic dependencies")
                sys.exit(1)
            print("Basic dependencies installed. Restarting...")
            # Restart the current process
            subprocess.run([sys.executable] + sys.argv, check=True)
            sys.exit(0)
    except KeyboardInterrupt:
        print("\nSetup interrupted by user")
        sys.exit(0)
    except subprocess.CalledProcessError:
        print("Failed to restart after installing dependencies")
        sys.exit(1)

# Run basic environment check first
if __name__ == "__main__":
    ensure_basic_environment()

# Now we can safely import and use the logger and other dependencies
from modules.utils.logger import logger
from modules.install.triggers import check_installation, start_installation
from modules.utils.triggers import check_env
from modules.api.triggers import start_server, stop_server
from modules.controller.events import discover_handlers

async def ensure_environment():
    """Ensure we're in the correct environment with all dependencies"""
    try:
        result = await check_installation()
        data = result.get('data', {})
        if data.get('status') == "missing":
            result = await start_installation()
            data = result.get('data', {})
            if data.get('status') == "failed":
                logger.error(f"Installation failed: {data.get('error', 'Unknown error')}")
                sys.exit(1)
            # If installation completed, we need to restart in the venv
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nSetup interrupted by user")
        sys.exit(0)

async def cleanup(api=None):
    """Cleanup function to ensure graceful shutdown"""
    if api:
        await stop_server(api)
    logger.info("Server stopped by user.")

async def main():
    from server.modules.llm.llm import LLM
    api = None
    try:
        llm = LLM()

        # Discover all event handlers
        discover_handlers()
        logger.debug("Event handlers discovery completed")
        
        # Run environment check
        await ensure_environment()
        
        # Check environment using emitter
        await check_env()
        
        # Start the server
        result = await start_server()
        data = result.get('data', {})
        api = data.get('api')
        
        # Run forever
        await asyncio.Future()
        
    except asyncio.CancelledError:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        await cleanup(api)

async def run_with_cleanup():
    """Run the main coroutine with proper cleanup on cancellation"""
    try:
        await main()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt...")

if __name__ == "__main__":
    try:
        asyncio.run(run_with_cleanup())
    except KeyboardInterrupt:
        pass  # Already handled in run_with_cleanup
    except Exception as e:
        logger.error(f"Unexpected error: {e}")