const vscode = require("vscode");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");
const { getPythonExecutablePath } = require("../utils");

const recording = async (provider) => {
	try{
		const scriptPath = path.join(path.resolve(__dirname, "..", ".."), "python", "transcribe_audio.py");
		const pythonExecutablePath = getPythonExecutablePath();
		const recordingProcess = spawn(pythonExecutablePath, ["-u", scriptPath]);

		recordingProcess.stdout.on("data", (data) => {
			console.log("Python output:", data.toString());
			if (!data.toString().includes("[INFO]")) {
				if (provider && provider._view) {
					provider._view.webview.postMessage({
						command: "recording",
						text: data.toString(),
					});
				}
			}
		});

		// Add stderr handler
		recordingProcess.stderr.on("data", (data) => {
			console.error("Python error:", data.toString());
		});

		// Add exit handler
		recordingProcess.on("close", (code) => {
			console.log(`Python process exited with code ${code}`);
		});


		
	} catch (error) {
		vscode.window.showErrorMessage(`Recording failed: ${error.message}`);
	}
};

module.exports = recording;
