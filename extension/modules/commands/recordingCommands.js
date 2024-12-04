const vscode = require("vscode");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");
const { getPythonExecutablePath } = require("../utils");

let recordingProcess;
const startRecording= async (provider) => {
		try {
			const scriptPath = path.join(
				path.resolve(__dirname, "..", ".."),
				"python",
				"transcribe_audio.py"
			);
			const pythonExecutablePath = getPythonExecutablePath();
			recordingProcess = spawn(pythonExecutablePath, ["-u", scriptPath]);
		} catch (error) {
			console.error("Failed to start recording:", error);
		}

		if (recordingProcess === undefined) {
			console.error("Recording process not started");
			return;
		}
		recordingProcess.stdout.on("data", (data) => {
			console.log("Python output:", data.toString());
			if (!data.toString().includes("[")) {
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
};

const stopRecording = async () => {
	if (recordingProcess) {
		recordingProcess.kill();
	}
}

module.exports = { startRecording, stopRecording };
