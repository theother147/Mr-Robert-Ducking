const vscode = require('vscode');
const { connect_websocket, close_websocket, send_message_to_websocket } = require('./modules/websocket');
const { ViewProvider } = require('./modules/webview/webview');

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    // Connect to WebSocket server
    connect_websocket();

    // Register the view provider
    const provider = new ViewProvider(context);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider('rubberduck.view', provider)
    );

    // Register the sendMessage command
    context.subscriptions.push(
        vscode.commands.registerCommand('rubberduck.sendMessage', (message) => {
            send_message_to_websocket(message);
        })
    );
}

function deactivate() {
    // Close the WebSocket connection
    close_websocket();
}

module.exports = {
    activate,
    deactivate
};