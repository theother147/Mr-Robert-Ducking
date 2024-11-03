const vscode = require('vscode');
const { receive_message_from_websocket } = require('../websocket');

class ViewProvider {
    constructor(context) {
        this.context = context;
        this._view = null;
    }

    resolveWebviewView(webviewView) {
        this._view = webviewView;
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: []
        };
        webviewView.webview.html = this._getWebviewContent();

        // Handle messages from the webview
        webviewView.webview.onDidReceiveMessage(
            message => {
                switch (message.command) {
                    case 'sendMessage':
                        vscode.commands.executeCommand('rubberduck.sendMessage', message.text);
                        break;
                }
            },
            undefined,
            this.context.subscriptions
        );

        // Handle messages from the WebSocket server
        const webSocketMessageHandler = (message) => {
            if (this._view?.webview) {
                this._view.webview.postMessage({
                    command: 'receiveMessage',
                    text: message,
                    sender: 'Server'
                });
            }
        };
        receive_message_from_websocket(webSocketMessageHandler);
    }

    _getWebviewContent() {
        return `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Rubber Duck AI Assistant</title>
                <style>
                    body {
                        display: flex;
                        flex-direction: column;
                        height: 100vh;
                        margin: 0;
                        padding: 0;
                    }
                    #chatHistory {
                        flex: 1;
                        overflow-y: auto;
                        padding: 10px;
                        word-wrap: break-word;
                    }
                    #chatHistory div {
                        margin-bottom: 8px;
                        padding: 6px;
                        border-radius: 4px;
                        background: var(--vscode-editor-background);
                    }
                    #inputContainer {
                        display: flex;
                        padding: 10px;
                        gap: 8px;
                        background: var(--vscode-editor-background);
                        border-top: 1px solid var(--vscode-panel-border);
                    }
                    #message {
                        flex: 1;
                        min-width: 0;
                        padding: 6px;
                        background: var(--vscode-input-background);
                        color: var(--vscode-input-foreground);
                        border: 1px solid var(--vscode-input-border);
                    }
                    #buttonContainer {
                        display: flex;
                        padding: 8px;
                        gap: 8px;
                        background: var(--vscode-editor-background);
                    }
                    .actionButton {
                        padding: 6px 12px;
                        background: var(--vscode-button-background);
                        color: var(--vscode-button-foreground);
                        border: none;
                        cursor: pointer;
                    }
                    .actionButton:hover {
                        background: var(--vscode-button-hoverBackground);
                    }
                </style>
            </head>
            <body>
                <div id="buttonContainer">
                    <button id="clearButton" class="actionButton">Clear Chat</button>
                </div>
                <div id="chatHistory"></div>
                <div id="inputContainer">
                    <input type="text" id="message" placeholder="Type a message...">
                    <button id="sendButton" class="actionButton">Send</button>
                </div>
                <script>
                    const vscode = acquireVsCodeApi();

                    function sendMessage() {
                        const messageInput = document.getElementById('message');
                        const message = messageInput.value.trim();
                        if (message) {
                            appendMessage('You', message);
                            vscode.postMessage({ command: 'sendMessage', text: message });
                            messageInput.value = '';
                        }
                    }

                    function appendMessage(sender, text) {
                        const chatHistory = document.getElementById('chatHistory');
                        const messageElement = document.createElement('div');
                        messageElement.textContent = \`\${sender}: \${text}\`;
                        chatHistory.appendChild(messageElement);
                        chatHistory.scrollTop = chatHistory.scrollHeight;
                    }

                    document.getElementById('sendButton').addEventListener('click', sendMessage);
                    document.getElementById('message').addEventListener('keydown', (event) => {
                        if (event.key === 'Enter') {
                            sendMessage();
                        }
                    });

                    document.getElementById('clearButton').addEventListener('click', () => {
                        document.getElementById('chatHistory').innerHTML = '';
                    });

                    window.addEventListener('message', event => {
                        const message = event.data;
                        if (message.command === 'receiveMessage') {
                            appendMessage(message.sender, message.text);
                        }
                    });
                </script>
            </body>
            </html>
        `;
    }
}

module.exports = {
    ViewProvider
};