const vscode = require("vscode");

const send_message_to_ws = async (messageData, wsManager, provider) => {
    try {
        console.log('Extension received message:', JSON.stringify(messageData, null, 2));
        wsManager.send_message(messageData);
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to send message: ${error.message}`);
        if (provider && provider._view) {
            provider._view.webview.postMessage({
                command: 'sendFailed',
                text: messageData.text,
            });
        }
    }
}

module.exports = send_message_to_ws;