// Description: Module for handling WebSocket communication
const vscode = require("vscode");
const WebSocket = require("ws");
const marked = require('marked');
const getRecordingStatus = require("./commands/transcribeCommand");

class WhisperliveWebSocketManager {
	constructor() {
		this._ws = null;
		this._wsUrl = vscode.workspace
			.getConfiguration("rubberduck")
			.get("wslUrl", "ws://localhost:8766");
		this._isConnecting = false;
		this._reconnectDelay = 5000;
		this._provider = null;
		this._currentSessionId = null;  // Track current recording session
		console.log("WhisperLive WebSocket: Initialized");
	}

	setProvider(provider) {
		this._provider = provider;
	}

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

	reconnect() {
		setTimeout(() => {
			console.log("WebSocket: Reconnecting...");
			this._isConnecting = false; // Reset connecting flag
			this.connect();
		}, this._reconnectDelay); // Reconnect after a delay
	}

	handleConnection() {
		console.log("WebSocket: Connected");
		this._isConnecting = false; // Reset connecting flag
	}

	handleDisconnection() {
		console.log("WebSocket: Disconnected");
		this._isConnecting = false; // Reset connecting flag
		this.reconnect(); // Reconnect to WebSocket server
	}

	handleError(error) {
		console.error("WebSocket error:", error);
	}

	sendMessage(message) {
		if (this._ws.readyState === WebSocket.OPEN) {
			try {
				// If starting a new recording, clear previous session
				if (message.command === "start_recording") {
					this._currentSessionId = null;
					// Clear the text in the webview
					if (this._provider && this._provider._view) {
						this._provider._view.webview.postMessage({
							command: "transcription",
							text: ""
						});
					}
				}
				
				this._ws.send(JSON.stringify(message));
				console.log("WebSocket: Message sent:", message);
			} catch (error) {
				console.error(`WebSocket: Failed to send message:`, error);
			}
		} else {
			console.error("WebSocket: Not connected, message not sent");
		}
	}

	handleMessage(data) {
		console.log("WebSocket: Received raw data");
		try {
			const messageString = data.toString();
			const message = JSON.parse(messageString);
			console.log("WebSocket: Parsed message:", message);

			// Handle transcription messages
			if (this._provider && this._provider._view && message.type === 'transcription') {
				// Store session ID from first message of new session
				if (message.data.status === "ready") {
					this._currentSessionId = message.data.sessionId;
					console.log("WebSocket: New session started:", this._currentSessionId);
					return;
				}

				// Only process messages from current session
				if (message.data.sessionId === this._currentSessionId && message.data.text !== undefined) {
					console.log("WebSocket: Sending message to webview:", message.data.text);
					this._provider._view.webview.postMessage({
						command: "transcription",
						text: message.data.text
					});
				}
			}
		} catch (error) {
			console.error("WebSocket: Error processing message:", error);
		}
	}

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

	closeConnection() {
		if (this._ws) {
			this._ws.close();
		}
	}
}

module.exports = {
	WhisperliveWebSocketManager,
};
