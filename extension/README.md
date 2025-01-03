# Rubber Duck AI Assistant

Rubber Duck AI Assistant is a Visual Studio Code extension that integrates an AI-powered coding assistant directly into your editor. It allows you to interact with an AI to get help with coding tasks, ask questions about your code, and enhance your productivity.

## Features

- **AI-Powered Chat**: Engage in conversations with the AI assistant within VS Code.
- **Code Context Attachment**: Attach code files or snippets to provide context to the AI.
- **Voice Input Support**: Use voice commands to interact with the assistant.
- **Interactive Chat History**: Keep track of your conversations with the AI.
- **Syntax Highlighting**: Enjoy improved readability with syntax-highlighted code in responses.

## Requirements

- Visual Studio Code ^1.94.0
- For extension usage:
  - No additional requirements - everything is handled by the backend server
- For backend development:
  - Docker and Docker Compose
  - Python 3.x (for local development only)

## Running the Extension

1. **Open the Assistant**
    - Click the Rubber Duck icon in the Activity Bar (left sidebar)
    - The extension will automatically connect to the backend server

## Usage

- **Sending Messages**: Type your message in the input box and press the send button or hit Enter.
- **Attaching Code Context**: Click the attach button to add code files or selected text from the editor to provide context.
- **Voice Commands**: Use the microphone button to start and stop voice input for sending messages.

All actions can be accessed via customizable keyboard shortcuts in VS Code's Keyboard Shortcuts settings (File > Preferences > Keyboard Shortcuts).

## Configuration Connection (optional)

    The extension connects to a hosted backend server by default. If you need to use a different server:
    1. Open VS Code Settings (Ctrl+,)
    2. Search for "Rubber Duck"
    3. Update the following settings if needed:
       - `rubberduck.webSocketUrl`: WebSocket server URL
       - `rubberduck.wslUrl`: WhisperLive WebSocket server URL

## Known Issues

- **WebSocket Status Indicator**: The WebSocket connection status indicator may not update correctly until the chat is cleared. As a workaround, press the "New Chat" button to see the current connection status.

- **Audio Transcription Delay**: First-time use of audio transcription may experience longer waiting times while the model is being loaded. Subsequent uses will be faster.

## Contributing

Contributions are welcome. Please open issues for any bugs or feature requests and submit pull requests for improvements.

## License

This project is licensed under the MIT License.
