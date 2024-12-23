/**
 * Webview provider module for managing the extension's UI.
 * Handles the creation and management of the VS Code webview panel,
 * including message passing between the extension and webview.
 */

const vscode = require("vscode");
const path = require("path");
const fs = require("fs");
const { stopRecording, getRecordingStatus } = require("../commands/transcribeCommand");

/**
 * ViewProvider class manages the webview interface and communication
 * between the extension and the webview content.
 */
class ViewProvider {
  /**
   * Creates a new ViewProvider instance
   * @param {vscode.ExtensionContext} context - The VS Code extension context
   */
  constructor(context) {
    this.context = context;
    this._view = null;
  }

  /**
   * Creates and configures the webview panel
   * @param {vscode.WebviewView} webviewView - The webview view to configure
   */
  resolveWebviewView(webviewView) {
    this._view = webviewView;

    // Stop recording when the webview is hidden
    webviewView.onDidChangeVisibility(() => {
      if (!webviewView.visible) {
        vscode.commands.executeCommand('rubberduck.transcribe', { force_stop: true });
      }
    });

    // Stop recording when the webview is hidden
    webviewView.onDidChangeVisibility(() => {
      if (!webviewView.visible) {
        vscode.commands.executeCommand('rubberduck.transcribe', { force_stop: true });
      }
    });

    // Configure webview security and resource access
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [
        vscode.Uri.file(
          path.join(this.context.extensionPath, "modules", "webview")
        ),
        vscode.Uri.file(
          path.join(
            this.context.extensionPath,
            "node_modules",
            "@vscode/codicons",
            "dist"
          )
        ),
      ],
    };

    // Set up the webview content
    webviewView.webview.html = this.getHtmlForWebview();

    // Set up message handling from webview
    webviewView.webview.onDidReceiveMessage(
      (message) => {
        switch (message.command) {
          case "sendMessage":
            vscode.commands.executeCommand("rubberduck.sendMessage", message);
            break;
          case "transcribe":
            vscode.commands.executeCommand("rubberduck.transcribe");
            break;
          case "selectFile":
            vscode.commands.executeCommand("rubberduck.selectFile");
            break;
          case "newChat":
            vscode.commands.executeCommand("rubberduck.newChat");
            break;
          case "showInfo":
            vscode.window.showInformationMessage(message.text);
            break;
        }
      },
      undefined,
      this.context.subscriptions
    );
  }

  /**
   * Generates the HTML content for the webview
   * @returns {string} The complete HTML content for the webview
   */
  getHtmlForWebview() {
    // Load the base HTML template
    const webviewPath = path.join(
      this.context.extensionPath,
      "modules",
      "webview",
      "index.html"
    );
    let html = fs.readFileSync(webviewPath, "utf8");

    // Get URIs for webview resources
    const stylesUri = this._view.webview.asWebviewUri(
      vscode.Uri.file(
        path.join(
          this.context.extensionPath,
          "modules",
          "webview",
          "styles.css"
        )
      )
    );
    const scriptsUri = this._view.webview.asWebviewUri(
      vscode.Uri.file(
        path.join(
          this.context.extensionPath,
          "modules",
          "webview",
          "scripts.js"
        )
      )
    );
    const codiconsUri = this._view.webview.asWebviewUri(
      vscode.Uri.file(
        path.join(
          this.context.extensionPath,
          "node_modules",
          "@vscode/codicons",
          "dist",
          "codicon.css"
        )
      )
    );

    // Replace resource placeholders with actual URIs
    html = html.replace("${scriptsUri}", scriptsUri.toString());
    html = html.replace("${stylesUri}", stylesUri.toString());
    html = html.replace("${codiconsUri}", codiconsUri.toString());

    return html;
  }

  /**
   * Checks if the webview panel is currently visible
   * @returns {boolean} Whether the webview is visible
   */
  isWebviewVisible() {
    return this._view !== null && this._view.visible;
  }
}

module.exports = {
  ViewProvider,
};
