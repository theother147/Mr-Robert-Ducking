const path = require("path");

const getPythonExecutablePath = () => {
    try {
        const parentFolder = path.resolve(__dirname, "..");
        const pythonVirtualEnvironmentPath = path.join(
            parentFolder,
            "python",
            ".venv"
        );
        let pythonExecutablePath;
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
        return pythonExecutablePath;
    } catch (error) {
        console.error("Error getting python executable path:", error);
    }
}
module.exports = { getPythonExecutablePath };