
let isRecording = false;

const startRecording = async (provider, whisperLiveWS) => {
    try {
        whisperLiveWS.sendMessage({ command: "start_recording" });
        isRecording = true;
        if (provider && provider._view) {
            provider._view.webview.postMessage({
                command: "recordingStarted"
            });
        }
        
    } catch (error) {
        console.error("Failed to start recording:", error);
    }
};

const stopRecording = async (provider, whisperLiveWS) => {
    try {
        whisperLiveWS.sendMessage({ command: "stop_recording" });
        isRecording = false;
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

module.exports = { startRecording, stopRecording, getRecordingStatus: () => isRecording };