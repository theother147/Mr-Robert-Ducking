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

## Installation

1. **Install the Extension**

    Install the extension using the provided .vsix file:
    1. Open VS Code
    2. Go to Extensions view (Ctrl+Shift+X)
    3. Click "..." (More Actions) at the top of the Extensions view
    4. Select "Install from VSIX..."
    5. Choose the provided .vsix file

2. **Configure Connection (Optional)**

    The extension connects to a hosted backend server by default. If you need to use a different server:
    1. Open VS Code Settings (Ctrl+,)
    2. Search for "Rubber Duck"
    3. Update the following settings if needed:
       - `rubberduck.webSocketUrl`: WebSocket server URL
       - `rubberduck.wslUrl`: WhisperLive WebSocket server URL

## Running the Extension

1. **Open the Assistant**
    - Click the Rubber Duck icon in the Activity Bar (left sidebar)
    - The extension will automatically connect to the backend server

## Usage

- **Sending Messages**: Type your message in the input box and press the send button or hit Enter.
- **Attaching Code Context**: Click the attach button to add code files or selected text from the editor to provide context.
- **Voice Commands**: Use the microphone button to start and stop voice input for sending messages.

All actions can be accessed via customizable keyboard shortcuts in VS Code's Keyboard Shortcuts settings (File > Preferences > Keyboard Shortcuts).

## Known Issues

-

## Contributing

Contributions are welcome. Please open issues for any bugs or feature requests and submit pull requests for improvements.

## License

This project is licensed under the MIT License.

## Authors

- Daniel Brauer
- Lisa Hilterhaus
- Mike Raj
- Sebastian Zameit

## Development

### Requirements
- Node.js and npm for extension development
- Python 3.x for backend development
- Docker and Docker Compose for containerization
- VS Code for extension testing

### Building the Extension

1. **Setup Extension Development**
    ```bash
    # Clone the repository
    git clone https://github.com/theother147/Mr-Robert-Ducking.git
    cd Mr-Robert-Ducking

    # Install extension dependencies
    cd extension
    npm install

    # Setup Python environment for the extension
    cd python
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    

    # Install vsce globally
    npm install -g @vscode/vsce

    # Build the VSIX package
    vsce package
    ```
    The VSIX file will be generated in the extension directory.

### Setting up the Backend

1. **Build and Run with Docker Compose**
    ```bash
    # Make sure you're in the root directory
    cd Mr-Robert-Ducking

    # Build and start the containers
    docker compose up -d --build
    ```

2. **Development Setup (without Docker)**
    ```bash
    # Create and activate virtual environment
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate

    # Install dependencies
    pip install -r requirements.txt

    # Start the server
    python main.py
    ```

### Testing

1. **Extension Testing with VS Code Debugger**
    ```bash
    # Make sure you're in the extension directory
    cd extension
    
    # Install dependencies if not done already
    npm install
    
    # Setup Python environment if not done already
    cd python
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    cd ..
    ```
    
    Then in VS Code:
    1. Open the extension folder in VS Code
    2. Press F5 or go to Run > Start Debugging
    3. Select "Run Extension" from the debug configuration
    4. A new VS Code window will open with the extension loaded
    5. Make changes to `extension.js` and reload the window (Ctrl+R or Cmd+R) to test
    
    For automatic rebuilding during development:
    ```bash
    npm run watch
    ```

2. **Backend Testing**
    - The server includes test endpoints for WebSocket connections
    - Use the test client in `server/tests` to verify functionality
    - Monitor logs in Docker: `docker compose logs -f`