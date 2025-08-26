FreeCAD MCP Plugin
The FreeCAD MCP plugin integrates the Model Control Protocol (MCP) into FreeCAD, enabling automation of model creation, macro execution, and view management through a server-client architecture. It provides a TCP server, a GUI control panel, and a client interface to streamline FreeCAD workflows, supporting tasks like running macros, adjusting views, and integrating with external tools (e.g., Claude, Cursor, Trace).

Table of Contents

Features
Installation
MCP Configuration
Usage
Tool Functions
Use Cases
Assets
Contributing
License

Features
The FreeCAD MCP plugin (v0.1.0) offers:

TCP Server: Runs on localhost:9876, handling commands like get_scene_info, run_script, run_macro, set_view, and get_report (freecad_mcp_server.py).
GUI Control Panel: Provides buttons to start/stop the server, clear logs, and switch views (front, top, right, axonometric) (freecad_mcp_server.py).
Client Interface: Command-line tool to run .FCMacro files, validate code, and control FreeCAD remotely (freecad_mcp_client.py).
Macro Normalization: Automatically adds imports (FreeCAD, Part, math) and post-execution steps (recompute, view adjustment) (freecad_mcp_client.py).
Logging: Records messages and errors to freecad_mcp_log.txt and a GUI report browser (100-line limit).
Workbench Integration: Adds a FreeCADMCPWorkbench with toolbar/menu commands (InitGui.py).
Visual Assets: Includes workbench icon (icon.svg) and example models (gear.png, flange.png, boat.png, table.png).

Watch the demo: FreeCAD MCP Demo
Installation
Follow these steps to install the FreeCAD MCP plugin in FreeCAD.
Prerequisites

FreeCAD: Version 0.21 or later (download).
Python: Version 3.8+ (included with FreeCAD or via Anaconda).
Anaconda (optional, for dependency management): download.

Steps

Clone the Repository:git clone https://github.com/ATOI-Ming/FreeCADMCP.git


Copy to FreeCAD Mod Directory:
Move the FreeCADMCP folder to FreeCAD's Mod directory:
Windows: C:\Users\<YourUser>\AppData\Roaming\FreeCAD\Mod\
Linux: ~/.local/share/FreeCAD/Mod/
macOS: ~/Library/Application Support/FreeCAD/Mod/



cp -r FreeCADMCP C:\Users\<YourUser>\AppData\Roaming\FreeCAD\Mod\


Set Up Anaconda Environment (recommended for dependencies):
Create a new environment:conda create -n freecad_mcp python=3.8
conda activate freecad_mcp


Install dependencies (pyproject.toml):pip install mcp-server>=1.2.0 httpx>=0.24.1




Launch FreeCAD:
Open FreeCAD.
The FreeCADMCPWorkbench should appear in the workbench dropdown (with icon.svg).


Verify Installation:
Switch to FreeCADMCPWorkbench.
Click FreeCAD_MCP_Show to open the control panel or FreeCAD_MCP_RunMacro to run a macro.



MCP Configuration
Configure the MCP server to run freecad_mcp_server.py with FreeCAD's Python or Anaconda.

Create Configuration File:
Create a JSON file (e.g., mcp_config.json) in D:\FreeCAD\Mod\FreeCADMCP\:{
    "mcpServers": {
        "freecad": {
            "command": "C:\\ProgramData\\anaconda3\\python.exe",
            "args": ["D:\\FreeCAD\\Mod\\FreeCADMCP\\freecad_mcp_server.py"]
        }
    }
}


Note: Adjust paths for your system (e.g., Linux: /home/user/anaconda3/bin/python, macOS: /Users/user/anaconda3/bin/python).


Run the Server:
Use the GUI panel (FreeCAD_MCP_Show) to start the server, or run manually:python D:\FreeCAD\Mod\FreeCADMCP\freecad_mcp_server.py




Verify Server:
Check freecad_mcp_log.txt in D:\FreeCAD\Mod\FreeCADMCP\ for server startup messages.
Ensure the server is listening on localhost:9876.



Usage
GUI Control Panel

In FreeCAD, switch to FreeCADMCPWorkbench.
Click FreeCAD_MCP_Show to open the control panel (FreeCADMCPPanel).
Use buttons:
Start/Stop Server: Starts or stops the TCP server (localhost:9876).
Clear Logs: Clears the report browser and freecad_mcp_log.txt.
View Buttons: Switch to front, top, right, or axonometric view.


View logs in the report browser (updated every second via QTimer).

Running Macros

GUI Method:
Click FreeCAD_MCP_RunMacro in FreeCADMCPWorkbench.
Select a .FCMacro file via the file dialog.
The macro runs with automatic normalization (adds imports, recomputes document, adjusts view).


Command-Line Method:
Activate Anaconda environment:conda activate freecad_mcp


