// Add to the top of scripts.js
let speechIndicator;

// Wait for DOM to be ready
window.addEventListener('DOMContentLoaded', () => {
    const vscode = acquireVsCodeApi();
    
    // Add speech indicator element
    speechIndicator = document.createElement('div');
    speechIndicator.id = 'speechIndicator';
    speechIndicator.className = 'speech-indicator';
    speechIndicator.textContent = '●';
    document.getElementById('buttonContainer').appendChild(speechIndicator);
    
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
        const recordButton = document.getElementById('recordButton');
        
        switch(message.command) {
            case 'receiveMessage':
                appendMessage(message.sender, message.text);
                break;
                
            case 'updateStatus':
                if (recordButton) {
                    recordButton.textContent = message.status;
                }
                break;
                
            case 'receiveTranscription':
                appendMessage('Transcription', message.text);
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
                appendMessage('Error', message.error);
                break;

            case 'voiceActivity':
                updateVoiceActivity(message.isSpeaking);
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

function updateVoiceActivity(isSpeaking) {
    if (!speechIndicator) return;
    speechIndicator.className = `speech-indicator ${isSpeaking ? 'active' : ''}`;
}