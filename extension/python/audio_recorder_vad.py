# python/audio_recorder_vad.py
import pyaudio
import webrtcvad
import numpy as np
import sys
import json
import time

RATE = 16000
CHUNK_DURATION_MS = 30  # Duration of each chunk in milliseconds
CHUNK_SIZE = int(RATE * CHUNK_DURATION_MS / 1000)  # Number of samples per chunk
FORMAT = pyaudio.paInt16
CHANNELS = 1

def main():
    # Initialize PyAudio and VAD
    audio = pyaudio.PyAudio()
    vad = webrtcvad.Vad(3)  # Aggressiveness mode 3 (0-3)
    
    try:
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )
        
        print(json.dumps({"status": "ready"}))
        sys.stdout.flush()
        
        while True:
            audio_chunk = stream.read(CHUNK_SIZE)
            is_speech = vad.is_speech(audio_chunk, RATE)
            
            # Send status update
            print(json.dumps({
                "status": "recording",
                "is_speech": is_speech
            }))
            sys.stdout.flush()
            
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()

if __name__ == "__main__":
    main()