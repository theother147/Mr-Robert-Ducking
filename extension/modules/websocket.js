/**
 * WebSocket manager module for handling real-time communication.
 * Manages connection, reconnection, and message handling between the extension and server.
 */

const vscode = require("vscode");
const WebSocket = require("ws");
const marked = require('marked');

/**
 * WebSocketManager class handles all WebSocket-related operations
 * including connection management, message sending/receiving, and error handling.
 */
class WebSocketManager {
	constructor() {
		// WebSocket connection and configuration
		this._ws = null;
		this._wsUrl = vscode.workspace
			.getConfiguration("rubberduck")
			.get("webSocketUrl", "ws://localhost:8765");
		
		// Connection state management
		this._isConnecting = false;
		this._reconnectDelay = 5000;
		this._resendDelay = 1000;
		
		// Message handling state
		this._pendingMessage = null;
		this._resendAttempt = 0;
		this._maxResendAttempts = 2;
		
		// UI reference
		this._provider = null;
	}

	/**
	 * Sets the webview provider for UI updates
	 * @param {ViewProvider} provider - The webview provider instance
	 */
	setProvider(provider) {
		this._provider = provider;
	}

	/**
	 * Initiates WebSocket connection if not already connected
	 */
	connect() {
		if (
			this._isConnecting ||
			(this._ws && this._ws.readyState === WebSocket.OPEN)
		) {
			return;
		}

		this._isConnecting = true;
		this._ws = new WebSocket(this._wsUrl);
		this.eventHandlers();
	}

	/**
	 * Handles reconnection attempts with delay
	 */
	reconnect() {
		setTimeout(() => {
			console.log("WebSocket: Reconnecting...");
			this._isConnecting = false;
			this.connect();
		}, this._reconnectDelay);
	}

	/**
	 * Updates the webview with connection status
	 * @param {string} statusType - Type of status update
	 * @param {boolean} currentStatus - Current connection status
	 * @param {string} message - Optional status message
	 */
	notifyWebview(statusType, currentStatus, message = null) {
		if (this._provider && this._provider._view) {
			const payload = {
				command: statusType,
				status: currentStatus,
			};
			if (statusType === "sendFailed") {
				payload.message = message;
			}
			this._provider._view.webview.postMessage(payload);
		}
	}

	/**
	 * Attempts to resend failed messages
	 */
	resendMessage() {
		if (this._resendAttempt < this._maxResendAttempts) {
			this._resendAttempt++;
			setTimeout(() => {
				this.sendMessage();
			}, this._resendDelay);
		} else {
			console.error(
				"WebSocket: Maximum resend attempts reached. Message not sent."
			);
			this._resendAttempt = 0;
			this.notifyWebview("sendFailed", true, this._pendingMessage);
		}
	}

	/**
	 * Sends a message through the WebSocket connection
	 * @param {Object} message - Message to be sent
	 */
	sendMessage(message) {
		// Store new message or use pending message for retries
		if (this._resendAttempt === 0 && message.retry !== true) {
			this._pendingMessage = {
				type: "text",
				message: message.text,
				files: message.context ? [message.context] : [],
			};
		}

		console.log(
			`WebSocket: Sending message (Attempt ${this._resendAttempt + 1}/${
				this._maxResendAttempts + 1
			}):`,
			this._pendingMessage
		);

		if (this._ws.readyState === WebSocket.OPEN) {
			try {
				this._ws.send(JSON.stringify(this._pendingMessage));
				console.log("WebSocket: Message sent:", this._pendingMessage);
				this._resendAttempt = 0;
				this.notifyWebview("sendSuccess", true);
			} catch (error) {
				console.error(`WebSocket: Failed to send message:`, error);
				this.resendMessage();
			}
		} else {
			console.error("WebSocket: Not connected, message not sent");
			this.resendMessage();
		}
	}

	/**
	 * Handles successful WebSocket connection
	 */
	handleConnection() {
		console.log("WebSocket: Connected");
		this._isConnecting = false;
		this.notifyWebview("wsStatus", true);
	}

	/**
	 * Handles WebSocket disconnection and initiates reconnection
	 */
	handleDisconnection() {
		console.log("WebSocket: Disconnected");
		this._isConnecting = false;
		this.notifyWebview("wsStatus", false);
		this.reconnect();
	}

	/**
	 * Handles WebSocket errors
	 * @param {Error} error - The error object
	 */
	handleError(error) {
		console.error("WebSocket error:", error);
	}

	/**
	 * Processes incoming WebSocket messages
	 * @param {Buffer} data - Raw message data
	 */
	handleMessage(data) {
		const messageString = data.toString();
		const message = JSON.parse(messageString);
		console.log("WebSocket: Received message:", message);

		// Convert markdown content to HTML
		const htmlContent = marked.parse(message.message);

		// Forward to webview
		if (this._provider && this._provider._view) {
			console.log("WebSocket: Sending message to webview:", htmlContent);
			this._provider._view.webview.postMessage({
				command: "receiveMessage",
				text: htmlContent,
			});
		}
	}

	/**
	 * Sets up WebSocket event handlers
	 */
	eventHandlers() {
		this._ws.on("open", async () => {
			this.handleConnection();
		});

		this._ws.on("close", () => {
			this.handleDisconnection();
		});

		this._ws.on("error", (error) => {
			this.handleError(error);
		});

		this._ws.on("message", (data) => {
			this.handleMessage(data);
		});
	}

	/**
	 * Closes the WebSocket connection
	 */
	closeConnection() {
		if (this._ws) {
			this._ws.close();
		}
	}
}

module.exports = {
	WebSocketManager,
};
