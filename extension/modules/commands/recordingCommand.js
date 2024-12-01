const vscode = require("vscode");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");

const recording = (provider) => {
	try {
		const parentFolder = path.resolve(__dirname, "..", "..");
		const pythonVirtualEnvironmentPath = path.join(
			parentFolder,
			"python",
			".venv"
		);
		let pythonExecutablePath;
		console.log("Platform:", process.platform);
		if (process.platform.includes("win32")) {
			pythonExecutablePath = path.join(
				pythonVirtualEnvironmentPath,
				"Scripts",
				"python.exe"
			);
		} else {
			pythonExecutablePath = path.join(
				pythonVirtualEnvironmentPath,
				"bin",
				"python"
			);
		}

		const scriptPath = path.join(parentFolder, "python", "transcribe_audio.py");

		const recordingProcess = spawn(pythonExecutablePath, ["-u", scriptPath]);

		if (!fs.existsSync(pythonExecutablePath)) {
			console.error("Python executable not found at:", pythonExecutablePath);
			return;
		}

		if (!fs.existsSync(scriptPath)) {
			console.error("Python script not found at:", scriptPath);
			return;
		}

		recordingProcess.stdout.on("data", (data) => {
			console.log("Python output:", data.toString());
			if (provider && provider._view) {
				provider._view.webview.postMessage({
					command: "recording",
					sender: "Rubber Duck",
					text: data.toString(),
				});
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
