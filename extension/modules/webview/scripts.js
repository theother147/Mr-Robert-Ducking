// Add to the top of scripts.js
let speechIndicator;
let wsStatusElement;

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
            // Disable all previous retry buttons when sending a new message
            disable_retry_buttons();
            append_message('You', message);
            messageInput.value = '';
            vscode.postMessage({ command: 'sendMessage', text: message });
        }
    }

    // Append a message to the chat history
    function append_message(sender, text, failed = false) {
        const chatHistory = document.getElementById('chatHistory');
        const messageElement = document.createElement('div');
        messageElement.className = failed ? 'message-failed' : '';

        const messageContent = document.createElement('span');
        // Show different text for failed messages
        if (failed) {
            messageContent.textContent = 'Failed to send message';
            messageContent.className = 'failed-message-text';
        } else {
            messageContent.textContent = `${sender}: ${text}`;
        }
        messageElement.appendChild(messageContent);

        if (failed) {
            const retryButton = document.createElement('button');
            retryButton.className = 'retry-button';
            retryButton.textContent = 'Retry';
            retryButton.onclick = () => {
                retryButton.disabled = true;
                // Pass the original text in the retry attempt
                vscode.postMessage({ 
                    command: 'sendMessage', 
                    text: text,
                    isRetry: true 
                });
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
                append_message('You', message.text, true);
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