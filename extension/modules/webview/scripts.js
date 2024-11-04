const vscode = acquireVsCodeApi();

// Send a message to the extension
function sendMessage() {
    const messageInput = document.getElementById('message');
    const message = messageInput.value.trim();
    if (message) {
        appendMessage('You', message);
        vscode.postMessage({ command: 'sendMessage', text: message });
        messageInput.value = '';
    }
}

// Append a message to the chat history
function appendMessage(sender, text) {
    const chatHistory = document.getElementById('chatHistory');
    const messageElement = document.createElement('div');
    messageElement.textContent = `${sender}: ${text}`;
    chatHistory.appendChild(messageElement);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Send a message when the send button is clicked or Enter is pressed
document.getElementById('sendButton').addEventListener('click', sendMessage);
document.getElementById('message').addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

// Clear the chat history
document.getElementById('clearButton').addEventListener('click', () => {
    document.getElementById('chatHistory').innerHTML = '';
});

// Handle messages from the extension
window.addEventListener('message', event => {
    const message = event.data;
    if (message.command === 'receiveMessage') {
        appendMessage(message.sender, message.text);
    }
});

// Log a message when the check button is clicked
document.getElementById('checkButton').addEventListener('click', () => {
    console.log('Check button clicked');
});