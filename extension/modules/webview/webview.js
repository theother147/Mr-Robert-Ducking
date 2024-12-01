// Description: Webview provider for the extension
const vscode = require('vscode');
const path = require('path');
const fs = require('fs');

class ViewProvider {
    constructor(context) {
        this.context = context;
        this._view = null;
    }

    // Create the webview view
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
        webviewView.webview.html = this.get_html_for_webview();

        // Handle messages from the webview
        webviewView.webview.onDidReceiveMessage(message => {
            switch (message.command) {
                case 'sendMessage':
                    vscode.commands.executeCommand('rubberduck.sendMessage', message);
                    break;
                case 'startRecording':
                    vscode.commands.executeCommand('rubberduck.startRecording');
                    break;
                case 'selectFile':
                    vscode.commands.executeCommand('rubberduck.selectFile');
                    break;
            }
        },
        undefined,
        this.context.subscriptions
        );
    }

    // HTML content for the webview
    get_html_for_webview() {
        const webviewPath = path.join(this.context.extensionPath, 'modules', 'webview', 'index.html');
        let html = fs.readFileSync(webviewPath, 'utf8');

        // Get URIs for scripts and styles
        const stylesUri = this._view.webview.asWebviewUri(vscode.Uri.file(
            path.join(this.context.extensionPath, 'modules', 'webview', 'styles.css')
        ));
        const scriptsUri = this._view.webview.asWebviewUri(vscode.Uri.file(
            path.join(this.context.extensionPath, 'modules', 'webview', 'scripts.js')
        ));
        const attachIconUri = this._view.webview.asWebviewUri(vscode.Uri.file(
            path.join(this.context.extensionPath, 'resources', 'attach.svg')
        ));

        // Replace placeholders
        html = html.replace('${scriptsUri}', scriptsUri.toString());
        html = html.replace('${stylesUri}', stylesUri.toString());
        html = html.replace('${attachIconUri}', attachIconUri.toString());

        return html;
    }
}

module.exports = {
    ViewProvider
};