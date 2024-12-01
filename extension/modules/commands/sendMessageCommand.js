const vscode = require("vscode");
const { send_message_to_websocket } = require("../websocket");

const send_message_to_ws = async (messageData, provider) => {
    try {
        console.log(
            "Extension received message:",
            JSON.stringify(messageData, null, 2)
        );
        // Pass forceRetry flag if this is a retry attempt
        const isRetry =
            messageData.command === "sendMessage" && messageData.isRetry;
        send_message_to_websocket(messageData, isRetry);
    } catch (error) {
        vscode.window.showErrorMessage(
            `Failed to send message: ${error.message}`
        );
        if (provider && provider._view) {
            provider._view.webview.postMessage({
                command: "sendFailed",
                text: messageData.text,
                originalMessage: messageData,
            });
        }
    }
}

module.exports = send_message_to_ws;