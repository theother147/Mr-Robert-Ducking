// Description: Module for handling WebSocket communication

const vscode = require('vscode');
const WebSocket = require('ws');

let ws; // WebSocket instance
let isConnecting = false; // Flag to indicate if WebSocket is connecting
let provider; // Reference to webview provider

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

    // Websocket event handlers
    ws.on('open', function open() {
        console.log('Connected to WebSocket server');
        isConnecting = false;
        notify_connection_status(true);
    });

    ws.on('message', function message(data) {
        // Convert Buffer to string
        const messageString = data.toString();

        // Try to parse the string as JSON
        try {
            const message = JSON.parse(messageString);
            console.log('Received response from server:', message);
            
            // Send to webview
            if (provider && provider._view) {
                provider._view.webview.postMessage({
                    command: 'receiveMessage',
                    sender: 'Assistant',
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

// Send message to WebSocket server
function send_message_to_websocket(message) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        var messageData = {
            type: "text",
            message: message
        };
        ws.send(JSON.stringify(messageData));
    } else {
        console.error('WebSocket is not connected');
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
                        sender: 'Assistant',
                        text: parsedMessage.message
                    });
                }
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        });
    }
}

// Close the WebSocket connection
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