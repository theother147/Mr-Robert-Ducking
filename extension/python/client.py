import os
import json
import threading
import asyncio
import websockets
import pyaudio
import time
from typing import List, Dict, Optional, Tuple

import logging
import uuid
import base64
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Placeholder for TranscriptionClient
class TranscriptionClient:
    """
    Placeholder TranscriptionClient.
    Implement the actual logic based on your transcription server's API.
    """
    def __init__(self, host: str, port: int, lang: str = "en", log_transcription: bool = True):
        self.host = host
        self.port = port
        self.lang = lang
        self.log_transcription = log_transcription
        self.ws = None
        self.loop = asyncio.new_event_loop()
        self._connected = False
        self._should_reconnect = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect())

    async def connect(self):
        while self._should_reconnect:
            try:
                if not self._connected:
                    uri = f"ws://{self.host}:{self.port}"
                    self.ws = await websockets.connect(uri)
                    
                    # Send initial configuration
                    config = {
                        "uid": str(uuid.uuid4()),
                        "language": self.lang,
                        "task": "transcribe",
                        "model": "turbo",
                        "use_vad": True,
                        "max_clients": 4,
                        "max_connection_time": 600
                    }
                    await self.ws.send(json.dumps(config))
                    
                    self._connected = True
                    logger.info(f"Connected to transcription server at {uri}")

                    try:
                        while True:
                            try:
                                message = await self.ws.recv()
                                if self.log_transcription:
                                    logger.info(f"Received from server: {message}")
                            except websockets.exceptions.ConnectionClosed:
                                logger.warning("Connection closed by server")
                                break
                    finally:
                        self._connected = False
                        
                if not self._connected:
                    await asyncio.sleep(5)  # Wait before reconnecting
            except Exception as e:
                logger.error(f"Connection error: {e}")
                await asyncio.sleep(5)  # Wait before retry

    def send_audio_data(self, data: bytes):
        if not self._connected or not self.ws:
            return

        try:
            # Convert audio data to float32 numpy array
            audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            
            future = asyncio.run_coroutine_threadsafe(
                self.ws.send(audio_data.tobytes()),
                self.loop
            )
            future.result(timeout=0.1)
            
            if self.log_transcription:
                logger.debug(f"Sent audio data: {len(data)} bytes")
        except Exception as e:
            if self._connected:
                logger.error(f"Error sending audio data: {str(e)}")
                self._connected = False

    def close(self):
        """
        Properly close the connection by sending END_OF_AUDIO and cleaning up
        """
        try:
            self._should_reconnect = False
            if self.ws and self._connected:
                # Send END_OF_AUDIO and wait for it to complete
                future = asyncio.run_coroutine_threadsafe(
                    self.ws.send(b"END_OF_AUDIO"),
                    self.loop
                )
                future.result(timeout=1.0)  # Wait up to 1 second for the message to send
                
                # Close the websocket connection
                future = asyncio.run_coroutine_threadsafe(
                    self.ws.close(),
                    self.loop
                )
                future.result(timeout=1.0)
                
            # Wait for the thread to finish
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2.0)
                
            self._connected = False
            logger.info("Transcription client connection closed.")
        except Exception as e:
            logger.error(f"Error during transcription client shutdown: {e}")


