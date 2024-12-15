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

	function focusOnInput() {
		document.getElementById('messageInput').focus();
	}

	function adjustInputHeight() {
		messageInput.style.height = "auto";
		messageInput.style.height = messageInput.scrollHeight + "px";
	}

	function scrollToBottom() {	
		chatHistory.scrollTop = chatHistory.scrollHeight;
	}

	const previousState = vscode.getState() || {};
	chatHistory.innerHTML = previousState.chatHistoryState
		? previousState.chatHistoryState
		: "";

	if (previousState.messageInputState) {
		// @ts-ignore
		messageInput.value = previousState.messageInputState;
		adjustInputHeight();
	} else {
		// @ts-ignore
		messageInput.value = "";
		adjustInputHeight();
	}

	scrollToBottom(); // Scroll to the bottom of the chat history
	focusOnInput(); // Focus on the message input

	// Send a message to the extension
	function sendMessage() {
		const message = messageInput.value.trim();
		if (message) {
			allowInput(false); // Disable input while sending message
			disableRetry(); // Disable retry buttons
			updateChat(userName, message); // Update chat history with the message

			const payload = {
				command: "sendMessage",
				text: message,
			};
			if (attachedContext) {
				payload.context = {
					filename: attachedContext.filename,
					content: attachedContext.content,
				};
				attachedContext = null;
				updateContext();
			}
			vscode.postMessage(payload);
			vscode.setState({ messageInputState: "" });
			messageInput.value = ""; // Clear the message input
			adjustInputHeight(); // Adjust message input height
			vscode.setState({ chatHistoryState: chatHistory.innerHTML });
		} else {
			vscode.postMessage({
				command: "showInfo",
				text: "Please enter a message to send."
			});
			focusOnInput();
		}
	}

	// Append a message to the chat history
	function updateChat(sender = null, text = null, failed = false) {
		if (failed) {
			// Create retry button if message failed to send
			const retryButton = document.createElement("button");
			retryButton.className = "retry-button";
			retryButton.textContent = "Retry";
			retryButton.onclick = () => {
				retryButton.disabled = true;
				allowInput(false); // Disable input while sending message
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
			messageContent.innerHTML = `<p class="sender">${sender}:</p>${text}`; // Show sender and text
			messageElement.appendChild(messageContent); // Append message content to message element
			chatHistory.appendChild(messageElement); // Append message element to chat history
		}
		scrollToBottom() // Scroll to the bottom of the chat history
		vscode.setState({ chatHistoryState: chatHistory.innerHTML });
		focusOnInput(); // Focus on the message input
	}

	// Clear the chat history
	function clearChat() {
		messageInput.value = "";
		chatHistory.innerHTML = "";
		vscode.setState({ messageInputState: "" });
		vscode.setState({ chatHistoryState: "" });
	}

	// Handle messages from the extension
	window.addEventListener("message", (event) => {
		const message = event.data;

		switch (message.command) {
			case "wsStatus":
				updateWsStatus(message.status);
				break;

			case 'addContext':
				attachedContext = {
					filename: message.filename,
					content: message.content,
				};
				updateContext();
				break;

			case "sendSuccess":
				allowInput(true);
				messageInput.value = "";
				break;

			case "sendFailed":
				allowInput(true);
				updateChat(null, null, true);
				break;

			case "receiveMessage":
				updateChat(aiName, message.text);
				break;

			case "recording":
				messageInput.value += message.text;
				vscode.setState({ messageInputState: messageInput.value });
				adjustInputHeight();
				break;
			
			case "triggerSend":
				sendMessage();
				break;

			case "clearChat":
				clearChat();
		}
	});

	// Adjust the height of the message input based on its content
	messageInput.addEventListener('input', () => {
		adjustInputHeight();
		vscode.setState({ messageInputState: messageInput.value });
	}
	);

	// Send a message when the send button is clicked or Enter is pressed
	sendButton.addEventListener("click", sendMessage);
	messageInput.addEventListener("keydown", (event) => {
		if (event.key === "Enter" && !event.shiftKey) {
			event.preventDefault();
			sendMessage();
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
            allowInput(true);
        } else {  
            recordButton.className = 'icon-button recording';
            recordButton.title = 'Stop Voice Recording';
            recIcon.className = 'codicon codicon-mic-filled';
            recStatus.className = 'rec-button active';
            isRecording = true;
            vscode.postMessage({ command: 'startRecording' });
            allowInput(false);
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
		.addEventListener("click", deleteContext);

	// New chat button functionality
	newChatButton.addEventListener("click", () => {
		clearChat(); // Clear the chat history
		vscode.postMessage({ command: "newChat" }); // Execute extension command to start a new chat session
	});
});


function updateWsStatus(connected) {
    wsStatusIndicator.className = `ws-status ${connected ? 'connected' : 'disconnected'}`;
    wsStatusIndicator.title = connected ? 'Connected' : 'Disconnected';
}

function disableRetry() {
    const retryButtons = document.querySelectorAll('.retry-button');
    retryButtons.forEach(button => {
        // @ts-ignore
        button.disabled = true;
    });
}

function updateContext() {
    if (attachedContext) {
        contextText.textContent = `Context: ${attachedContext.filename}`;
        contextElement.className = 'context-indicator active';
        deleteContextButton.style.display = 'inline';
    } else {
        contextText.textContent = '';
        contextElement.className = 'context-indicator';
        deleteContextButton.style.display = 'none';
    }
}

function deleteContext() {
    attachedContext = null;
    updateContext();
} 

// Add control management functions
function allowInput(allowed) {
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