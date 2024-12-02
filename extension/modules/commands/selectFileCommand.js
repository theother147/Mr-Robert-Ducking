const vscode = require("vscode");

const select_file = async (provider) => {
    try {
        if (!vscode.workspace.workspaceFolders) {
            throw new Error("No workspace folder open");
        }

        // Get all files in workspace
        const files = await vscode.workspace.findFiles(
            "**/*",
            "**/node_modules/**" // Exclude node_modules
        );
        const fileItems = files.map((file) => ({
            label: vscode.workspace.asRelativePath(file),
            uri: file,
            type: "file",
        }));

        // Add text selection option if there is selected text
        const editor = vscode.window.activeTextEditor;
        const selection = editor?.selection;
        const selectedText = editor?.document.getText(selection);

        let items = [
            ...(selectedText
                ? [
                        {
                            label: "Selected Text",
                            description:
                                selectedText.length > 50
                                    ? selectedText.substring(0, 50) + "..."
                                    : selectedText,
                            type: "selection",
                            text: selectedText,
                        },
                ]
                : []),
            ...fileItems,
        ];

        // Show quick pick with both options
        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: "Select content to attach",
        });

        if (selected) {
            if (selected.type === "selection") {
                // Handle text selection
                if (provider && provider._view) {
                    provider._view.webview.postMessage({
                        command: "addContext",
                        file: "Text selection",
                        content: selected.text, // text is available on selection items
                    });
                }
            } else if (selected.type === "file") {
                // Get current document if it matches the selected file
                const activeDocuments = vscode.workspace.textDocuments;
                const selectedDoc = activeDocuments.find(
                    (doc) => doc.uri.fsPath === selected.uri.fsPath
                );

                // Use current document content if available, otherwise read from disk
                const text = selectedDoc
                    ? selectedDoc.getText()
                    : new TextDecoder().decode(
                            await vscode.workspace.fs.readFile(selected.uri)
                    );

                if (provider && provider._view) {
                    provider._view.webview.postMessage({
                        command: "addContext",
                        file: `File: ${selected.label}`,
                        content: text,
                    });
                }
            }
        }
    } catch (error) {
        vscode.window.showErrorMessage(
            `Failed to read content: ${error.message}`
        );
    }
}

module.exports = select_file;