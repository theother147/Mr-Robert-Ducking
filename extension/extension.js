const vscode = require('vscode');
const { exec } = require("child_process");
const { connect_websocket, close_websocket, send_message_to_websocket } = require('./modules/websocket');
const { ViewProvider } = require('./modules/webview/webview');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');


let provider;
let recordingCommand;

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    try {
        // Connect to WebSocket server
        connect_websocket();

        // Register the view provider
        provider = new ViewProvider(context);
        context.subscriptions.push(
            vscode.window.registerWebviewViewProvider('rubberduck.view', provider)
        );

        // Only register command if not already registered
        if (!recordingCommand) {
            recordingCommand = vscode.commands.registerCommand('rubberduck.startRecording', async () => {
                try {
									// const workspaceFolders = vscode.workspace.workspaceFolders;
									// if (!workspaceFolders || workspaceFolders.length === 0) {
									//     vscode.window.showErrorMessage('No workspace folder is open.');
									//     return;
									// }
									// const workspaceFolder = workspaceFolders[0].uri.fsPath;
									// const venvPath = path.join(workspaceFolder, 'venv', 'bin', 'python');
									// const pythonPath = fs.existsSync(venvPath) ? venvPath : (vscode.workspace.getConfiguration('python').get('pythonPath') || 'python');
									// const scriptPath = path.join(context.extensionPath, 'python', 'main.py');
									// const recordingProcess = spawn(pythonPath, [scriptPath]);

									const venvPath = "python/.venv";
									const command =
										`${venvPath}/bin/python script.py` ||
										`${venvPath}\\Scripts\\python script.py`;

									exec(command, (error, stdout, stderr) => {
										if (error) {
											console.error(`Error: ${error.message}`);
											return;
										}
										if (stderr) {
											console.error(`Stderr: ${stderr}`);
											return;
										}
										console.log(`Output: ${stdout}`);
									});

                    const pythonExecutable = "path_to_venv/bin/python" || 'path_to_venv\\Scripts\\python'; 
                    
                    const pythonProcess = spawn(pythonExecutable);

									recordingProcess.stdout.on("data", (data) => {
										try {
											const messages = data.toString().trim().split("\n");
											messages.forEach((msg) => {
												const parsed = JSON.parse(msg);
												if (parsed.status === "recording") {
													provider._view.webview.postMessage({
														command: "voiceActivity",
														isSpeaking: parsed.is_speech,
													});
												}
											});
										} catch (error) {
											console.error("Error parsing recording output:", error);
										}
									});

									recordingProcess.on("error", (error) => {
										vscode.window.showErrorMessage(
											`Recording failed: ${error.message}`
										);
									});
								} catch (error) {
                    vscode.window.showErrorMessage(`Recording failed: ${error.message}`);
                }
            });
            context.subscriptions.push(recordingCommand);
        }

    } catch (error) {
        console.error('Extension activation failed:', error);
        vscode.window.showErrorMessage(`Extension activation failed: ${error.message}`);
    }
}

function deactivate() {
    if (recordingCommand) {
        recordingCommand.dispose();
        recordingCommand = undefined;
    }
    close_websocket();
}

module.exports = {
    activate,
    deactivate
};