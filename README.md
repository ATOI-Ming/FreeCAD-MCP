# FreeCAD MCP Plugin

The **FreeCAD MCP** plugin integrates the **Model Control Protocol (MCP)** into FreeCAD, enabling automation of model creation, macro execution, and view management through a server-client architecture. It provides an MCP server with a GUI control panel and a client interface to streamline FreeCAD workflows, supporting tasks like creating/running macros, adjusting views, and integrating with external tools (e.g., Claude, Cursor, Trace, CodeBuddy).

![FreeCAD MCP Icon](assets/icon.svg)

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [MCP Configuration](#mcp-configuration)
- [Usage](#usage)
- [Tool Functions](#tool-functions)
- [Use Cases](#use-cases)
- [Assets](#assets)
- [Contributing](#contributing)
- [License](#license)

## Features

The FreeCAD MCP plugin (v0.1.0) offers:

- **MCP Server**: Provides a GUI control panel (`FreeCADMCPPanel`) and processes commands like `create_macro`, `update_macro`, `run_macro`, `set_view`, and `get_report` (`freecad_mcp_server.py`).
- **MCP Client**: Command-line tool to send commands via `stdio` or TCP, create/update/run `.FCMacro` files, validate code, and control FreeCAD remotely (`freecad_mcp_client.py`).
- **Macro Normalization**: Automatically adds imports (`FreeCAD`, `FreeCADGui`, `Part`, `math`) and post-execution steps (recompute, view adjustment) for macros (`freecad_mcp_client.py`).
- **GUI Control Panel**: Includes buttons to start/stop the server, clear logs, and switch views (front, top, right, axonometric) (`freecad_mcp_server.py`).
- **Logging**: Records messages and errors to `freecad_mcp_log.txt` and a GUI report browser (100-line limit).
- **Workbench Integration**: Adds a `FreeCADMCPWorkbench` with toolbar/menu commands (`InitGui.py`).
- **Visual Assets**: Includes workbench icon (`icon.svg`) and example models (`gear.png`, `flange.png`, `boat.png`, `table.png`).

Watch the demo: <img src="https://raw.githubusercontent.com/ATOI-Ming/FreeCAD-MCP/main/assets/freecad.gif" width="600">  
Download: [FreeCAD MCP Demo MP4](assets/freecad.mp4)  
For alternative playback, view on YouTube: [FreeCAD MCP Demo](https://youtube.com/your-video-link) (replace with actual link after uploading).

## Installation

Follow these steps to install and set up the FreeCAD MCP plugin.

### Prerequisites

- **FreeCAD**: Version 0.21 or later. [Download FreeCAD](https://www.freecad.org/downloads.php).
- **Python**: Version 3.8+ (included with FreeCAD or via Anaconda).
- **Anaconda** (optional, for dependency management): [Download Anaconda](https://www.anaconda.com/products/distribution).
- **Dependencies**: `mcp-server>=1.2.0`, `httpx>=0.24.1` (specified in `pyproject.toml`).

### Installation Steps

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/ATOI-Ming/FreeCAD-MCP.git
   ```

2. **Copy to FreeCAD Mod Directory**:

   Move the `FreeCAD-MCP` folder to FreeCAD's Mod directory:

   - **Windows**: `C:\Users\<YourUser>\AppData\Roaming\FreeCAD\Mod\`
   - **Linux**: `~/.local/share/FreeCAD/Mod/`
   - **macOS**: `~/Library/Application Support/FreeCAD/Mod/`

   ```bash
   cp -r FreeCAD-MCP C:\Users\<YourUser>\AppData\Roaming\FreeCAD\Mod\
   ```

3. **Set Up Anaconda Environment** (recommended):

   Create and activate a new Anaconda environment:

   ```bash
   conda create -n freecad_mcp python=3.8
   conda activate freecad_mcp
   ```

   Install dependencies:

   ```bash
   pip install mcp-server>=1.2.0 httpx>=0.24.1
   ```

4. **Launch FreeCAD**:

   - Open FreeCAD.
   - Switch to the `FreeCADMCPWorkbench` (icon: `assets/icon.svg`) from the workbench dropdown.

5. **Verify Installation**:

   - Confirm the `FreeCADMCPWorkbench` appears in FreeCAD.
   - Click `FreeCAD_MCP_Show` to open the control panel or `FreeCAD_MCP_RunMacro` to test macro execution.

## MCP Configuration

Configure the MCP client to run `freecad_mcp_client.py` using Anaconda's Python for `stdio` communication with FreeCAD.

1. **Create Configuration File**:

   Create a JSON file (e.g., `mcp_config.json`) in `D:\FreeCAD\Mod\FreeCAD-MCP-main\`:

   ```json
   {
       "mcpServers": {
           "freecad": {
               "disabled": false,
               "timeout": 60,
               "type": "stdio",
               "command": "D:\\Anaconda3\\python.exe",
               "args": ["D:\\FreeCAD\\Mod\\FreeCAD-MCP-main\\src\\freecad_mcp_client.py"]
           }
       }
   }
   ```

   **Notes**:
   - Adjust paths for your system:
     - Linux: `/home/<user>/anaconda3/bin/python`, `/home/<user>/.local/share/FreeCAD/Mod/FreeCAD-MCP-main/src/freecad_mcp_client.py`
     - macOS: `/Users/<user>/anaconda3/bin/python`, `/Users/<user>/Library/Application Support/FreeCAD/Mod/FreeCAD-MCP-main/src/freecad_mcp_client.py`
   - The configuration runs `freecad_mcp_client.py` for `stdio` communication with FreeCAD.

2. **Run the Server**:

   - **GUI Method**: In `FreeCADMCPWorkbench`, click `FreeCAD_MCP_Show` to start the MCP server (`freecad_mcp_server.py`) and open the control panel.
   - **Command-Line Method**:
     ```bash
     conda activate freecad_mcp
     python D:\FreeCAD\Mod\FreeCAD-MCP-main\freecad_mcp_server.py
     ```

3. **Verify Server**:

   - Check `freecad_mcp_log.txt` in `D:\FreeCAD\Mod\FreeCAD-MCP-main\` for startup messages (e.g., "Server started").
   - Ensure the server is responsive to client commands (e.g., `freecad_mcp_client.py --get-report`).

## Usage

### Using the GUI Control Panel

1. In FreeCAD, switch to `FreeCADMCPWorkbench` (icon: `assets/icon.svg`).
2. Click `FreeCAD_MCP_Show` to open the control panel (`FreeCADMCPPanel`).
3. Use the panel:
   - **Start/Stop Server**: Starts or stops the MCP server (`freecad_mcp_server.py`).
   - **Clear Logs**: Clears the report browser and `freecad_mcp_log.txt`.
   - **View Buttons**: Switches to front, top, right, or axonometric view.
4. Monitor logs in the report browser (updated every second via `QTimer`).

### Running Macros

1. **GUI Method**:
   - In `FreeCADMCPWorkbench`, click `FreeCAD_MCP_RunMacro`.
   - Select a `.FCMacro` file using the file dialog.
   - The macro runs with automatic normalization (adds imports, recomputes document, adjusts view).

2. **Command-Line Method**:
   - Activate Anaconda environment:
     ```bash
     conda activate freecad_mcp
     ```
   - Run a macro:
     ```bash
     python D:\FreeCAD\Mod\FreeCAD-MCP-main\src\freecad_mcp_client.py --run-macro path/to/macro.FCMacro
     ```
   - With parameters:
     ```bash
     python D:\FreeCAD\Mod\FreeCAD-MCP-main\src\freecad_mcp_client.py --run-macro gear.FCMacro --params '{"radius": 10}'
     ```

### Remote Control

Use `freecad_mcp_client.py` to send commands to the MCP server:

```bash
python D:\FreeCAD\Mod\FreeCAD-MCP-main\src\freecad_mcp_client.py --set-view 7
python D:\FreeCAD\Mod\FreeCAD-MCP-main\src\freecad_mcp_client.py --get-report
```

## Tool Functions

The plugin provides the following tool functions, implemented in `freecad_mcp_client.py` (for sending commands via `stdio` or TCP to `localhost:9876`) and processed by `freecad_mcp_server.py` (for handling commands in FreeCAD). These functions enable remote control of FreeCAD for macro operations, code validation, and view adjustments.

### Main Tool Functions

- **create_macro**:
  - **Description**: Creates a new FreeCAD macro file (`.FCMacro`) with a specified template.
  - **Parameters**:
    - `macro_name`: Name of the macro file (e.g., `my_macro.FCMacro`).
    - `template_type`: Template type (`default`, `basic`, `part`, `sketch`).
  - **Usage**:
    ```bash
    python D:\FreeCAD\Mod\FreeCAD-MCP-main\src\freecad_mcp_client.py --create-macro my_macro.FCMacro --template-type default
    ```
  - **Output**: JSON object confirming macro creation or error (e.g., `{"status": "success", "result": "Macro created"}` or `{"status": "error", "message": "..."}`).
  - **Implementation**:
    - Client (`freecad_mcp_client.py`): Generates macro file with predefined template code, sends creation request via `stdio` or TCP.
    - Server (`freecad_mcp_server.py`): Processes request (assumed via `handle_create_macro`).

- **update_macro**:
  - **Description**: Updates the content of an existing FreeCAD macro file (`.FCMacro`).
  - **Parameters**:
    - `macro_name`: Name of the macro file to update (e.g., `my_macro.FCMacro`).
    - `code`: New code content for the macro.
  - **Usage**:
    ```bash
    python D:\FreeCAD\Mod\FreeCAD-MCP-main\src\freecad_mcp_client.py --update-macro my_macro.FCMacro --code "import FreeCAD\nApp.newDocument()"
    ```
  - **Output**: JSON object confirming update or error (e.g., `{"status": "success", "result": "Macro updated"}` or `{"status": "error", "message": "..."}`).
  - **Implementation**:
    - Client: Sends update request with new code via `stdio` or TCP.
    - Server: Processes request (assumed via `handle_update_macro`).

- **run_macro**:
  - **Description**: Executes a FreeCAD macro file, normalizing code by adding imports (`FreeCAD`, `FreeCADGui`, `Part`, `math`) and post-execution steps (recompute document, set axonometric view, fit view).
  - **Parameters**:
    - `macro_path`: Path to the `.FCMacro` file (e.g., `path/to/macro.FCMacro`).
    - `params`: Optional JSON string for macro parameters (e.g., `{"radius": 10}`).
  - **Usage**:
    ```bash
    python D:\FreeCAD\Mod\FreeCAD-MCP-main\src\freecad_mcp_client.py --run-macro macro.FCMacro --params '{"radius": 10}'
    ```
  - **Output**: JSON object with execution result or error, including traceback if failed (e.g., `{"status": "success", "result": {...}}` or `{"status": "error", "message": "...", "result": {"traceback": "..."}}`).
  - **Implementation**:
    - Client: Normalizes macro code via `normalize_macro_code`, sends `{"type": "run_macro", "params": {"code": normalized_code, ...}}` via `stdio` or TCP.
    - Server: Executes normalized code via `handle_run_macro`, returns result.

- **validate_macro_code**:
  - **Description**: Validates the syntax and runtime correctness of a FreeCAD macro file or code snippet.
  - **Parameters**:
    - `macro_name`: Name of the macro file (e.g., `my_macro.FCMacro`) or `code` (direct code string).
  - **Usage**:
    ```bash
    python D:\FreeCAD\Mod\FreeCAD-MCP-main\src\freecad_mcp_client.py --validate-macro-code macro.FCMacro
    ```
  - **Output**: JSON object indicating validation result or error (e.g., `{"status": "success"}` or `{"status": "error", "message": "..."}`).
  - **Implementation**:
    - Client: Parses code using `ast` or try-except (inferred from `run_macro` error handling), checks syntax and imports.
    - Server: May assist in validation (assumed via `handle_validate_macro_code`).

- **set_view**:
  - **Description**: Adjusts the FreeCAD 3D view to a specified perspective (front, top, right, or axonometric).
  - **Parameters**:
    - `view_type`: View type (`1` for front, `2` for top, `3` for right, `7` for axonometric).
  - **Usage**:
    ```bash
    python D:\FreeCAD\Mod\FreeCAD-MCP-main\src\freecad_mcp_client.py --set-view 7
    ```
  - **Output**: JSON object confirming view change or error (e.g., `{"status": "success", "result": "view set to axonometric"}` or `{"status": "error", "message": "Invalid view type"}`).
  - **Implementation**:
    - Client: Validates `view_type` (1, 2, 3, 7), sends `{"type": "set_view", "params": {"view_type": view_type}}` via `stdio` or TCP.
    - Server: Adjusts view via `handle_set_view`, returns confirmation.

- **get_report**:
  - **Description**: Retrieves execution and validation reports from `freecad_mcp_log.txt`.
  - **Parameters**: None.
  - **Usage**:
    ```bash
    python D:\FreeCAD\Mod\FreeCAD-MCP-main\src\freecad_mcp_client.py --get-report
    ```
  - **Output**: JSON object containing log content (e.g., `{"status": "success", "result": {...}}`).
  - **Implementation**:
    - Client: Sends `{"type": "get_report", "params": {}}` via `stdio` or TCP.
    - Server: Reads log file via `handle_get_report`, returns content.

### Auxiliary Functions

- **Logging System**:
  - **Description**: Logs operations and errors to `freecad_mcp_log.txt` and the GUI report browser (100-line limit).
  - **Implementation**:
    - Server: Uses `log_message` for standard messages and `log_error` for errors with HTML formatting in the GUI.
    - Logs include timestamps and are appended to the file and displayed in the report browser.

- **Server Management**:
  - **Description**: Starts/stops the MCP server, listening on `localhost:9876` for TCP connections.
  - **Implementation**:
    - Server: `FreeCADMCPServer` class manages server lifecycle (`start`, `stop` methods).
    - GUI: `FreeCADMCPPanel` provides start/stop buttons.

- **GUI Panel**:
  - **Description**: Provides a graphical control panel (`FreeCADMCPPanel`) for server control, log management, and view switching.
  - **Implementation**:
    - Server: Uses `PySide2` to create a dialog with buttons for starting/stopping the server, clearing logs, and switching views (front, top, right, axonometric).
    - Updated every second via `QTimer` for real-time log display.

- **Error Handling**:
  - **Description**: Captures and reports exceptions during command execution, validation, and server operations.
  - **Implementation**:
    - Client: Uses `try-except` to catch JSON parsing, socket connection, and execution errors, returning JSON error objects with tracebacks.
    - Server: Logs errors via `log_error`, displays in GUI with red HTML formatting.

## Use Cases

### 1. Automating Gear Model Creation

- **Scenario**: Create a gear model programmatically for engineering design.
- **Steps**:
  1. Create a macro file:
     ```bash
     python D:\FreeCAD\Mod\FreeCAD-MCP-main\src\freecad_mcp_client.py --create-macro gear.FCMacro --template-type part
     ```
  2. Update the macro:
     ```bash
     python D:\FreeCAD\Mod\FreeCAD-MCP-main\src\freecad_mcp_client.py --update-macro gear.FCMacro --code "import FreeCAD, Part\nradius = 10\ngear = Part.makeCylinder(radius, 5)\nPart.show(gear)"
     ```
  3. Run the macro:
     ```bash
     python D:\FreeCAD\Mod\FreeCAD-MCP-main\src\freecad_mcp_client.py --run-macro gear.FCMacro --params '{"radius": 15}'
     ```
  4. Result: Gear model created, recomputed, and displayed in axonometric view.
- **Output**:
  ![Gear Model](assets/gear.png)

### 2. Generating a Flange Model

- **Scenario**: Automate flange creation with holes for mechanical design.
- **Steps**:
  1. Create and run a macro via GUI (`FreeCAD_MCP_RunMacro`) or command line:
     ```bash
     python D:\FreeCAD\Mod\FreeCAD-MCP-main\src\freecad_mcp_client.py --run-macro flange.FCMacro
     ```
  2. Result: Flange model created with normalized code.
- **Output**:
  ![Flange Model](assets/flange.png)

### 3. Text-Based Model Generation

- **Scenario**: Generate a boat model from a text description (e.g., "create a boat with a curved hull").
- **Steps**:
  1. Use an external tool (e.g., Claude) to generate `boat.FCMacro`.
  2. Run the macro:
     ```bash
     python D:\FreeCAD\Mod\FreeCAD-MCP-main\src\freecad_mcp_client.py --run-macro boat.FCMacro
     ```
  3. Result: Boat model created with automatic imports and view adjustment.
- **Output**:
  ![Boat Model](assets/boat.png)

### 4. CAD Drawing Recognition

- **Scenario**: Recreate a table model from a CAD drawing.
- **Steps**:
  1. Convert CAD drawing to `table.FCMacro` using a tool like Trace.
  2. Run via GUI or command line:
     ```bash
     python D:\FreeCAD\Mod\FreeCAD-MCP-main\src\freecad_mcp_client.py --run-macro table.FCMacro
     ```
  3. Result: Table model recreated in FreeCAD.
- **Output**:
  ![Table Model](assets/table.png)

### 5. Batch Processing Models

- **Scenario**: Automate creation of multiple models (e.g., gear and flange).
- **Steps**:
  1. Create a script to loop through macros:
     ```bash
     for macro in gear.FCMacro flange.FCMacro; do
         python D:\FreeCAD\Mod\FreeCAD-MCP-main\src\freecad_mcp_client.py --run-macro $macro
     done
     ```
  2. Result: Models generated sequentially, logged in `freecad_mcp_log.txt`.

## Assets

The `assets/` directory contains visual and demonstration resources for the FreeCAD MCP plugin:

- **icon.svg**: Workbench and command icon for `FreeCADMCPWorkbench`, used in `InitGui.py` and `package.xml`.
  ![FreeCAD MCP Icon](assets/icon.svg)
- **gear.png**: Example gear model created via `run_macro`.
  ![Gear Model](assets/gear.png)
- **flange.png**: Example flange model for engineering design.
  ![Flange Model](assets/flange.png)
- **boat.png**: Example boat model from text-based generation.
  ![Boat Model](assets/boat.png)
- **table.png**: Example table model from CAD drawing recognition.
  ![Table Model](assets/table.png)
- **freecad.gif**: Demo animation showcasing GUI panel, macro execution, and view switching.
  Watch: <img src="https://raw.githubusercontent.com/ATOI-Ming/FreeCAD-MCP/main/assets/freecad.gif" width="600">
- **freecad.mp4**: Original demo video, available for download.
  Download: [FreeCAD MCP Demo MP4](assets/freecad.mp4)
  For alternative playback, view on YouTube: [FreeCAD MCP Demo](https://youtube.com/your-video-link) (replace with actual link after uploading).

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository: `https://github.com/ATOI-Ming/FreeCAD-MCP`.
2. Create a branch: `git checkout -b feature/your-feature`.
3. Commit changes: `git commit -m "Add your feature"`.
4. Push and create a Pull Request.

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md) (to be added).

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.