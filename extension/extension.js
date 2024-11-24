const vscode = require('vscode');
const { connect_websocket, close_websocket, send_message_to_websocket, set_provider } = require('./modules/websocket');
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
        provider = new ViewProvider(context); // Initialize  webview provider
        set_provider(provider); // Share provider with WebSocket module
        connect_websocket(); // Connect to WebSocket server

        // Register the webview provider to create UI
        context.subscriptions.push(
            vscode.window.registerWebviewViewProvider('rubberduck.view', provider)
        );

        // Register command to send messages to WebSocket server
        let sendMessageCommand = vscode.commands.registerCommand('rubberduck.sendMessage', (text) => {
            try {
                send_message_to_websocket(text);
                // Response is handled by receive_message_from_websocket
            } catch (error) {
                // Show error message in case of failure
                vscode.window.showErrorMessage(`Failed to send message: ${error.message}`);
                if (provider && provider._view) {
                    provider._view.webview.postMessage({
                        command: 'sendFailed',
                        text: text
                    });
                }
            }
        });
        context.subscriptions.push(sendMessageCommand);

        // Register recording command (existing code)
        if (!recordingCommand) {
            recordingCommand = vscode.commands.registerCommand('rubberduck.startRecording', async () => {
                try {
                    const workspaceFolder = vscode.workspace.workspaceFolders[0].uri.fsPath;
                    const venvPath = path.join(workspaceFolder, 'venv', 'bin', 'python');
                    const pythonPath = fs.existsSync(venvPath) ? venvPath : (vscode.workspace.getConfiguration('python').get('pythonPath') || 'python');
                    const scriptPath = path.join(context.extensionPath, 'python', 'main.py');
                    const recordingProcess = spawn(pythonPath, [scriptPath]);
                    
                    recordingProcess.stdout.on('data', (data) => {
                        try {
                            const messages = data.toString().trim().split('\n');
                            messages.forEach(msg => {
                                const parsed = JSON.parse(msg);
                                if (parsed.status === 'recording') {
                                    provider._view.webview.postMessage({
                                        command: 'voiceActivity',
                                        isSpeaking: parsed.is_speech
                                    });
                                }
                            });
                        } catch (error) {
                            console.error('Error parsing recording output:', error);
                        }
                    });
                    
                    recordingProcess.on('error', (error) => {
                        vscode.window.showErrorMessage(`Recording failed: ${error.message}`);
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