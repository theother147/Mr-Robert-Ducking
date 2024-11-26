let speechIndicator;
let wsStatusElement;
let storedContext = null;

// Wait for DOM to be ready
window.addEventListener('DOMContentLoaded', () => {
    const vscode = acquireVsCodeApi();
    
    wsStatusElement = document.getElementById('wsStatus');
    
    /* // Add speech indicator element
    speechIndicator = document.createElement('div');
    speechIndicator.id = 'speechIndicator';
    speechIndicator.className = 'speech-indicator';
    speechIndicator.textContent = '●';
    document.getElementById('buttonContainer').appendChild(speechIndicator); */
    
    // Send a message to the extension
    function send_message() {
        const messageInput = document.getElementById('message');
        const message = messageInput.value.trim();
        if (message) {
            disable_controls(); // Disable controls immediately when sending
            disable_retry_buttons();
            append_message('You', message);
            
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

    // Clear the chat history
    document.getElementById('clearButton').addEventListener('click', () => {
        document.getElementById('chatHistory').innerHTML = '';
    });

    // Handle messages from the extension
    window.addEventListener('message', event => {
        const message = event.data;
        const recordButton = document.getElementById('recordButton');
        
        switch(message.command) {
            case 'receiveMessage':
                append_message(message.sender, message.text);
                break;
                
            case 'updateStatus':
                if (recordButton) {
                    recordButton.textContent = message.status;
                }
                break;
                
            case 'receiveTranscription':
                append_message('Transcription', message.text);
                if (recordButton) {
                    recordButton.disabled = false;
                    recordButton.textContent = 'Record Audio';
                }
                break;
                
            case 'recordingError':
                if (recordButton) {
                    recordButton.disabled = false;
                    recordButton.textContent = 'Record Audio';
                }
                append_message('Error', message.error);
                break;

            case 'voiceActivity':
                update_voice_activity(message.isSpeaking);
                break;

            case 'wsStatus':
                update_websocket_status(message.connected);
                break;

            case 'sendFailed':
                if (message.isLastRetry) {
                    enable_controls(message.text); // Re-enable with original text after last retry
                } else {
                    disable_controls(); // Keep disabled during retries
                }
                append_message('You', message.text, true, message.originalMessage);
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
                enable_controls(); // Clear and re-enable on success
                const messageInput = document.getElementById('message');
                messageInput.value = '';
                break;
        }
    });

    // Record audio button functionality
    const recordButton = document.getElementById('recordButton');
    if (recordButton) {
        recordButton.addEventListener('click', async () => {
            // Disable button and show recording state
            recordButton.disabled = true;
            recordButton.textContent = 'Recording...';
            
            try {
                // Send command to extension to start recording
                vscode.postMessage({ command: 'startRecording' });
                
            } catch (error) {
                // Reset button on error
                recordButton.disabled = false;
                recordButton.textContent = 'Record Audio';
                console.error('Recording failed:', error);
            }
        });
    }

    document.getElementById('attachButton').addEventListener('click', () => {
        vscode.postMessage({ 
            command: 'selectFile'
        });
    });
});

function update_voice_activity(isSpeaking) {
    if (!speechIndicator) return;
    speechIndicator.className = `speech-indicator ${isSpeaking ? 'active' : ''}`;
}

function update_websocket_status(connected) {
    if (!wsStatusElement) return;
    wsStatusElement.className = `ws-status ${connected ? 'connected' : 'disconnected'}`;
    wsStatusElement.title = connected ? 'Connected' : 'Disconnected';
}

function disable_retry_buttons() {
    const retryButtons = document.querySelectorAll('.retry-button:not([disabled])');
    retryButtons.forEach(button => {
        button.disabled = true;
        button.title = 'Retry no longer available';
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