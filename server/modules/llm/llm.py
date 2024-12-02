import ollama
from server.modules.controller.main import controller


class LLM:
    """
    Wrapper class for the Ollama API
    """
    def __init__(self):
        """
        Initialize the LLM object
        """
        self.ollama = ollama
        self.context = None
        self.messages = []

    @controller.on("generate_response")
    def chat(self, data: dict):
        """
        Chat with the model
        """
        # Add the files and the content to the input
        """if data["files"] is not None:
            for file in data["files"]:
                input += " Datei: " + file["filename"] + ", Code: " + file["content"]
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
        return self.send_response(data)

    @controller.emits("response_generated")
    def send_response(self, data):
        """
        Send the response to the Controller
        """
        return data





llm = LLM()
while True:
    chat = input("Enter your message: ")
    if chat == "exit":
        break
    print(llm.chat(chat))

