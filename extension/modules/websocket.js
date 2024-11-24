// Description: Module for handling WebSocket communication

const vscode = require('vscode');
const WebSocket = require('ws');

let ws; // WebSocket instance
let isConnecting = false; // Flag to indicate if WebSocket is connecting
let provider; // Reference to webview provider
let messageQueue = []; // Queue for messages that failed to send
const MAX_RETRIES = 2; // Maximum number of retries for sending messages

// Get WebSocket URL from the configuration (package.json)
const wsUrl = vscode.workspace.getConfiguration('rubberduck').get('webSocketUrl', 'ws://localhost:8765');

// Share webview provider with WebSocket module
function set_provider(viewProvider) {
    provider = viewProvider;
}

// Notify webview about the connection status
function notify_connection_status(connected) {
    if (provider && provider._view) {
        provider._view.webview.postMessage({
            command: 'wsStatus',
            connected: connected
        });
    }
}

// WebSocket connection and event handlers
function connect_websocket() {

    // Check if WebSocket is already connected
    if (isConnecting || (ws && ws.readyState === WebSocket.OPEN)) {
        return; // Prevent multiple connections
    }

    isConnecting = true; // Set the flag to indicate that the WebSocket is connecting
    ws = new WebSocket(wsUrl); // Create a new WebSocket instance

    // WebSocket event handlers
    ws.on('open', async function open() {
        console.log('Connected to WebSocket server');
        isConnecting = false;
        notify_connection_status(true);

        // Attempt to send any queued messages
        messageQueue.forEach(async (queuedMessage) => {
            await send_message_to_websocket(queuedMessage.text);
        });
    });

    // Handle incoming messages from the WebSocket server
    ws.on('message', function message(data) {
        // Convert buffer to string
        const messageString = data.toString();

        // Try to parse the string as JSON
        try {
            const message = JSON.parse(messageString);
            console.log('Received response from server:', message);
            
            // Send to webview
            if (provider && provider._view) {
                provider._view.webview.postMessage({
                    command: 'receiveMessage',
                    sender: 'Rubber Duck',
                    text: message.message
                });
            }
        } catch (error) {
            console.error('Failed to parse message as JSON:', error);
        }
    });

    ws.on('close', function close() {
        console.log('WebSocket connection closed');
        isConnecting = false;
        notify_connection_status(false);
        reconnect_websocket();
    });

    ws.on('error', function error(error) {
        console.error('WebSocket error:', error);
        isConnecting = false;
        notify_connection_status(false);
        reconnect_websocket();
    });
}

// Reconnect to WebSocket server
function reconnect_websocket() {
    setTimeout(() => {
        console.log('Reconnecting to WebSocket server...');
        connect_websocket();
    }, 5000); // Reconnect after 5 seconds
}

// Handle message sending with retries
async function send_message_retry(messageData, retryCount = 0) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        try {
            ws.send(JSON.stringify(messageData));
            // If message sent successfully, remove from queue
            messageQueue = messageQueue.filter(m => m.text !== messageData.message);
            return true;
        } catch (error) {
            console.error('Failed to send message:', error);
        }
    }

    // Use message queue if there are more retries left
    if (retryCount < MAX_RETRIES) {
        console.log(`Retry attempt ${retryCount + 1} for message: ${messageData.message}`);
        await new Promise(resolve => setTimeout(resolve, 2000));
        return send_message_retry(messageData, retryCount + 1);
    }

    // Clear message from queue when there are no retries left
    messageQueue = messageQueue.filter(m => m.text !== messageData.message);
    return false;
}

// Send message to WebSocket server
async function send_message_to_websocket(message) {
    const messageData = {
        type: "text",
        message: message
    };

    // Check if message is already in queue
    if (!messageQueue.find(m => m.text === message)) {
        messageQueue.push({text: message, attempts: 0});
    }

    const success = await send_message_retry(messageData);
    
    if (!success) {
        // If all retries failed, notify the webview
        if (provider && provider._view) {
            provider._view.webview.postMessage({
                command: 'sendFailed',
                text: message
            });
        }
        console.error('Failed to send message after retries');
    }
}

// Receive message from WebSocket server
function receive_message_from_websocket(messageHandler) {
    if (ws) {
        ws.on('message', function message(response) {
            try {
                const parsedMessage = JSON.parse(response);
                // Send to webview via provider
                if (provider && provider._view) {
                    provider._view.webview.postMessage({
                        command: 'receiveMessage',
                        sender: 'Rubber Duck',
                        text: parsedMessage.message
                    });
                }
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        });
    }
}

// Close WebSocket connection
function close_websocket() {
    if (ws) {
        ws.close();
    }
}

module.exports = {
    connect_websocket,
    close_websocket,
    send_message_to_websocket,
    receive_message_from_websocket,
    set_provider
};