import ollama
from server.modules.controller.main import controller


class LLM:
    """
    Wrapper class for the Ollama API
    """
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        Initialize the LLM object
        """
        if not self._initialized:
            self.ollama = ollama
            self.context = None
            self.messages = []
            self._initialized = True

    @controller.on("generate_response")
    def chat(self, data: dict):
        """
        Chat with the model
        """
        # Append the user message to the messages list
        self.messages.append({"role": "user", "content": data["message"]})
        # Create a chat response
        response = self.ollama.chat(
            model="codellama",
            messages=self.messages,
            stream=False
        )
        # Append the response to the messages list
        self.messages.append(response["message"])
        data = {
            "session_id": data["session_id"],
            "response": response["message"]["content"]
        }
        return controller.trigger("response_generated", data)

llm = LLM()
while True:
    chat = input("Enter your message: ")
    if chat == "exit":
        break
    print(llm.chat(chat))

