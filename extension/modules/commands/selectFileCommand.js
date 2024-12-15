const vscode = require("vscode");

const selectFile = async (provider) => {
    try {
        // Get all files in workspace if available
        let files = [];
        if (vscode.workspace.workspaceFolders) {
            files = await vscode.workspace.findFiles(
                "**/*", // Globally search for all files
                "**/node_modules/**" // Exclude node_modules
            );
        }

        // Map files to quick pick items
        const fileItems = files.map((file) => ({
            type: "file",
            label: vscode.workspace.asRelativePath(file),
            description: "", // Only show relative path for workspace files
            uri: file,
        }));

        // Add text selection option if there is selected text
        const editor = vscode.window.activeTextEditor;
        const selection = editor?.selection;
        const selectedText = editor?.document.getText(selection);

        // Add currently open files option if they are not part of the workspace
        const openFiles = vscode.workspace.textDocuments.filter(
            (doc) => !files.some((file) => file.fsPath === doc.uri.fsPath)
        );
        openFiles.forEach((doc) => {
            fileItems.push({
                type: "file",
                label: doc.fileName,
                description: doc.uri.fsPath, // Show path for non-workspace files
                uri: doc.uri,
            });
        });

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
                        filename: "Text selection",
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
                        filename: selected.label,
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

module.exports = selectFile;