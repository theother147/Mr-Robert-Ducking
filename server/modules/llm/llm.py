import ollama


class LLM:
    def __init__(self):
        self.ollama = ollama
        self.context = None

    def chat(self, input: str):
        if self.context is not None:
            response = self.ollama.generate(
                model="codellama",
                prompt=input,
                context=self.context,
                stream=False
            )

        else:
            response = self.ollama.generate(
                model="codellama",
                prompt=input,
                stream=False
            )
        self.context = response["context"]
        return response["response"]
