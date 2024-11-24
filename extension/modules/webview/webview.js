// Description: Webview provider for the extension
const vscode = require('vscode');
const path = require('path');
const fs = require('fs');
const { receive_message_from_websocket } = require('../websocket');

class ViewProvider {
    constructor(context) {
        this.context = context;
        this._view = null;
    }

    // Create the webview
    resolveWebviewView(webviewView) {
        this._view = webviewView;

        // Set webview options
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [
                vscode.Uri.file(path.join(this.context.extensionPath, 'modules', 'webview'))
            ]
        };

        // Load webview HTML content
        webviewView.webview.html = this._get_webview_content();

        // Handle messages from webview
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

    // HTML content for the webview
    _get_webview_content() {
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