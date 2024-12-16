const { WhisperliveWebSocketManager } = require("../websocketWhisperLive");

let whisperLiveWS;
let isRecording = false;

const startRecording = async (provider) => {
    try {
        whisperLiveWS = new WhisperliveWebSocketManager();
        whisperLiveWS.setProvider(provider);
        whisperLiveWS.connect();
        whisperLiveWS.sendMessage({ command: "start_recording" });
        isRecording = true;
        
    } catch (error) {
        console.error("Failed to start recording:", error);
    }
};

const stopRecording = async (provider) => {
    try {
        whisperLiveWS.sendMessage({ command: "stop_recording" });
        whisperLiveWS.closeConnection();
        isRecording = false;
    }
    catch (error) {
        console.error("Failed to stop recording:", error);
    }
}

module.exports = { startRecording, stopRecording, getRecordingStatus: () => isRecording };