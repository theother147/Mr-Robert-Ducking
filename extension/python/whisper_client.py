from whisper_client import TranscriptionClient

client = TranscriptionClient(
    "localhost",
    9090,
    multilingual=True,
    language="en",
    translate=True,
    model="turbo",
    use_vad=True,
    save_output_recording=False,  # Only used for microphone input, False by Default
    max_clients=4,
    max_connection_time=600,
)
