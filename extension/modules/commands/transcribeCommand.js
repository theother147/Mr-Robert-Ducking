
let isRecording = false;

const startRecording = async (whisperLiveWS) => {
    try {
        whisperLiveWS.sendMessage({ command: "start_recording" });
        isRecording = true;
        
    } catch (error) {
        console.error("Failed to start recording:", error);
    }
};

const stopRecording = async (whisperLiveWS) => {
    try {
        whisperLiveWS.sendMessage({ command: "stop_recording" });
        isRecording = false;
    }
    catch (error) {
        console.error("Failed to stop recording:", error);
    }
}

module.exports = { startRecording, stopRecording, getRecordingStatus: () => isRecording };