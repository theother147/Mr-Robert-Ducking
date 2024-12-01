import ollama


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

    def chat(self, input: str, files: list = None):
        """
        Chat with the model
        """
        # Add the files and the content to the input
        if files is not None:
            for file in files:
                input += " Datei: " + file["filename"] + ", Code: " + file["content"]

        # Append the user message to the messages list
        self.messages.append({"role": "user", "content": input})
        # Create a chat response
        response = self.ollama.chat(
            model="codellama",
            messages=self.messages,
            stream=False
        )
        # Append the response to the messages list
        self.messages.append(response["message"])
        return response["message"]["content"]




llm = LLM()
while True:
    chat = input("Enter your message: ")
    if chat == "exit":
        break
    print(llm.chat(chat))

