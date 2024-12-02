from server.modules.controller.main import controller
from server.modules.utils.logger import logger
from server.modules.llm.llm import LLM


@controller.on("init_llm")
def handle_init_llm(data):
    """Handler for LLM initialization"""
    logger.info(f"[LLM INIT] Initializing LLM...")
    llm = LLM()

@controller.on("response_generated")
def handle_response(data):
    """Handler for LLM responses"""
    session_id = data['session_id']
    response = data['data']
    logger.info(f"[LLM RESPONSE] Response received: {response}")
