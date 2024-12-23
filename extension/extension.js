const { startRecording, stopRecording, getRecordingStatus } = require("./modules/commands/transcribeCommand");
const selectFile = require("./modules/commands/selectFileCommand");
const sendMessageToWs = require("./modules/commands/sendMessageCommand");
const vscode = require("vscode");
const { exec } = require("child_process");
const { WebSocketManager } = require("./modules/websocket");
const { WhisperliveWebSocketManager } = require("./modules/websocketWhisperLive");
const { ViewProvider } = require("./modules/webview/webview");
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");
const { getPythonExecutablePath } = require("./modules/utils");

let wsManager;
let provider;
let transcriptionServer;

let wslManager;
/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
  try {
    // Start Whisper server
    const pythonExecutablePath = getPythonExecutablePath();
    const scriptPath = path.join(__dirname, "python", "client.py");
    transcriptionServer = spawn(pythonExecutablePath, ["-u", scriptPath]);

    wsManager = new WebSocketManager(); // Initialize WebSocket manager
    provider = new ViewProvider(context); // Initialize webview provider
    wsManager.setProvider(provider); // Share provider with WebSocket module
    wsManager.connect(); // Connect to WebSocket server

    wslManager = new WhisperliveWebSocketManager(); // Initialize WhisperLive WebSocket manager
    wslManager.setProvider(provider); // Share provider with WhisperLive WebSocket module
    wslManager.connect(); // Connect to WhisperLive WebSocket server

    // Register the webview provider to create UI
    context.subscriptions.push(
      vscode.window.registerWebviewViewProvider("rubberduck.view", provider)
    );

    // Check webview visibility
    function checkWebviewVisible() {
      if (!provider.isWebviewVisible()) {
        vscode.window.showInformationMessage(
          "Please open the Rubber Duck AI Assistant view first"
        );
        return false;
      }
      return true;
    }

    // Register command to send messages to WebSocket server
    let sendMessageCommand = vscode.commands.registerCommand(
      "rubberduck.sendMessage",
      (messageData) => {
        if (checkWebviewVisible()) {
          if (messageData) {
            sendMessageToWs(messageData, wsManager, provider);
          } else {
            // Don't allow sending messages while recording is in progress
            if (getRecordingStatus()) {
              vscode.window.showInformationMessage("Cannot send messages while recording is in progress"); 
              return;
            }
            // Trigger send message from webview if no message data is provided
            provider._view.webview.postMessage({
              command: "triggerSend"
            });
          }
        }
      }
    );
    context.subscriptions.push(sendMessageCommand);

    // Register command to start recording
    let transcribeCommand = vscode.commands.registerCommand(
      "rubberduck.transcribe",
      (options = {}) => {
        if (options.force_stop) {
          stopRecording(provider, wslManager); // Stop recording if forced
        } else {
          if (checkWebviewVisible() && !getRecordingStatus()) {
              startRecording(provider, wslManager); // Start recording if not already recording
          } else {
            stopRecording(provider, wslManager); // Stop recording if already recording
          }
        }
      }
    );
    context.subscriptions.push(transcribeCommand);

    // Register command to select and read file
    let selectFileCommand = vscode.commands.registerCommand(
      "rubberduck.selectFile",
      () => {
        if (checkWebviewVisible()) {
          selectFile(provider);
        }
      }
    );
    context.subscriptions.push(selectFileCommand);

    // Register command to begin new chat session
    let newChatCommand = vscode.commands.registerCommand(
      "rubberduck.newChat",
      () => {
        if (checkWebviewVisible()) {

          // Don't allow starting new chat while recording is in progress
          if (getRecordingStatus()) {
            vscode.window.showInformationMessage("Cannot start new chat while recording is in progress"); 
            return;
          }

          // Notify webview to clear chat history
          provider._view.webview.postMessage({
            command: 'clearChat'
          });

          // Close and re-open WebSocket connection
          wsManager.closeConnection();
          setTimeout(() => {
            wsManager.connect();
          }, 1000); // 1-second delay
        }
      }
    );
    context.subscriptions.push(newChatCommand);
    
  } catch (error) {
    console.error("Extension activation failed:", error);
    vscode.window.showErrorMessage(
      `Extension activation failed: ${error.message}`
    );
  }
}

function deactivate() {
	if (wsManager) {
		wsManager.close_connection();
	}
	if (transcriptionServer) {
		transcriptionServer.kill("SIGKILL");
	}
}

module.exports = {
  activate,
  deactivate,
};
