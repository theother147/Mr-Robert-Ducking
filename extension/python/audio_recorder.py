import asyncio
import websockets
import pyaudio
import json
import argparse
import uuid
import logging
import numpy as np
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioRecorder:
    def __init__(self, ws_uri: str, device_index: Optional[int] = None):
        self.ws_uri = ws_uri
        self.device_index = device_index
        self.session_id = str(uuid.uuid4())
        self.is_recording = False
        self.websocket = None
        
        # Audio configuration for WhisperLive compatibility
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.RATE = 16000  # WhisperLive expects 16kHz
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.ws_uri)
            logger.info(f"Connected to WebSocket server at {self.ws_uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket server: {e}")
            return False
            
    def setup_audio_stream(self):
        try:
            self.stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.CHUNK
            )
            logger.info("Audio stream initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize audio stream: {e}")
            return False
            
    async def send_audio(self):
        if not self.setup_audio_stream():
            return
            
        self.is_recording = True
        logger.info("Starting audio recording...")
        
        try:
            while self.is_recording:
                try:
                    # Read audio data
                    data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                    audio_array = np.frombuffer(data, dtype=np.float32)
                    
                    # Format message to match existing extension expectations
                    message = {
                        "type": "recording",  # Keep existing message type
                        "text": "",  # Will be filled by transcription
                        "audio": {
                            "data": audio_array.tolist(),
                            "sample_rate": self.RATE,
                            "chunk_size": self.CHUNK,
                            "session_id": self.session_id
                        }
                    }
                    
                    if self.websocket and self.websocket.open:
                        await self.websocket.send(json.dumps(message))
                    else:
                        logger.warning("WebSocket connection lost, attempting to reconnect...")
                        if await self.connect():
                            continue
                        else:
                            break
                            
                except Exception as e:
                    logger.error(f"Error during audio streaming: {e}")
                    await asyncio.sleep(0.1)  # Prevent tight loop on error
                    
        except Exception as e:
            logger.error(f"Fatal error in audio streaming: {e}")
        finally:
            self.stop()
            
    def stop(self):
        self.is_recording = False
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.error(f"Error stopping audio stream: {e}")
                
        if self.audio:
            try:
                self.audio.terminate()
            except Exception as e:
                logger.error(f"Error terminating PyAudio: {e}")
                
        logger.info("Audio recording stopped")
        
    async def cleanup(self):
        self.stop()
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket connection: {e}")
                
async def main(args):
    recorder = AudioRecorder(args.ws_uri, args.device_index)
    
    if not await recorder.connect():
        logger.error("Failed to establish WebSocket connection. Exiting...")
        return
        
    try:
        await recorder.send_audio()
    except KeyboardInterrupt:
        logger.info("Recording interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await recorder.cleanup()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Python Audio Recorder for VS Code Extension")
    parser.add_argument('--ws_uri', type=str, default='ws://localhost:8765',
                      help='WebSocket URI of the VS Code extension')
    parser.add_argument('--device_index', type=int, default=None,
                      help='Index of the microphone device to use')
    parser.add_argument('--list_devices', action='store_true',
                      help='List available audio input devices and exit')
    
    args = parser.parse_args()
    
    if args.list_devices:
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev.get('maxInputChannels') > 0:
                print(f"Index {i}: {dev.get('name')}")
        p.terminate()
    else:
        asyncio.run(main(args)) 