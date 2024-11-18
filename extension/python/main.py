from .whisper_client import client
from .whisper_server import server


def main():
    server.run("0.0.0.0", 9090)
    result = client()
    print(result)