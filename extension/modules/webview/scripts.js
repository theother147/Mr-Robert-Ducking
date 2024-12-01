let wsStatusElement;
let storedContext = null;
let isRecording = false;
const userName = 'You';
const aiName = 'Rubber Duck';

// Wait for DOM to be ready
window.addEventListener('DOMContentLoaded', () => {
    const vscode = acquireVsCodeApi();
    
    wsStatusElement = document.getElementById('wsStatus');
    
    // Send a message to the extension
    function send_message() {
        const messageInput = document.getElementById('message');
        const message = messageInput.value.trim();
        if (message) {
            disable_controls();
            disable_retry();
            append_message(userName, message);
            
            const payload = {
                command: 'sendMessage',
                text: message
            };
            if (storedContext) {
                payload.context = storedContext.content;
                clear_stored_context();
            }
            vscode.postMessage(payload);
        }
    }

    // Append a message to the chat history
    function append_message(sender, text, failed = false, originalMessage = null) {
        const chatHistory = document.getElementById('chatHistory');
        const messageElement = document.createElement('div');
        messageElement.className = failed ? 'message-failed' : '';

        const messageContent = document.createElement('span');
        messageContent.textContent = failed ? 'Failed to send message' : `${sender}: ${text}`;
        messageContent.className = failed ? 'failed-message-text' : '';
        messageElement.appendChild(messageContent);

        if (failed) {
            const retryButton = document.createElement('button');
            retryButton.className = 'retry-button';
            retryButton.textContent = 'Retry';
            retryButton.onclick = () => {
                retryButton.disabled = true;
                disable_controls(); // Disable controls during retry
                const messageToRetry = {
                    command: 'sendMessage',
                    text: originalMessage?.text || text,
                    originalText: text,
                    isRetry: true
                };
                vscode.postMessage(messageToRetry);
            };
            messageElement.appendChild(retryButton);
        }

        chatHistory.appendChild(messageElement);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    // Send a message when the send button is clicked or Enter is pressed
    document.getElementById('sendButton').addEventListener('click', send_message);
    document.getElementById('message').addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            send_message();
        }
    });

    // Clear chat history
    document.getElementById('clearButton').addEventListener('click', () => {
        document.getElementById('chatHistory').innerHTML = '';
    });

    // Attach a file to the chat
    document.getElementById('attachButton').addEventListener('click', () => {
        vscode.postMessage({ 
            command: 'selectFile'
        });
    });

    // Handle messages from the extension
    window.addEventListener('message', event => {
        const message = event.data;
        
        switch(message.type) {
            case 'wsStatus':
                update_websocket_status(message.status);
                break;

            case 'fileContent':
                storedContext = {
                    type: message.type || 'file',
                    content: message.content,
                    label: message.label || 'Selected content'
                };
                console.log('Stored context:', storedContext);
                update_context_indicator();
                break;

            case 'sendSuccess':
                enable_controls();
                const messageInput = document.getElementById('message');
                messageInput.value = '';
                break;

            case 'sendFailed':
                enable_controls(message.text);
                append_message(userName, message.text, true, message.originalMessage);
                break;

            case 'receiveMessage':
                append_message(message.sender, message.text);
                break;              
        }
    });

    // Record audio button functionality
    const recordButton = document.getElementById('recordButton');
    if (recordButton) {
        recordButton.addEventListener('click', async () => {
            if (isRecording) {
                recordButton.textContent = 'Start recording';
                isRecording = false;
                vscode.postMessage({ command: 'stopRecording' });
            } else {  
                recordButton.textContent = 'Stop recording';
                isRecording = true;
                vscode.postMessage({ command: 'startRecording' });
            }
        });
    }
});


function update_websocket_status(connected) {
    wsStatusElement.className = `ws-status ${connected ? 'connected' : 'disconnected'}`;
    wsStatusElement.title = connected ? 'Connected' : 'Disconnected';
}

function disable_retry() {
    const retryButtons = document.querySelectorAll('.retry-button:not([disabled])');
    retryButtons.forEach(button => {
        button.disabled = true;
    });
}

function update_context_indicator() {
    const indicator = document.getElementById('contextIndicator');
    if (storedContext) {
        indicator.textContent = `Context: ${storedContext.label}`;
        indicator.className = 'context-indicator active';
    } else {
        indicator.className = 'context-indicator';
    }
}

function clear_stored_context() {
    storedContext = null;
    update_context_indicator();
}

// Add control management functions
function disable_controls() {
    const messageInput = document.getElementById('message');
    const sendButton = document.getElementById('sendButton');
    const attachButton = document.getElementById('attachButton');
    
    messageInput.disabled = true;
    sendButton.disabled = true;
    attachButton.disabled = true;
}

function enable_controls(textToRestore = '') {
    const messageInput = document.getElementById('message');
    const sendButton = document.getElementById('sendButton');
    const attachButton = document.getElementById('attachButton');
    
    messageInput.disabled = false;
    sendButton.disabled = false;
    attachButton.disabled = false;
    
    if (textToRestore) {
        messageInput.value = textToRestore;
    }
}