class CommandServer:
    """
    A WebSocket server to receive commands for controlling the Client.
    """

    def __init__(self, client, host='localhost', port=8765):
        self.client = client
        self.host = host
        self.port = port
        self.server = None
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.start_server, daemon=True)

    def start(self):
        self.thread.start()

    def start_server(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.start_server_async())
            self.loop.run_forever()
        except Exception as e:
            logger.error(f"CommandServer encountered an error: {e}")

    async def start_server_async(self):
        self.server = await websockets.serve(
            self.handle_connection,
            self.host,
            self.port,
            ping_interval=None  # Disable ping/pong to avoid some connection issues
        )
        logger.info(f"CommandServer started on ws://{self.host}:{self.port}")

    async def handle_connection(self, websocket):
        client_ip = websocket.remote_address[0]
        logger.info(f"Client connected: {client_ip}")
        try:
            async for message in websocket:
                response = await self.process_command(message)
                await websocket.send(json.dumps(response))
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_ip}")

    async def process_command(self, message):
        try:
            data = json.loads(message)
            command = data.get('command')
            args = data.get('args', {})

            logger.debug(f"Received command: {command} with args: {args}")

            if command == 'list_input_devices':
                devices = self.client.list_input_devices()
                return {'status': 'success', 'devices': devices}

            elif command == 'change_input_device':
                device_id = args.get('device_id')
                if device_id is None:
                    return {'status': 'error', 'message': 'device_id is required.'}
                success, msg = self.client.change_input_device(device_id)
                if success:
                    return {'status': 'success', 'message': msg}
                else:
                    return {'status': 'error', 'message': msg}

            elif command == 'start_recording':
                success, msg = self.client.start_recording()
                if success:
                    return {'status': 'success', 'message': msg}
                else:
                    return {'status': 'error', 'message': msg}

            elif command == 'stop_recording':
                success, msg = self.client.stop_recording()
                if success:
                    return {'status': 'success', 'message': msg}
                else:
                    return {'status': 'error', 'message': msg}

            elif command == 'pause_recording':
                success, msg = self.client.pause_recording()
                if success:
                    return {'status': 'success', 'message': msg}
                else:
                    return {'status': 'error', 'message': msg}

            elif command == 'resume_recording':
                success, msg = self.client.resume_recording()
                if success:
                    return {'status': 'success', 'message': msg}
                else:
                    return {'status': 'error', 'message': msg}

            else:
                return {'status': 'error', 'message': 'Unknown command'}

        except json.JSONDecodeError:
            return {'status': 'error', 'message': 'Invalid JSON format'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


class Client:
    def __init__(
        self,
        host: str,
        port: int,
        lang: str = "en",
        translate: bool = False,
        model: str = "small",
        srt_file_path: str = "output.srt",
        use_vad: bool = True,
        log_transcription: bool = True,
        command_host: str = "localhost",
        command_port: int = 8765,
    ):
        self.host = host
        self.port = port
        self.lang = lang
        self.translate = translate
        self.model = model
        self.srt_file_path = srt_file_path
        self.use_vad = use_vad
        self.log_transcription = log_transcription

        self.pyaudio_instance = pyaudio.PyAudio()
        self.current_device_id = self.get_default_input_device()
        logger.info(f"Default input device: {self.get_device_name(self.current_device_id)} (ID: {self.current_device_id})")

        self.recording = False
        self.paused = False
        self.recording_thread = None

        # Initialize TranscriptionClient if server details are provided
        if self.host and self.port:
            self.transcription_client = TranscriptionClient(
                self.host, 
                self.port,
                lang=self.lang,
                log_transcription=self.log_transcription
            )
        else:
            self.transcription_client = None
            logger.warning("No transcription server details provided. TranscriptionClient not initialized.")

        # Initialize Command Server
        self.command_server = CommandServer(self, host=command_host, port=command_port)
        self.command_server.start()

    def get_default_input_device(self) -> Optional[int]:
        try:
            default_device = self.pyaudio_instance.get_default_input_device_info()
            return default_device['index']
        except IOError:
            logger.error("No default input device found.")
            return None

    def get_device_name(self, device_id) -> str:
        try:
            info = self.pyaudio_instance.get_device_info_by_index(device_id)
            return info['name']
        except IOError:
            return "Unknown Device"

    def list_input_devices(self) -> List[Dict[str, str]]:
        devices = []
        for i in range(self.pyaudio_instance.get_device_count()):
            try:
                info = self.pyaudio_instance.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    devices.append({'id': i, 'name': info['name']})
            except IOError:
                continue
        logger.info("Listing input devices.")
        return devices

    def change_input_device(self, device_id: int) -> Tuple[bool, str]:
        """
        Changes the input device to the specified device ID.
        """
        try:
            device_info = self.pyaudio_instance.get_device_info_by_index(device_id)
            if device_info['maxInputChannels'] == 0:
                return False, "Selected device does not support input."
            
            was_recording = self.recording
            if was_recording:
                # Properly stop the current recording
                self.recording = False
                if self.recording_thread:
                    self.recording_thread.join()
                    self.recording_thread = None

            # Change device
            self.current_device_id = device_id
            logger.info(f"Changed input device to {device_info['name']} (ID: {device_id}).")

            # Restart recording if it was active
            if was_recording:
                self.recording = True
                self.paused = False
                self.recording_thread = threading.Thread(target=self.record_audio, daemon=True)
                self.recording_thread.start()
                logger.info("Recording restarted with new device.")

            return True, f"Changed input device to {device_info['name']}."
        except Exception as e:
            self.recording = False
            self.recording_thread = None
            logger.error(f"Error changing input device: {e}")
            return False, str(e)

    def start_recording(self) -> Tuple[bool, str]:
        if self.recording:
            return False, "Recording is already in progress."
        if self.current_device_id is None:
            return False, "No valid input device selected."
        self.recording = True
        self.paused = False
        self.recording_thread = threading.Thread(target=self.record_audio, daemon=True)
        self.recording_thread.start()
        logger.info("Recording started.")
        return True, "Recording started."

    def stop_recording(self) -> Tuple[bool, str]:
        """
        Stops the current recording.
        """
        if not self.recording:
            return False, "Recording is not in progress."
        
        try:
            # Set recording flag to False
            self.recording = False
            
            # Wait for recording thread to finish
            if self.recording_thread is not None:
                self.recording_thread.join(timeout=2.0)  # Add timeout to prevent hanging
                if self.recording_thread.is_alive():
                    logger.warning("Recording thread did not stop properly")
                self.recording_thread = None
                
            logger.info("Recording stopped.")
            return True, "Recording stopped."
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            self.recording = False
            self.recording_thread = None
            return False, f"Error stopping recording: {e}"

    def pause_recording(self) -> Tuple[bool, str]:
        if not self.recording:
            return False, "Recording is not in progress."
        if self.paused:
            return False, "Recording is already paused."
        self.paused = True
        logger.info("Recording paused.")
        return True, "Recording paused."

    def resume_recording(self) -> Tuple[bool, str]:
        if not self.recording:
            return False, "Recording is not in progress."
        if not self.paused:
            return False, "Recording is not paused."
        self.paused = False
        logger.info("Recording resumed.")
        return True, "Recording resumed."

    def record_audio(self):
        """
        Records audio from the selected input device and streams it to the transcription client.
        """
        stream = None
        try:
            stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024,
                input_device_index=self.current_device_id
            )
            logger.info("Recording thread started.")
            
            while self.recording:
                try:
                    if self.paused:
                        time.sleep(0.1)
                        continue
                        
                    data = stream.read(1024, exception_on_overflow=False)
                    if self.transcription_client and self.transcription_client._connected:
                        self.transcription_client.send_audio_data(data)
                        
                except IOError as e:
                    logger.error(f"IOError during recording: {e}")
                    if not self.recording:  # Exit if we're supposed to stop
                        break
                    time.sleep(0.1)
                except Exception as e:
                    logger.error(f"Error during recording: {e}")
                    if not self.recording:  # Exit if we're supposed to stop
                        break
                    time.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Failed to initialize recording: {e}")
        finally:
            # Clean up resources
            if stream is not None:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception as e:
                    logger.error(f"Error closing audio stream: {e}")
            
            self.recording = False
            logger.info("Recording thread stopped.")

    def shutdown(self):
        """
        Shuts down the client gracefully, stopping recording and terminating resources.
        """
        logger.info("Shutting down client.")
        try:
            # Stop recording first
            if self.recording:
                self.stop_recording()
                
            # Close TranscriptionClient
            if self.transcription_client:
                self.transcription_client.close()
                
            # Shutdown Command Server
            if self.command_server:
                self.command_server.loop.call_soon_threadsafe(self.command_server.loop.stop)
                self.command_server.thread.join(timeout=2.0)
                
            # Terminate PyAudio
            if self.pyaudio_instance:
                self.pyaudio_instance.terminate()
                
            logger.info("Client shutdown complete.")
        except Exception as e:
            logger.error(f"Error during client shutdown: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extended WhisperLive Client with WebSocket Control")
    parser.add_argument("--server-host", default="localhost", help="Transcription server host")
    parser.add_argument("--server-port", type=int, default=9090, help="Transcription server port")
    parser.add_argument("--command-host", default="localhost", help="Command WebSocket server host")
    parser.add_argument("--command-port", type=int, default=8765, help="Command WebSocket server port")
    parser.add_argument("--lang", type=str, default="en", help="Language for transcription")
    parser.add_argument("--translate", action="store_true", help="Enable translation")
    parser.add_argument("--model", type=str, default="small", help="Transcription model")
    parser.add_argument("--srt-file", type=str, default="output.srt", help="Path to save SRT file")
    parser.add_argument("--use-vad", action="store_true", help="Enable Voice Activity Detection")
    parser.add_argument("--log-transcription", action="store_true", help="Enable transcription logging")

    args = parser.parse_args()

    try:
        client = Client(
            host=args.server_host,
            port=args.server_port,
            lang=args.lang,
            translate=args.translate,
            model=args.model,
            srt_file_path=args.srt_file,
            use_vad=args.use_vad,
            log_transcription=args.log_transcription,
            command_host=args.command_host,
            command_port=args.command_port
        )

        logger.info("Client is running. Press Ctrl+C to exit.")

        # Keep the main thread alive to allow background threads to run
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    finally:
        client.shutdown()