const userName = 'You';
const aiName = 'Rubber Duck';
let wsStatusIndicator;
let chatHistory;
let messageInput;
let attachButton;
let contextElement;
let contextText;
let deleteContextButton;
let recordButton;
let sendButton;
let newChatButton;
let isRecording = false;
let attachedContext;

// Wait for DOM to be ready
window.addEventListener('DOMContentLoaded', () => {
	// @ts-ignore
	const vscode = acquireVsCodeApi();

	wsStatusIndicator = document.getElementById("wsStatusIndicator");
	messageInput = document.getElementById("messageInput");
	chatHistory = document.getElementById("chatHistory");
	recordButton = document.getElementById("recordButton");
	attachButton = document.getElementById("attachButton");
	contextElement = document.getElementById("contextIndicator");
	contextText = document.getElementById("contextText");
	deleteContextButton = document.getElementById("deleteContextButton");
	sendButton = document.getElementById("sendButton");
	newChatButton = document.getElementById("newChatButton");

	function adjust_input_height() {
		messageInput.style.height = "auto";
		messageInput.style.height = messageInput.scrollHeight + "px";
	}

	const previousState = vscode.getState();
	chatHistory.innerHTML = previousState.chatHistoryState
		? previousState.chatHistoryState
		: "";

	if (previousState.messageInputState) {
		// @ts-ignore
		messageInput.value = previousState.messageInputState;
		adjust_input_height();
	}
	// Send a message to the extension
	function send_message() {
		const message = messageInput.value.trim();
		if (message) {
			allow_input(false); // Disable input while sending message
			disable_retry(); // Disable retry buttons
			update_chat(userName, message); // Update chat history with the message

			const payload = {
				command: "sendMessage",
				text: message,
			};
			if (attachedContext) {
				payload.context = {
					file: attachedContext.file,
					content: attachedContext.content,
				};
				attachedContext = null;
				update_context();
			}
			vscode.postMessage(payload);
			vscode.setState({ messageInputState: "" });
			messageInput.value = "";
		}
	}

	// Append a message to the chat history
	function update_chat(sender = null, text = null, failed = false) {
		if (failed) {
			// Create retry button if message failed to send
			const retryButton = document.createElement("button");
			retryButton.className = "retry-button";
			retryButton.textContent = "Retry";
			retryButton.onclick = () => {
				retryButton.disabled = true;
				allow_input(false); // Disable input while sending message
				const retryMessage = {
					command: "sendMessage",
					retry: true,
				};
				vscode.postMessage(retryMessage);
			};
			// Append failed message element to chat history
			const failedMessageElement = document.createElement("div");
			failedMessageElement.className = "message-failed";
			const failedMessageContent = document.createElement("span");
			failedMessageContent.className = "failed-message-text";
			failedMessageContent.textContent = "Failed to send message";
			failedMessageElement.appendChild(failedMessageContent);
			failedMessageElement.appendChild(retryButton);
			chatHistory.appendChild(failedMessageElement);
		} else {
			// Create message element
			const messageElement = document.createElement("div");
			const messageContent = document.createElement("span");
			messageContent.textContent = `${sender}: ${text}`; // Show sender and text
			messageElement.appendChild(messageContent); // Append message content to message element
			chatHistory.appendChild(messageElement); // Append message element to chat history
		}
		chatHistory.scrollTop = chatHistory.scrollHeight;
		vscode.setState({ chatHistoryState: chatHistory.innerHTML });
	}

	// Handle messages from the extension
	window.addEventListener("message", (event) => {
		const message = event.data;

		switch (message.command) {
			case "wsStatus":
				update_ws_status(message.status);
				break;

			case 'addContext':
				attachedContext = {
					file: message.file,
					content: message.content,
				};
				update_context();
				break;

			case "sendSuccess":
				allow_input(true);
				messageInput.value = "";
				break;

			case "sendFailed":
				allow_input(true);
				update_chat(null, null, true);
				break;

			case "receiveMessage":
				update_chat(aiName, message.text);
				break;

			case "recording":
				messageInput.value += message.text;
				vscode.setState({ messageInputState: messageInput.value });
				adjust_input_height();
				break;
		}
	});

	// Adjust the height of the message input based on its content
	messageInput.addEventListener('input', () => {
		adjust_input_height();
		vscode.setState({ messageInputState: messageInput.value });
	}
	);

	// Send a message when the send button is clicked or Enter is pressed
	sendButton.addEventListener("click", send_message);
	messageInput.addEventListener("keydown", (event) => {
		if (event.key === "Enter" && !event.shiftKey) {
			event.preventDefault();
			send_message();
		}
	});

    // Record button functionality
    recordButton.addEventListener('click', async () => {
        const recIcon = recordButton.querySelector('i');
        const recStatus = recordButton.querySelector('.rec-button');
        if (isRecording) {
            recordButton.className = 'icon-button';
            recordButton.title = 'Start Voice Recording';
            recIcon.className = 'codicon codicon-mic';
            recStatus.className = 'rec-button';
            isRecording = false;
            vscode.postMessage({ command: 'stopRecording' });
            allow_input(true);
        } else {  
            recordButton.className = 'icon-button recording';
            recordButton.title = 'Stop Voice Recording';
            recIcon.className = 'codicon codicon-mic-filled';
            recStatus.className = 'rec-button active';
            isRecording = true;
            vscode.postMessage({ command: 'startRecording' });
            allow_input(false);
        }
    });

	// Attach file button functionality
	attachButton.addEventListener("click", () => {
		vscode.postMessage({
			command: "selectFile",
		});
	});

	// Delete context button functionality
	document
		.getElementById("deleteContextButton")
		.addEventListener("click", delete_context);

	// New chat button functionality
	newChatButton.addEventListener("click", () => {
		messageInput.value = "";
		chatHistory.innerHTML = "";
		vscode.setState({ messageInputState: "" });
		vscode.setState({ chatHistoryState: "" });
	});
});


function update_ws_status(connected) {
    wsStatusIndicator.className = `ws-status ${connected ? 'connected' : 'disconnected'}`;
    wsStatusIndicator.title = connected ? 'Connected' : 'Disconnected';
}

function disable_retry() {
    const retryButtons = document.querySelectorAll('.retry-button');
    retryButtons.forEach(button => {
        // @ts-ignore
        button.disabled = true;
    });
}

function update_context() {
    if (attachedContext) {
        contextText.textContent = `Context: ${attachedContext.file}`;
        contextElement.className = 'context-indicator active';
        deleteContextButton.style.display = 'inline';
    } else {
        contextText.textContent = '';
        contextElement.className = 'context-indicator';
        deleteContextButton.style.display = 'none';
    }
}

function delete_context() {
    attachedContext = null;
    update_context();
} 

// Add control management functions
function allow_input(allowed) {
    if (allowed) {
        messageInput.disabled = false;
        recordButton.disabled = false;
        attachButton.disabled = false;
        sendButton.disabled = false;
        newChatButton.disabled = false;
    } else {
        messageInput.disabled = true;
        sendButton.disabled = true;
        attachButton.disabled = true;
        newChatButton.disabled = true;
        if (isRecording) {
            recordButton.disabled = false;
        } else {
            recordButton.disabled = true;
        }
    }
}