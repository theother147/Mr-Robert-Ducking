// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
const vscode = require('vscode');
const WebSocket = require('ws'); // Import the ws library
var ws;

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    console.log('Machine ID:', vscode.env.machineId);
    ws = new WebSocket('ws://localhost:8765'); // Get WebSocket server

    // Create a status bar item that will be displayed immediately when the extension is activated
    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right);
    statusBarItem.text = '$(chat-editor-label-icon) Rubber Duck';  // Display text and icon
    statusBarItem.command = 'rubberduck.openWebview';  // Command to be executed when the item is clicked
    statusBarItem.show();  // Make sure to show the item
    context.subscriptions.push(statusBarItem);  // Add to the subscription

    // Command to open the Webview panel when the status bar item is clicked
    const webView = vscode.commands.registerCommand('rubberduck.openWebview', function () {
        console.log('Start Rubber Duck');
        createWebviewPanel(context);
    });
    context.subscriptions.push(webView);  // Add to the subscription

    const sendMessage = vscode.commands.registerCommand('rubberduck.sendMessage', function (message) {
        console.log(message);
        sendMessageToWebSocket(message, ws);
    });
    context.subscriptions.push(sendMessage);  // Add to the subscription

}


// Function to send a message to the WebSocket server
function sendMessageToWebSocket(message, ws) {
    var messageData = {
        type: "text",
        message: message
    };

    ws.send(JSON.stringify(messageData)); // Send the message to WebSocket server

    // Listen for messages (including the acknowledgment response) from the server
    ws.on('message', function message(response) {
        vscode.window.showInformationMessage(`Received response from server: ${response}`);
    });
    
    ws.on('error', function error(error) {
        vscode.window.showErrorMessage(`WebSocket error: ${error}`);
    });
}

// Function to create the Webview Panel
function createWebviewPanel(context) {
    const panel = vscode.window.createWebviewPanel(
        'rubberDuckPanel',  // Identify the type of the webview
        'Rubber Duck AI Assistant',  // Title of the panel/tab
        vscode.ViewColumn.Beside,  // Show panel beside the code editor
        {
            enableScripts: true  // Allows JS to run in the Webview
        }
    );

    // HTML content for the Webview Panel
    panel.webview.html = getWebviewContent();

    // Handle messages from the Webview
    panel.webview.onDidReceiveMessage(
        message => {
            switch (message.command) {
                case 'sendMessage':
                    //sendMessageToWebSocket(message.text);
                    vscode.commands.executeCommand('rubberduck.sendMessage', message.text);
                    break;
            }
        },
        undefined,
        context.subscriptions
    );
}

// HTML content of the Webview Panel
function getWebviewContent() {
    return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Rubber Duck AI Assistant</title>
        </head>
        <body>
            <input type="text" id="message" placeholder="Message">
            <button id="sendButton">Send message</button>

            <script>
                const vscode = acquireVsCodeApi();  // Acquire the VS Code API for communication

                // Add event listener for the button
                document.getElementById('sendButton').addEventListener('click', () => {
                    const message = document.getElementById('message').value;  // Get the input value
                    vscode.postMessage({ command: 'sendMessage', text: message });  // Send message to extension
                });
            </script>
        </body>
        </html>
    `;
}

// This method is called when your extension is deactivated
function deactivate() {}

module.exports = {
	activate,
	deactivate
}