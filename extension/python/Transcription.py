from whisper_live.client import TranscriptionClient

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