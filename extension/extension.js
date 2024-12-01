const  recording  = require("./modules/commands/recordingCommand");
const vscode = require("vscode");
const { exec } = require("child_process");
const {
	connect_websocket,
	close_websocket,
	send_message_to_websocket,
	set_provider,
} = require("./modules/websocket");
const { ViewProvider } = require("./modules/webview/webview");
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

let provider;
let recordingCommand;
// const pythonExecutablePath = path.join(
// 	__dirname,
// 	"python",
// 	".venv",
// 	"Scripts",
// 	"python.exe"
// );
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

		provider = new ViewProvider(context); // Initialize webview provider
		set_provider(provider); // Share provider with WebSocket module
		connect_websocket(); // Connect to WebSocket server

		// Register the webview provider to create UI
		context.subscriptions.push(
			vscode.window.registerWebviewViewProvider("rubberduck.view", provider)
		);

		// Register command to send messages to WebSocket server
		let sendMessageCommand = vscode.commands.registerCommand(
			"rubberduck.sendMessage",
			(messageData) => {
				try {
					console.log(
						"Extension received message:",
						JSON.stringify(messageData, null, 2)
					);
					// Pass forceRetry flag if this is a retry attempt
					const isRetry =
						messageData.command === "sendMessage" && messageData.isRetry;
					send_message_to_websocket(messageData, isRetry);
				} catch (error) {
					vscode.window.showErrorMessage(
						`Failed to send message: ${error.message}`
					);
					if (provider && provider._view) {
						provider._view.webview.postMessage({
							command: "sendFailed",
							text: messageData.text,
							originalMessage: messageData,
						});
					}
				}
			}
		);
		context.subscriptions.push(sendMessageCommand);

		// Only register command if not already registered
		if (!recordingCommand) {
			recordingCommand = vscode.commands.registerCommand(
				"rubberduck.startRecording",
				recording
			);
			context.subscriptions.push(recordingCommand);
		}

		// Register command to select and read file
		let selectFileCommand = vscode.commands.registerCommand(
			"rubberduck.selectFile",
			async () => {
				try {
					if (!vscode.workspace.workspaceFolders) {
						throw new Error("No workspace folder open");
					}

					// Get all files in workspace
					const files = await vscode.workspace.findFiles(
						"**/*",
						"**/node_modules/**"
					);
					const fileItems = files.map((file) => ({
						label: vscode.workspace.asRelativePath(file),
						uri: file,
						type: "file",
					}));

					// Add text selection option if there is selected text
					const editor = vscode.window.activeTextEditor;
					const selection = editor?.selection;
					const selectedText = editor?.document.getText(selection);

					let items = [
						...(selectedText
							? [
									{
										label: "Selected Text",
										description:
											selectedText.length > 50
												? selectedText.substring(0, 50) + "..."
												: selectedText,
										type: "selection",
										text: selectedText,
									},
							  ]
							: []),
						...fileItems,
					];

					// Show quick pick with both options
					const selected = await vscode.window.showQuickPick(items, {
						placeHolder: "Select content to attach",
					});

					if (selected) {
						if (selected.type === "selection") {
							// Handle text selection
							if (provider && provider._view) {
								provider._view.webview.postMessage({
									command: "fileContent",
									type: "selection",
									content: selected.text, // text is available on selection items
									label: "Text selection",
								});
							}
						} else if (selected.type === "file") {
							// Get current document if it matches the selected file
							const activeDocuments = vscode.workspace.textDocuments;
							const selectedDoc = activeDocuments.find(
								(doc) => doc.uri.fsPath === selected.uri.fsPath
							);

							// Use current document content if available, otherwise read from disk
							const text = selectedDoc
								? selectedDoc.getText()
								: new TextDecoder().decode(
										await vscode.workspace.fs.readFile(selected.uri)
								  );

							if (provider && provider._view) {
								provider._view.webview.postMessage({
									command: "fileContent",
									type: "file",
									content: text,
									label: `File: ${selected.label}`,
								});
							}
						}
					}
				} catch (error) {
					vscode.window.showErrorMessage(
						`Failed to read content: ${error.message}`
					);
				}
			}
		);
		context.subscriptions.push(selectFileCommand);

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
							"Scripts",
							"python"
						);

						const scriptPath = path.join(
							__dirname,
							"python",
							"transcribe_audio.py"
						);

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
