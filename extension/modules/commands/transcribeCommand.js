const { WhisperliveWebSocketManager } = require("../websocketWhisperLive");

let whisperLiveWS;

const startRecording = async (provider) => {
    try {
        whisperLiveWS = new WhisperliveWebSocketManager();
        whisperLiveWS.setProvider(provider);
        whisperLiveWS.connect();
        whisperLiveWS.sendMessage({ command: "startRecording" });
        
    } catch (error) {
        console.error("Failed to start recording:", error);
    }
};

const stopRecording = async (provider) => {
    try {
        whisperLiveWS.sendMessage({ command: "stopRecording" });
        whisperLiveWS.closeConnection();
    }
    catch (error) {
        console.error("Failed to stop recording:", error);
    }
}

module.exports = { startRecording, stopRecording};