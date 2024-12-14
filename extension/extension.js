const { startRecording, stopRecording } = require("./modules/commands/recordingCommands");
const select_file = require("./modules/commands/selectFileCommand");
const send_message_to_ws = require("./modules/commands/sendMessageCommand");
const vscode = require("vscode");
const { exec } = require("child_process");
const { WebSocketManager } = require("./modules/websocket");
const { ViewProvider } = require("./modules/webview/webview");
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");
const { getPythonExecutablePath } = require("./modules/utils");

let wsManager;
let provider;
let transcriptionServer;

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
	try {
		// Start Whisper server
		const pythonExecutablePath = getPythonExecutablePath();
		const scriptPath = path.join(__dirname, "python", "run_server.py");
		transcriptionServer = spawn(pythonExecutablePath, ["-u", scriptPath]);

		wsManager = new WebSocketManager(); // Initialize WebSocket manager
		provider = new ViewProvider(context); // Initialize webview provider
		wsManager.set_provider(provider); // Share provider with WebSocket module
		wsManager.connect(); // Connect to WebSocket server

		// Register the webview provider to create UI
		context.subscriptions.push(
			vscode.window.registerWebviewViewProvider("rubberduck.view", provider)
		);

		// Register command to send messages to WebSocket server
		let sendMessageCommand = vscode.commands.registerCommand(
			"rubberduck.sendMessage",
			(messageData) => {
				send_message_to_ws(messageData, wsManager, provider);
			}
		);
		context.subscriptions.push(sendMessageCommand);

		// Register command to start recording
		let startRecordingCommand = vscode.commands.registerCommand(
			"rubberduck.startRecording",
			() => {
				startRecording(provider);
			}
		);
		context.subscriptions.push(startRecordingCommand);

		// Register command to stop recording
		let stopRecordingCommand = vscode.commands.registerCommand(
			"rubberduck.stopRecording",
			() => {
				stopRecording();
			}
		);
		context.subscriptions.push(stopRecordingCommand);

		// Register command to select and read file
		let selectFileCommand = vscode.commands.registerCommand(
			"rubberduck.selectFile",
			() => {
				select_file(provider);
			}
		);
		context.subscriptions.push(selectFileCommand);

		// Register command to begin new chat session
		let newChatCommand = vscode.commands.registerCommand(
			"rubberduck.newChat",
			() => {
				wsManager.close_connection();
				setTimeout(() => {
					wsManager.connect();
				}, 1000); // 1-second delay
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
	wsManager.close_connection();
	transcriptionServer.kill("SIGKILL");
}

module.exports = {
	activate,
	deactivate,
};
