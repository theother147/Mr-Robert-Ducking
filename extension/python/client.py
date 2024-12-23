import json
import threading
import asyncio
import websockets
import pyaudio
import time
from typing import List, Dict, Optional, Tuple

import logging
import uuid
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Placeholder for TranscriptionClient
class TranscriptionClient:
    def __init__(self, host: str, port: int, lang: str = "en", log_transcription: bool = True, command_server=None):
        self.host = host
        self.port = port
        self.lang = lang
        self.log_transcription = log_transcription
        self.command_server = command_server
        self.ws = None
        self.loop = asyncio.new_event_loop()
        self._connected = False
        self._should_reconnect = True
        self.current_session_id = None
        self.is_recording = False  # Track recording state
        self.current_transcription = None  # Store current session's transcription
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
                    self._connected = True
                    logger.info(f"Connected to transcription server at {uri}")

                    try:
                        while True:
                            try:
                                message = await self.ws.recv()
                                if self.log_transcription:
                                    logger.info(f"Received from server: {message}")
                                
                                # Process all messages, but only forward if recording
                                processed_message = self.process_transcription(message)
                                if processed_message and self.is_recording and self.command_server:
                                    await self.command_server.broadcast({
                                        "type": "transcription",
                                        "data": processed_message
                                    })
                                    
                            except websockets.exceptions.ConnectionClosed:
                                logger.warning("Connection closed by server")
                                break
                    finally:
                        self._connected = False
            except Exception as e:
                logger.error(f"Connection error: {e}")
                await asyncio.sleep(5)

    def clear_transcription(self):
        """Clear the current transcription when stopping recording"""
        self.current_transcription = None
        if self.command_server:
            asyncio.run_coroutine_threadsafe(
                self.command_server.broadcast({
                    "type": "transcription",
                    "data": {
                        "status": "transcribing",
                        "sessionId": self.current_session_id,
                        "text": ""  # Send empty text to clear frontend
                    }
                }),
                self.loop
            )

    def process_transcription(self, message):
        try:
            data = json.loads(message)
            
            # Handle server ready message
            if "message" in data and data["message"] == "SERVER_READY":
                return {
                    "status": "ready",
                    "sessionId": self.current_session_id
                }
            
            # Handle transcription segments
            if "segments" in data:
                # Only process messages from current session
                if data["uid"] == self.current_session_id:
                    full_text = " ".join(segment["text"].strip() for segment in data["segments"])
                    self.current_transcription = full_text
                    return {
                        "status": "transcribing",
                        "sessionId": self.current_session_id,
                        "text": full_text
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing transcription message: {e}")
            return None

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
                # Clear transcription before closing
                self.clear_transcription()
                
                # Send END_OF_AUDIO and wait for it to complete
                future = asyncio.run_coroutine_threadsafe(
                    self.ws.send(b"END_OF_AUDIO"),
                    self.loop
                )
                future.result(timeout=1.0)
                
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

    def start_new_session(self):
        """Start a new recording session"""
        self.current_session_id = str(uuid.uuid4())
        self.is_recording = True
        
        # Send new configuration for the new session
        config = {
            "uid": self.current_session_id,
            "language": None,
            "task": "transcribe",
            "model": "turbo",
            "use_vad": True,
            "detect_language": True,
            "translate": False,
            "max_clients": 4,
            "max_connection_time": 600
        }
        
        if self._connected and self.ws:
            try:
                # Send END_OF_AUDIO first to ensure clean state
                future = asyncio.run_coroutine_threadsafe(
                    self.ws.send(b"END_OF_AUDIO"),
                    self.loop
                )
                future.result(timeout=1.0)
                
                # Small delay to ensure server processes END_OF_AUDIO
                time.sleep(0.1)
                
                # Now send new configuration
                future = asyncio.run_coroutine_threadsafe(
                    self.ws.send(json.dumps(config)),
                    self.loop
                )
                future.result(timeout=1.0)
                logger.info(f"Started new recording session: {self.current_session_id}")
            except Exception as e:
                logger.error(f"Error starting new session: {e}")

    def end_session(self):
        """End the current recording session"""
        if self._connected and self.ws:
            try:
                # Send END_OF_AUDIO to finish current session
                future = asyncio.run_coroutine_threadsafe(
                    self.ws.send(b"END_OF_AUDIO"),
                    self.loop
                )
                future.result(timeout=1.0)
            except Exception as e:
                logger.error(f"Error ending session: {e}")

        self.is_recording = False
        self.current_session_id = None
        
        # Send empty text to clear the frontend
        if self.command_server:
            asyncio.run_coroutine_threadsafe(
                self.command_server.broadcast({
                    "type": "transcription",
                    "data": {
                        "status": "transcribing",
                        "text": ""
                    }
                }),
                self.loop
            )
        logger.info("Ended recording session")


class CommandServer:
    """
    A WebSocket server to receive commands for controlling the Client.
    """

    def __init__(self, client, host='localhost', port=8765):
        self.client = client
        self.host = host
        self.port = port
        self.clients = set()
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()

    def _run_server(self):
        """
        Run the server in the thread's event loop
        """
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.start_server_async())
        self.loop.run_forever()

    async def broadcast(self, message):
        """
        Broadcasts a message to all connected clients
        """
        if self.clients:  # only try to broadcast if there are connected clients
            message_str = json.dumps(message)
            await asyncio.gather(
                *[client.send(message_str) for client in self.clients],
                return_exceptions=True
            )

    async def handler(self, websocket):
        try:
            self.clients.add(websocket)
            logger.info(f"Client connected: {websocket.remote_address[0]}")
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    command = data.get('command')
                    args = data.get('args', {})

                    logger.debug(f"Received command: {command} with args: {args}")

                    if command == 'list_input_devices':
                        devices = self.client.list_input_devices()
                        await websocket.send(json.dumps({'status': 'success', 'devices': devices}))

                    elif command == 'change_input_device':
                        device_id = args.get('device_id')
                        if device_id is None:
                            await websocket.send(json.dumps({'status': 'error', 'message': 'device_id is required.'}))
                        else:
                            success, msg = self.client.change_input_device(device_id)
                            if success:
                                await websocket.send(json.dumps({'status': 'success', 'message': msg}))
                            else:
                                await websocket.send(json.dumps({'status': 'error', 'message': msg}))

                    elif command == 'start_recording':
                        success, msg = self.client.start_recording()
                        if success:
                            await websocket.send(json.dumps({'status': 'success', 'message': msg}))
                        else:
                            await websocket.send(json.dumps({'status': 'error', 'message': msg}))

                    elif command == 'stop_recording':
                        success, msg = self.client.stop_recording()
                        if success:
                            await websocket.send(json.dumps({'status': 'success', 'message': msg}))
                        else:
                            await websocket.send(json.dumps({'status': 'error', 'message': msg}))

                    elif command == 'pause_recording':
                        success, msg = self.client.pause_recording()
                        if success:
                            await websocket.send(json.dumps({'status': 'success', 'message': msg}))
                        else:
                            await websocket.send(json.dumps({'status': 'error', 'message': msg}))

                    elif command == 'resume_recording':
                        success, msg = self.client.resume_recording()
                        if success:
                            await websocket.send(json.dumps({'status': 'success', 'message': msg}))
                        else:
                            await websocket.send(json.dumps({'status': 'error', 'message': msg}))

                    else:
                        await websocket.send(json.dumps({'status': 'error', 'message': 'Unknown command'}))

                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "status": "error",
                        "message": "Invalid JSON format"
                    }))
        finally:
            self.clients.remove(websocket)

    async def start_server_async(self):
        self.server = await websockets.serve(
            self.handler,
            self.host,
            self.port,
            ping_interval=None
        )
        logger.info(f"CommandServer started on ws://{self.host}:{self.port}")


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

        # Initialize CommandServer
        self.command_server = CommandServer(self, host=command_host, port=command_port)

        # Initialize TranscriptionClient with command_server reference
        if self.host and self.port:
            self.transcription_client = TranscriptionClient(
                self.host, 
                self.port,
                lang=self.lang,
                log_transcription=self.log_transcription,
                command_server=self.command_server
            )
        else:
            self.transcription_client = None
            logger.warning("No transcription server details provided. TranscriptionClient not initialized.")

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
        
        # Start new transcription session
        if self.transcription_client:
            self.transcription_client.start_new_session()
        
        self.recording = True
        self.paused = False
        self.recording_thread = threading.Thread(target=self.record_audio, daemon=True)
        self.recording_thread.start()
        logger.info("Recording started.")
        return True, "Recording started."

    def stop_recording(self) -> Tuple[bool, str]:
        if not self.recording:
            return False, "Recording is not in progress."
        
        try:
            self.recording = False
            
            # Wait for recording thread to finish
            if self.recording_thread is not None:
                self.recording_thread.join(timeout=2.0)
                if self.recording_thread.is_alive():
                    logger.warning("Recording thread did not stop properly")
                self.recording_thread = None
            
            # End transcription session
            if self.transcription_client:
                self.transcription_client.end_session()
            
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
    parser.add_argument("--command-port", type=int, default=8766, help="Command WebSocket server port")
    parser.add_argument("--lang", type=str, help="Language for transcription (optional, uses auto-detection if not specified)")
    parser.add_argument("--translate", action="store_true", help="Enable translation")
    parser.add_argument("--model", type=str, default="turbo", help="Transcription model")
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