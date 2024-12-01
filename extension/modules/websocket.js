// Description: Module for handling WebSocket communication

const vscode = require('vscode');
const WebSocket = require('ws');

let ws; // WebSocket instance
let isConnecting = false; // Flag to indicate if WebSocket is connecting
let provider; // Reference to webview provider
let messageQueue = []; // Queue for messages
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

        // Only retry messages that haven't exhausted their retries
        const pendingMessages = messageQueue.filter(msg => !msg.retriesExhausted);
        for (const msg of pendingMessages) {
            await send_message_to_websocket({
                text: msg.text,
                context: msg.context
            });
        }
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
    // Notify webview about retry attempt starting
    if (provider && provider._view) {
        provider._view.webview.postMessage({
            command: 'retryStatus',
            retrying: true,
            attempt: retryCount + 1
        });
    }

    const queueItem = messageQueue.find(m => m.text === messageData.message);
    
    if (!queueItem || queueItem.retriesExhausted || queueItem.sentSuccessfully) {
        // Notify webview about completion
        if (provider && provider._view) {
            provider._view.webview.postMessage({
                command: 'retryStatus',
                retrying: false
            });
        }
        return queueItem?.sentSuccessfully || false;
    }

    console.log(`Attempt ${retryCount + 1}/${MAX_RETRIES + 1} to send message:`, JSON.stringify(messageData, null, 2));

    if (ws?.readyState === WebSocket.OPEN) {
        try {
            ws.send(JSON.stringify(messageData));
            console.log('Message sent successfully:', JSON.stringify(messageData, null, 2));
            queueItem.sentSuccessfully = true;
            // Return immediately after successful send - no more retries needed
            return true;
        } catch (error) {
            console.error(`Send attempt ${retryCount + 1} failed:`, error);
        }
    }

    if (retryCount >= MAX_RETRIES) {
        console.log('Max retries reached, marking as exhausted');
        queueItem.retriesExhausted = true;
        return false;
    }

    const delay = 2000;
    await new Promise(resolve => setTimeout(resolve, delay));
    return send_message_retry(messageData, retryCount + 1);
}

// Send message to WebSocket server
async function send_message_to_websocket(message, forceRetry = false) {
    if (!message || !message.text) {
        console.warn('Invalid message:', message);
        return;
    }

    console.log('WebSocket preparing to send:', message);
    const messageData = {
        type: "text",
        message: message.text,
        context: message.context
    };

    // For manual retries, reset the exhausted state if it exists
    if (forceRetry) {
        const existingMessage = messageQueue.find(m => m.text === message.text);
        if (existingMessage) {
            existingMessage.retriesExhausted = false;
            existingMessage.attempts = 0;
            existingMessage.sentSuccessfully = false;
        }
    }

    // Add to queue if not already present
    if (!messageQueue.some(m => m.text === message.text)) {
        messageQueue.push({
            text: message.text,
            context: message.context,
            attempts: 0,
            retriesExhausted: false,
            sentSuccessfully: false
        });
    }

    const success = await send_message_retry(messageData);
    const queueItem = messageQueue.find(m => m.text === message.text);

    if (success && provider?._view) {
        provider._view.webview.postMessage({
            command: 'sendSuccess',
            text: message.text
        });
    } else if (queueItem && queueItem.retriesExhausted && !queueItem.sentSuccessfully && provider?._view) {
        provider._view.webview.postMessage({
            command: 'sendFailed',
            text: message.text,
            originalMessage: message,
            isLastRetry: true
        });
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