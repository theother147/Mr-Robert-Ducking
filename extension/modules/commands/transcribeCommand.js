/**
 * Module for handling audio transcription commands.
 * Manages the recording state and communication with the WhisperLive WebSocket server.
 */

// Recording state tracking
let isRecording = false;

/**
 * Starts the audio recording and transcription process
 * @param {ViewProvider} provider - The webview provider for UI updates
 * @param {WhisperliveWebSocketManager} whisperLiveWS - WebSocket manager for WhisperLive server
 * @returns {Promise<void>}
 */
const startRecording = async (provider, whisperLiveWS) => {
    try {
        // Send start command to WhisperLive server
        whisperLiveWS.sendMessage({ command: "start_recording" });
        isRecording = true;
        
        // Update UI to show recording state
        if (provider && provider._view) {
            provider._view.webview.postMessage({
                command: "recordingStarted"
            });
        }
        
    } catch (error) {
        console.error("Failed to start recording:", error);
    }
};

/**
 * Stops the audio recording and transcription process
 * @param {ViewProvider} provider - The webview provider for UI updates
 * @param {WhisperliveWebSocketManager} whisperLiveWS - WebSocket manager for WhisperLive server
 * @returns {Promise<void>}
 */
const stopRecording = async (provider, whisperLiveWS) => {
    try {
        // Send stop command to WhisperLive server
        whisperLiveWS.sendMessage({ command: "stop_recording" });
        isRecording = false;
        
        // Update UI to show stopped state
        if (provider && provider._view) {
            provider._view.webview.postMessage({
                command: "recordingStopped"
            });
        }
    }
    catch (error) {
        console.error("Failed to stop recording:", error);
    }
}

/**
 * Gets the current recording status
 * @returns {boolean} Whether recording is currently active
 */
const getRecordingStatus = () => isRecording;

module.exports = { startRecording, stopRecording, getRecordingStatus };