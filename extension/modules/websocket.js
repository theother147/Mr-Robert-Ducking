// Description: Module for handling WebSocket communication
const vscode = require('vscode');
const WebSocket = require('ws');

class WebSocketManager {
    constructor() {
        this._ws = null;
        this._wsUrl = vscode.workspace.getConfiguration('rubberduck').get('webSocketUrl', 'ws://localhost:8765'); // Get WebSocket URL from the configuration (package.json)
        this._isConnecting = false; // Flag to indicate if WebSocket is connecting
        this._reconnectDelay = 5000; // Reconnect delay in milliseconds
        this._resendDelay = 1000; // Resend delay in milliseconds
        this._pendingMessage = null; // Pending message to be sent
        this._resendAttempt = 0; // Number of resend attempts
        this._maxResendAttempts = 2; // Maximum number of resend attempts
        this._provider = null; // Reference to webview provider
    }

    // Share webview provider with WebSocket module
    set_provider(provider) {
        this._provider = provider;
    }

    // Connect to WebSocket server
    connect() {
        if (this._isConnecting || (this._ws && this._ws.readyState === WebSocket.OPEN)) {
            return; // Do not connect if WebSocket is already connecting or connected
        }

        this._isConnecting = true; // Set the flag to indicate that the WebSocket is connecting
        this._ws = new WebSocket(this._wsUrl); // Create a new WebSocket instance
        this.event_handlers(); // Setup WebSocket event handlers
    }

    // Reconnect to WebSocket server
    reconnect() {
        setTimeout(() => {
            console.log('WebSocket: Reconnecting...');
            this._isConnecting = false; // Reset connecting flag
            this.connect();
        }, this._reconnectDelay); // Reconnect after a delay
    }

    // Notify webview about the connection status
    notify_webview(statusType, currentStatus, message = null) {
        if (this._provider && this._provider._view) {
            const payload = {
                command: statusType,
                status: currentStatus
            };
            if (statusType === "sendFailed") {
                payload.message = message;
            }
            this._provider._view.webview.postMessage(payload);
        }
    }

    // Resend pending messages
    resend_message() {
        if (this._resendAttempt < this._maxResendAttempts) {
            this._resendAttempt++; // Increment resend attempt counter
            setTimeout(() => {
                this.send_message(); // Resend the message
            }, this._resendDelay); // Resend after a delay
        } else {
            console.error('WebSocket: Maximum resend attempts reached. Message not sent.');
            this._resendAttempt = 0; // Reset resend attempt counter
            this.notify_webview("sendFailed", true, this._pendingMessage); // Notify webview about send failure
        }
    }

    // Send message to WebSocket server
    send_message(message) {
        // Store message on first attempt
        if (this._resendAttempt === 0 && message.retry !== true) {
            this._pendingMessage = {
                type: "text",
                message: message.text,
                context: message.context
            };
        }

        console.log(`WebSocket: Sending message (Attempt ${this._resendAttempt + 1}/${this._maxResendAttempts + 1}):`, this._pendingMessage);

        if (this._ws.readyState === WebSocket.OPEN) {
            try {
                this._ws.send(JSON.stringify(this._pendingMessage));
                console.log('WebSocket: Message sent:', this._pendingMessage);
                this._resendAttempt = 0; // Reset resend attempt counter
                this.notify_webview("sendSuccess", true);
            } catch (error) {
                console.error(`WebSocket: Failed to send message:`, error);
                this.resend_message();
            }
        } else {
            console.error('WebSocket: Not connected, message not sent');
            this.resend_message();
        }
    }
    
    // Handle WebSocket connection
    handle_connection() {
        console.log('WebSocket: Connected');
        this._isConnecting = false; // Reset connecting flag
        this.notify_webview("wsStatus", true); // Notify webview about connection status
    }

    // Handle WebSocket disconnection
    handle_disconnection() {
        console.log('WebSocket: Disconnected');
        this._isConnecting = false; // Reset connecting flag
        this.notify_webview("wsStatus", false); // Notify webview about connection status
        this.reconnect(); // Reconnect to WebSocket server
    }

    // Handle WebSocket connection error
    handle_error(error) {
        console.error('WebSocket error:', error);
    }

    // Handle incoming messages from the WebSocket server
    handle_message(data) {
        // Convert buffer to string
        const messageString = data.toString(); // Convert buffer to string
        const message = JSON.parse(messageString); // Try to parse the string as JSON
        console.log('WebSocket: Received message:', message);

        // Send to webview
        if (this._provider && this._provider._view) {
            console.log('WebSocket: Sending message to webview:', message.message);
            this._provider._view.webview.postMessage({
                command: 'receiveMessage',
                text: message.message
            });
        }
    }

    // Setup WebSocket event handlers
    event_handlers() {
        this._ws.on('open', async () => {
            this.handle_connection(); // Handle WebSocket connection
        });

        this._ws.on('close', () => {
            this.handle_disconnection(); // Handle WebSocket disconnection
        });

        this._ws.on('error', (error) => {
            this.handle_error(error); // Handle WebSocket connection error
        });

        this._ws.on('message', (data) => {
            this.handle_message(data); // Handle incoming messages from the WebSocket server
        });
    }


    // Close WebSocket connection
    close_connection() {
        if (this._ws) {
            this._ws.close();
        }
    }
}

module.exports = {
    WebSocketManager
};