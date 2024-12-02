const vscode = require("vscode");

const select_file = async (provider) => {
    try {
        if (!vscode.workspace.workspaceFolders) {
            throw new Error("No workspace folder open");
        }

        // Get all files in workspace
        const files = await vscode.workspace.findFiles(
            "**/*", // Globally search for all files
            "**/node_modules/**" // Exclude node_modules
        );

        // Map files to quick pick items
        const fileItems = files.map((file) => ({
            type: "file",
            label: vscode.workspace.asRelativePath(file),
            uri: file,
        }));

        // Add text selection option if there is selected text
        const editor = vscode.window.activeTextEditor;
        const selection = editor?.selection;
        const selectedText = editor?.document.getText(selection);

        // Combine selected text and files into one array
        let items = [
            ...(selectedText
                ? [
                        {
                            type: "selection",
                            label: "Selected Text",
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

        // Attach selected content to chat
        if (selected) {
            if (selected.type === "selection") {
                // Send selected text to webview
                if (provider && provider._view) {
                    provider._view.webview.postMessage({
                        command: "addContext",
                        file: "Text selection",
                        content: selected.text,
                    });
                }
            } else if (selected.type === "file") {
                // Get current document if it matches the selected file
                const activeDocuments = vscode.workspace.textDocuments;
                const selectedDoc = activeDocuments.find(
                    (doc) => doc.uri.fsPath === selected.uri.fsPath
                );

                // Get text content of selected file
                const text = selectedDoc
                    ? selectedDoc.getText()
                    : new TextDecoder().decode(
                            await vscode.workspace.fs.readFile(selected.uri)
                    );

                // Send file content to webview
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