const vscode = require("vscode");
const { exec } = require("child_process");
const {
	connect_websocket,
	close_websocket,
	send_message_to_websocket,
} = require("./modules/websocket");
const { ViewProvider } = require("./modules/webview/webview");
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

let provider;
let recordingCommand;
const pythonExecutablePath = path.join(
	__dirname,
	"python",
	".venv",
	"bin",
	"python"
);
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

		// Connect to WebSocket server
		connect_websocket();

		// Register the view provider
		provider = new ViewProvider(context);
		context.subscriptions.push(
			vscode.window.registerWebviewViewProvider("rubberduck.view", provider)
		);

		// Only register command if not already registered
		if (!recordingCommand) {
			recordingCommand = vscode.commands.registerCommand(
				"rubberduck.startRecording",
				async () => {
					try {
						const pythonExecutablePath = path.join(
							__dirname,
							"python",
							".venv",
							"bin",
							"python"
						);

						const scriptPath = path.join(__dirname, "python", "transcribe_audio.py");

						const recordingProcess = spawn(pythonExecutablePath, [
							"-u",
							scriptPath,
						]);

						if (!fs.existsSync(pythonExecutablePath)) {
							console.error(
								"Python executable not found at:",
								pythonExecutablePath
							);
							return;
						}

						if (!fs.existsSync(scriptPath)) {
							console.error("Python script not found at:", scriptPath);
							return;
						}

						recordingProcess.stdout.on("data", (data) => {
							console.log("Python output:", data.toString());
						});

						// Add stderr handler
						recordingProcess.stderr.on("data", (data) => {
							console.error("Python error:", data.toString());
						});

						// Add exit handler
						recordingProcess.on("close", (code) => {
							console.log(`Python process exited with code ${code}`);
						});
					} catch (error) {
						vscode.window.showErrorMessage(
							`Recording failed: ${error.message}`
						);
					}
				}
			);
			context.subscriptions.push(recordingCommand);
		}
	} catch (error) {
		console.error("Extension activation failed:", error);
		vscode.window.showErrorMessage(
			`Extension activation failed: ${error.message}`
		);
	}
}

function deactivate() {
	if (recordingCommand) {
		recordingCommand.dispose();
		recordingCommand = undefined;
	}
	close_websocket();
	transcriptionServerScript.kill("SIGKILL");
}

module.exports = {
	activate,
	deactivate,
};
