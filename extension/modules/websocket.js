const vscode = require('vscode');
const WebSocket = require('ws');

let ws;
let isConnecting = false; // Flag to track connection status

// Get the WebSocket URL from the configuration
const wsUrl = vscode.workspace.getConfiguration('rubberduck').get('webSocketUrl', 'ws://localhost:8765');

// Connect to the WebSocket server
function connect_websocket() {

    // Check if WebSocket is already connected
    if (isConnecting || (ws && ws.readyState === WebSocket.OPEN)) {
        return; // Prevent multiple connections
    }

    // Set the flag to indicate that the WebSocket is connecting
    isConnecting = true;
    ws = new WebSocket(wsUrl);

    // WebSocket event listeners
    // Handle WebSocket connection open
    ws.on('open', function open() {
        console.log('Connected to WebSocket server');
        isConnecting = false;
    });

    // Handle WebSocket connection close
    ws.on('close', function close() {
        console.log('WebSocket connection closed');
        isConnecting = false;
        reconnect_websocket();
    });

    // Handle messages from the WebSocket server
    ws.on('message', function message(data) {
        // Convert Buffer to string
        const messageString = data.toString();

        // Try to parse the string as JSON
        let message;
        try {
            message = JSON.parse(messageString);
        } catch (error) {
            console.error('Failed to parse message as JSON:', error);
            message = messageString; // Fallback to raw string if parsing fails
        }

        // Log the actual message
        console.log('Received response from server:', message);
    });

    // Handle WebSocket errors
    ws.on('error', function error(error) {
        console.error('WebSocket error:', error);
        isConnecting = false;
        reconnect_websocket(); // Reconnect to WebSocket server
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
                messageHandler(parsedMessage.message);
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
    receive_message_from_websocket
};