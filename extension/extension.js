/**
 * Main extension module that initializes and manages the VS Code extension.
 * Handles the setup of WebSocket connections, command registration, and UI components.
 */

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

// Global instances for managing WebSocket connections and UI
let wsManager;
let provider;
let transcriptionServer;
let wslManager;

/**
 * Activates the extension and sets up all necessary components
 * @param {vscode.ExtensionContext} context - The VS Code extension context
 */
function activate(context) {
  try {
    // Start Python-based transcription server
    const pythonExecutablePath = getPythonExecutablePath();
    const scriptPath = path.join(__dirname, "python", "client.py");
    transcriptionServer = spawn(pythonExecutablePath, ["-u", scriptPath]);

    // Initialize WebSocket managers for chat and transcription
    wsManager = new WebSocketManager();
    provider = new ViewProvider(context);
    wsManager.setProvider(provider);
    wsManager.connect();

    // Initialize WhisperLive WebSocket manager for transcription
    wslManager = new WhisperliveWebSocketManager();
    wslManager.setProvider(provider);
    wslManager.connect();

    // Register the webview provider for UI
    context.subscriptions.push(
      vscode.window.registerWebviewViewProvider("rubberduck.view", provider)
    );

    /**
     * Helper function to verify webview visibility before executing commands
     * @returns {boolean} Whether the webview is visible
     */
    function checkWebviewVisible() {
      if (!provider.isWebviewVisible()) {
        vscode.window.showInformationMessage(
          "Please open the Rubber Duck AI Assistant view first"
        );
        return false;
      }
      return true;
    }

    // Register command for sending messages to WebSocket server
    let sendMessageCommand = vscode.commands.registerCommand(
      "rubberduck.sendMessage",
      (messageData) => {
        if (checkWebviewVisible()) {
          if (messageData) {
            sendMessageToWs(messageData, wsManager, provider);
          } else {
            // Prevent sending messages during recording
            if (getRecordingStatus()) {
              vscode.window.showInformationMessage("Cannot send messages while recording is in progress"); 
              return;
            }
            // Trigger send message from webview
            provider._view.webview.postMessage({
              command: "triggerSend"
            });
          }
        }
      }
    );
    context.subscriptions.push(sendMessageCommand);

    // Register command for controlling audio transcription
    let transcribeCommand = vscode.commands.registerCommand(
      "rubberduck.transcribe",
      () => {
          if (!getRecordingStatus()) {
            startRecording(provider, wslManager);
          } else {
            stopRecording(provider, wslManager);
          }
      }
    );
    context.subscriptions.push(transcribeCommand);

    // Register command for file selection
    let selectFileCommand = vscode.commands.registerCommand(
      "rubberduck.selectFile",
      () => {
        if (checkWebviewVisible()) {
          selectFile(provider);
        }
      }
    );
    context.subscriptions.push(selectFileCommand);

    // Register command for starting new chat sessions
    let newChatCommand = vscode.commands.registerCommand(
      "rubberduck.newChat",
      () => {
        if (checkWebviewVisible()) {
          // Prevent new chat during recording
          if (getRecordingStatus()) {
            vscode.window.showInformationMessage("Cannot start new chat while recording is in progress"); 
            return;
          }

          // Clear chat history in webview
          provider._view.webview.postMessage({
            command: 'clearChat'
          });

          // Restart WebSocket connection
          wsManager.closeConnection();
          setTimeout(() => {
            wsManager.connect();
          }, 1000);
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

/**
 * Deactivates the extension and cleans up resources
 */
function deactivate() {
  // Close WebSocket connections
  if (wsManager) {
    wsManager.close_connection();
  }
  // Terminate transcription server
  if (transcriptionServer) {
    transcriptionServer.kill("SIGKILL");
  }
}

module.exports = {
  activate,
  deactivate,
};
