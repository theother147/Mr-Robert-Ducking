const recording = require("./modules/commands/recordingCommand");
const select_file = require("./modules/commands/selectFileCommand");
const send_message_to_ws = require("./modules/commands/sendMessageCommand");
const vscode = require("vscode");
const { exec } = require("child_process");
const { WebSocketManager } = require('./modules/websocket');
const { ViewProvider } = require('./modules/webview/webview');
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

let wsManager;
let provider;
const pythonVirtualEnvironmentPath = path.join(__dirname, "python", ".venv");
let pythonExecutablePath;
console.log("Platform:", process.platform);
if (process.platform.includes("win32")) {
	pythonExecutablePath = path.join(
		pythonVirtualEnvironmentPath,
		"Scripts",
		"python.exe"
	);
} else {
	pythonExecutablePath = path.join(
		pythonVirtualEnvironmentPath,
		"bin",
		"python"
	);
}
const scriptPath = path.join(__dirname, "python", "run_server.py");
var transcriptionServerScript;

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
	try {
		// Start Whisper server

		transcriptionServerScript = spawn(pythonExecutablePath, [
			"-u",
			scriptPath,
			"--no_single_model",
		]);

		transcriptionServerScript.stdout.on("data", (data) => {
			console.log("Python output:", data.toString());
		});

		// Add stderr handler
		transcriptionServerScript.stderr.on("data", (data) => {
			console.error("Python error:", data.toString());
		});

		// Add exit handler
		transcriptionServerScript.on("close", (code) => {
			console.log(`Python process exited with code ${code}`);
		});

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
			(messageData, provider) => {
				send_message_to_ws(messageData, wsManager, provider);
			}
		);
		context.subscriptions.push(sendMessageCommand);

		// Register command to start recording
		let recordingCommand = vscode.commands.registerCommand(
			"rubberduck.startRecording",
			async(provider) => {recording(provider);}
		);
		context.subscriptions.push(recordingCommand);

		// Register command to select and read file
		let selectFileCommand = vscode.commands.registerCommand(
			"rubberduck.selectFile",
			async () => {
				select_file(provider);
			}
		);
		context.subscriptions.push(selectFileCommand);
	} catch (error) {
		console.error("Extension activation failed:", error);
		vscode.window.showErrorMessage(
			`Extension activation failed: ${error.message}`
		);
	}
}

function deactivate() {
	wsManager.close_connection();
	transcriptionServerScript.kill("SIGKILL");
}

module.exports = {
	activate,
	deactivate,
};
