const vscode = require("vscode");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");

const recording = async () => {
		try {
			const parentFolder = path.resolve(__dirname, "..", "..");
			const pythonExecutablePath = path.join( 
				parentFolder,
				"python",
				".venv",
				"bin",
				"python"
			);

			const scriptPath = path.join(
				parentFolder,
				"python",
				"transcribe_audio.py"
			);

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