Run a macro:python D:\FreeCAD\Mod\FreeCADMCP\freecad_mcp_client.py --run-macro path/to/macro.FCMacro


Example with parameters:python D:\FreeCAD\Mod\FreeCADMCP\freecad_mcp_client.py --run-macro gear.FCMacro --params '{"radius": 10}'





Remote Control

Use freecad_mcp_client.py to send commands to the server:python D:\FreeCAD\Mod\FreeCADMCP\freecad_mcp_client.py --set-view front
python D:\FreeCAD\Mod\FreeCADMCP\freecad_mcp_client.py --get-report



Tool Functions
The plugin provides the following tool functions (defined in freecad_mcp_client.py and handled by freecad_mcp_server.py):

get_scene_info:

Description: Retrieves details of the active FreeCAD document (objects, properties).
Usage: python freecad_mcp_client.py --get-scene-info
Output: JSON with document details (e.g., object names, types).
Code: freecad_mcp_server.py (handle_get_scene_info).


run_script:

Description: Executes a Python script in FreeCAD's Python environment.
Usage: python freecad_mcp_client.py --run-script script.py
Code: freecad_mcp_server.py (handle_run_script).


run_macro:

Description: Runs a .FCMacro file with optional parameters, normalizing code (adds imports, recomputes).
Usage: python freecad_mcp_client.py --run-macro macro.FCMacro --params '{"radius": 10}'
Code: freecad_mcp_client.py (normalize_macro_code), freecad_mcp_server.py (handle_run_macro).


set_view:

Description: Adjusts the FreeCAD view (front, top, right, axonometric).
Usage: python freecad_mcp_client.py --set-view axonometric
Code: freecad_mcp_server.py (handle_set_view).


get_report:

Description: Retrieves the latest logs from freecad_mcp_log.txt.
Usage: python freecad_mcp_client.py --get-report
Code: freecad_mcp_server.py (handle_get_report).


validate_macro_code:

Description: Validates .FCMacro code before execution.
Usage: python freecad_mcp_client.py --validate-macro-code macro.FCMacro
Code: freecad_mcp_client.py (validate_macro_code).



Use Cases
1. Automating Gear Model Creation

Scenario: Create a gear model programmatically.
Steps:
Write a .FCMacro file (e.g., gear.FCMacro):import FreeCAD, Part
radius = 10  # Adjustable via --params
gear = Part.makeCylinder(radius, 5)
Part.show(gear)


Run via client:python freecad_mcp_client.py --run-macro gear.FCMacro --params '{"radius": 15}'


Result: Gear model created in FreeCAD, recomputed, and view set to axonometric.


Output: See assets/gear.png:

2. Generating a Flange Model

Scenario: Automate flange creation for engineering design.
Steps:
Use a macro (flange.FCMacro) to create a flange with holes.
Run via GUI (FreeCAD_MCP_RunMacro) or command line:python freecad_mcp_client.py --run-macro flange.FCMacro


Result: Flange model with normalized code and adjusted view.


Output: See assets/flange.png:

3. Text-Based Model Generation

Scenario: Generate a model from a text description (e.g., "create a boat model").
Steps:
Use an external tool (e.g., Claude) to generate a .FCMacro from text.
Run the macro:python freecad_mcp_client.py --run-macro boat.FCMacro


Result: Boat model created with automatic imports and view adjustment.


Output: See assets/boat.png:

4. CAD Drawing Recognition

Scenario: Recognize and recreate a table from a CAD drawing.
Steps:
Convert CAD drawing to .FCMacro using an external tool (e.g., Trace).
Run the macro via the GUI panel or:python freecad_mcp_client.py --run-macro table.FCMacro


Result: Table model recreated in FreeCAD.


Output: See assets/table.png:

5. Batch Processing Models

Scenario: Run multiple macros to create a series of models.
Steps:
Create a script to loop through macros:for macro in gear.FCMacro flange.FCMacro; do
    python freecad_mcp_client.py --run-macro $macro
done


Result: Multiple models generated with logs saved in freecad_mcp_log.txt.



Assets
The assets/ directory contains visual and demonstration resources:

icon.svg: Workbench and command icon for FreeCADMCPWorkbench (InitGui.py, package.xml).
gear.png: Example gear model created via run_macro.
flange.png: Example flange model showcasing engineering design.
boat.png: Example boat model from text-based generation.
table.png: Example table model from CAD drawing recognition.
freecad.mp4: Demo video showing GUI panel, macro execution, and view switching.Watch: FreeCAD MCP Demo

Contributing
Contributions are welcome! To contribute:

Fork the repository: https://github.com/ATOI-Ming/FreeCADMCP.
Create a branch: git checkout -b feature/your-feature.
Commit changes: git commit -m "Add your feature".
Push and create a Pull Request.See CONTRIBUTING.md for details (to be added).

License
This project is licensed under the MIT License. See LICENSE for details.