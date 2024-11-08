// Description: Webview provider for the rubber duck assistant
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
                    case 'startRecording':
                        vscode.commands.executeCommand('rubberduck.startRecording');
                        break;
                }
            },
            undefined,
            this.context.subscriptions
        );
    }

    _getWebviewContent() {
        const webviewPath = path.join(this.context.extensionPath, 'modules', 'webview', 'index.html');
        let html = fs.readFileSync(webviewPath, 'utf8');

        // Get URIs for scripts and styles
        const stylesUri = this._view.webview.asWebviewUri(vscode.Uri.file(
            path.join(this.context.extensionPath, 'modules', 'webview', 'styles.css')
        ));
        const scriptsUri = this._view.webview.asWebviewUri(vscode.Uri.file(
            path.join(this.context.extensionPath, 'modules', 'webview', 'scripts.js')
        ));

        // Replace placeholders
        html = html.replace('${scriptsUri}', scriptsUri.toString());
        html = html.replace('${stylesUri}', stylesUri.toString());

        return html;
    }
}

module.exports = {
    ViewProvider
};