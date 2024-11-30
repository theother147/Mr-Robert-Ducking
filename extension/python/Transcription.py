import asyncio
from whisper_live.client import TranscriptionClient
from whisper_live.server import TranscriptionServer
import socket


class Transcription:

    def transcribe(self):
        print("Starting transcription")
        try:
            client = TranscriptionClient(
                host="localhost",
                port=9090,
                lang="en",
                translate=True,
                model="turbo",
                use_vad=True,
                save_output_recording=False,
            )
            client()
        except Exception as e:
            print(f"Transcription error: {e}")
            return None

    async def cleanup(self):
        if self.server:
            # Add cleanup if needed
            pass



# class Transcribtion:
#     def __init__(self):
#         self.server = self.start_server()

#     def start_server(self):
#         server = TranscriptionServer()
#         #check if server is already running
#         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         if s.connect_ex(("localhost", 9090)) == 0:
#             print("Server already running")
#             s.close()
#         else:
#             print("Starting server")
#             server.run("0.0.0.0", no_single_model=True)
        
#     def transcribe(self):
#         print("transcribe")
#         client = TranscriptionClient(
#             host="localhost",
#             port=9090,
#             lang="en",
#             translate=True,
#             model="turbo",
#             use_vad=True,
#             save_output_recording=False,
#         )
#         client()

#server could still be running - check if disconnecting works
#bash
# lsof -i :9090
# kill -9 PID
