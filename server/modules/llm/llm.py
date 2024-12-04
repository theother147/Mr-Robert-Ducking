import ollama
from modules.utils.logger import logger
from modules.config.config import Config

class LLM:
    """
    Wrapper class for the Ollama API
    """
    def __init__(self):
        """
        Initialize the LLM object
        """
        logger.info("Initializing LLM service")
        self.ollama = ollama
        self.context = None
        self.messages = []
        logger.info("LLM service initialized successfully")

    async def generate_response(self, session_id: str, prompt: str, files: list = None) -> dict:
        """Generate a response to a prompt"""
        try:
            logger.info(f"Generating response for session {session_id}")
            logger.debug(f"Prompt: {prompt}")
            if files:
                logger.debug(f"Files included: {[f['filename'] for f in files]}")
            
            # Manage message history size
            if len(self.messages) >= Config.LLM_MAX_HISTORY:
                self.messages = self.messages[-Config.LLM_MAX_HISTORY:]
                logger.debug(f"Trimmed message history to {Config.LLM_MAX_HISTORY} messages")
            
            # Append the user message to the messages list
            self.messages.append({"role": "user", "content": prompt})
            logger.debug("Added user message to context")
            
            # Create a chat response
            logger.info("Sending request to Ollama")
            response = self.ollama.chat(
                model=Config.LLM_MODEL,
                messages=self.messages,
                stream=Config.LLM_STREAM
            )
            logger.debug("Received response from Ollama")
            
            # Append the response to the messages list
            self.messages.append(response["message"])
            logger.debug("Added response to context")
            
            result = {
                "session_id": session_id,
                "message": response["message"]["content"]
            }
            logger.info(f"Successfully generated response for session {session_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating response for session {session_id}: {str(e)}")
            return {
                "session_id": session_id,
                "message": f"Error generating response: {str(e)}"
            }

