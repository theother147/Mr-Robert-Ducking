// Description: Module for handling WebSocket communication
const vscode = require("vscode");
const WebSocket = require("ws");
const marked = require('marked');

class WhisperliveWebSocketManager {
	constructor() {
		this._ws = null;
		this._wsUrl = vscode.workspace
			.getConfiguration("rubberduck")
			.get("webSocketUrl", "ws://localhost:8766"); // Get WebSocket URL from the configuration (package.json)
		this._isConnecting = false; // Flag to indicate if WebSocket is connecting
		this._reconnectDelay = 5000; // Reconnect delay in milliseconds
		this._resendDelay = 1000; // Resend delay in milliseconds
		this._pendingMessage = null; // Pending message to be sent
		this._resendAttempt = 0; // Number of resend attempts
		this._maxResendAttempts = 2; // Maximum number of resend attempts
		this._provider = null; // Reference to webview provider
	}

	// Share webview provider with WebSocket module
	setProvider(provider) {
		this._provider = provider;
	}

	// Connect to WebSocket server
	connect() {
		if (
			this._isConnecting ||
			(this._ws && this._ws.readyState === WebSocket.OPEN)
		) {
			return; // Do not connect if WebSocket is already connecting or connected
		}

		this._isConnecting = true; // Set the flag to indicate that the WebSocket is connecting
		this._ws = new WebSocket(this._wsUrl); // Create a new WebSocket instance
		this.eventHandlers(); // Setup WebSocket event handlers
	}

	// Reconnect to WebSocket server
	reconnect() {
		setTimeout(() => {
			console.log("WebSocket: Reconnecting...");
			this._isConnecting = false; // Reset connecting flag
			this.connect();
		}, this._reconnectDelay); // Reconnect after a delay
	}

	// Handle WebSocket connection
	handleConnection() {
		console.log("WebSocket: Connected");
		this._isConnecting = false; // Reset connecting flag
	}

	// Handle WebSocket disconnection
	handleDisconnection() {
		console.log("WebSocket: Disconnected");
		this._isConnecting = false; // Reset connecting flag
		this.reconnect(); // Reconnect to WebSocket server
	}

	// Handle WebSocket connection error
	handleError(error) {
		console.error("WebSocket error:", error);
	}

	sendMessage(message) {
		// Store message on first attempt
		if (this._ws.readyState === WebSocket.OPEN) {
			try {
				this._ws.send(JSON.stringify(message));
				console.log("WebSocket: Message sent:", message);
			} catch (error) {
				console.error(`WebSocket: Failed to send message:`, error);
			}
		} else {
			console.error("WebSocket: Not connected, message not sent");
		}
	}

	// Handle incoming messages from the WebSocket server
	handleMessage(data) {
		// Convert buffer to string
		const messageString = data.toString(); // Convert buffer to string
		const message = JSON.parse(messageString); // Try to parse the string as JSON
		console.log("WebSocket: Received message:", message);

		// Convert markdown to HTML
		// const htmlContent = marked.parse(message.message);

		// Send to webview
		if (this._provider && this._provider._view) {
			console.log("WebSocket: Sending message to webview:", message);
			this._provider._view.webview.postMessage({
				command: "transcription",
				text: message,
			});
		}
	}

	// Setup WebSocket event handlers
	eventHandlers() {
		this._ws.on("open", async () => {
			this.handleConnection(); // Handle WebSocket connection
		});

		this._ws.on("close", () => {
			this.handleDisconnection(); // Handle WebSocket disconnection
		});

		this._ws.on("error", (error) => {
			this.handleError(error); // Handle WebSocket connection error
		});

		this._ws.on("message", (data) => {
			this.handleMessage(data); // Handle incoming messages from the WebSocket server
		});
	}

	// Close WebSocket connection
	closeConnection() {
		if (this._ws) {
			this._ws.close();
		}
	}
}

module.exports = {
	WhisperliveWebSocketManager,
};
