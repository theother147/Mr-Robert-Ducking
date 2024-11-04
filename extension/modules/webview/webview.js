// Description: This module is responsible for creating the webview that will be displayed in the sidebar.

const vscode = require('vscode');
const path = require('path');
const fs = require('fs');
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
            localResourceRoots: [
                vscode.Uri.file(path.join(this.context.extensionPath, 'modules', 'webview'))
            ]
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
        // Read the HTML file for the webview
        const webviewPath = path.join(this.context.extensionPath, 'modules', 'webview', 'index.html');
        let html = fs.readFileSync(webviewPath, 'utf8');

        // Get the URIs for the scripts and styles
        const stylesUri = this._view.webview.asWebviewUri(vscode.Uri.file(
            path.join(this.context.extensionPath, 'modules', 'webview', 'styles.css')
        ));
        const scriptsUri = this._view.webview.asWebviewUri(vscode.Uri.file(
            path.join(this.context.extensionPath, 'modules', 'webview', 'scripts.js')
        ));

        // Replace placeholders in the HTML with the URIs
        html = html.replace('${scriptsUri}', scriptsUri.toString());
        html = html.replace('${stylesUri}', stylesUri.toString());

        return html;
    }
}

module.exports = {
    ViewProvider
};