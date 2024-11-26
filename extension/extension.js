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
        provider = new ViewProvider(context); // Initialize webview provider
        set_provider(provider); // Share provider with WebSocket module
        connect_websocket(); // Connect to WebSocket server

        // Register the webview provider to create UI
        context.subscriptions.push(
            vscode.window.registerWebviewViewProvider('rubberduck.view', provider)
        );

        // Register command to send messages to WebSocket server
        let sendMessageCommand = vscode.commands.registerCommand('rubberduck.sendMessage', (messageData) => {
            try {
                console.log('Extension received message:', JSON.stringify(messageData, null, 2));
                // Pass forceRetry flag if this is a retry attempt
                const isRetry = messageData.command === 'sendMessage' && messageData.isRetry;
                send_message_to_websocket(messageData, isRetry);
            } catch (error) {
                vscode.window.showErrorMessage(`Failed to send message: ${error.message}`);
                if (provider && provider._view) {
                    provider._view.webview.postMessage({
                        command: 'sendFailed',
                        text: messageData.text,
                        originalMessage: messageData
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

        // Register command to select and read file
        let selectFileCommand = vscode.commands.registerCommand('rubberduck.selectFile', async () => {
            try {
                if (!vscode.workspace.workspaceFolders) {
                    throw new Error('No workspace folder open');
                }

                // Get all files in workspace
                const files = await vscode.workspace.findFiles('**/*', '**/node_modules/**');
                const fileItems = files.map(file => ({
                    label: vscode.workspace.asRelativePath(file),
                    uri: file,
                    type: 'file'
                }));

                // Add text selection option if there is selected text
                const editor = vscode.window.activeTextEditor;
                const selection = editor?.selection;
                const selectedText = editor?.document.getText(selection);
                
                let items = [
                    ...(selectedText ? [{
                        label: "Selected Text",
                        description: selectedText.length > 50 ? selectedText.substring(0, 50) + '...' : selectedText,
                        type: 'selection',
                        text: selectedText
                    }] : []),
                    ...fileItems
                ];

                // Show quick pick with both options
                const selected = await vscode.window.showQuickPick(items, {
                    placeHolder: 'Select content to attach'
                });

                if (selected) {
                    if (selected.type === 'selection') {
                        // Handle text selection
                        if (provider && provider._view) {
                            provider._view.webview.postMessage({
                                command: 'fileContent',
                                type: 'selection',
                                content: selected.text, // text is available on selection items
                                label: 'Text selection'
                            });
                        }
                    } else if (selected.type === 'file') {
                        // Get current document if it matches the selected file
                        const activeDocuments = vscode.workspace.textDocuments;
                        const selectedDoc = activeDocuments.find(doc => 
                            doc.uri.fsPath === selected.uri.fsPath
                        );

                        // Use current document content if available, otherwise read from disk
                        const text = selectedDoc 
                            ? selectedDoc.getText()
                            : new TextDecoder().decode(await vscode.workspace.fs.readFile(selected.uri));
                        
                        if (provider && provider._view) {
                            provider._view.webview.postMessage({
                                command: 'fileContent',
                                type: 'file',
                                content: text,
                                label: `File: ${selected.label}`
                            });
                        }
                    }
                }
            } catch (error) {
                vscode.window.showErrorMessage(`Failed to read content: ${error.message}`);
            }
        });
        context.subscriptions.push(selectFileCommand);

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