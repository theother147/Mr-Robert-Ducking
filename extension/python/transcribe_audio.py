from whisper_live.client import TranscriptionClient

def transcribe_audio():
    try:
        client = TranscriptionClient(
            host="localhost",
            port=9090,
            lang="de",
            translate=False,
            model="turbo",
            use_vad=True,
            save_output_recording=False,
        )
        client()
    except Exception as e:
        print(f"Transcription error: {e}")
        return None

transcribe_audio()