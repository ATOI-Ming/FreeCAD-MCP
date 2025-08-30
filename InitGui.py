import FreeCAD as App
import FreeCADGui as Gui
import os
import sys
from PySide import QtGui

# Command to show the MCP panel
class FreeCADMCPShowCommand:
    def GetResources(self):
        """Define the icon, menu text, and tooltip for the command."""
        icon_path = "D:/FreeCAD/Mod/freecad_mcp-main/assets/icon.svg"
        if not os.path.exists(icon_path):
            icon_path = ""
        return {
            'Pixmap': icon_path,
            'MenuText': 'Show FreeCAD MCP Panel',
            'ToolTip': 'Show the FreeCAD Model Control Protocol panel'
        }
    
    def IsActive(self):
        """Command is always active."""
        return True
    
    def Activated(self):
        """Show the MCP panel when the command is triggered."""
        import freecad_mcp_server
        freecad_mcp_server.show_panel()

# Command to run the macro file
class FreeCADMCPRunMacroCommand:
    last_macro_path = None
    
    def GetResources(self):
        """Define the icon, menu text, and tooltip for the command."""
        icon_path = "D:/FreeCAD/Mod/freecad_mcp-main/assets/icon.svg"
        if not os.path.exists(icon_path):
            icon_path = ""
        return {
            'Pixmap': icon_path,
            'MenuText': 'Run MCP Macro',
            'ToolTip': 'Run the FreeCAD MCP macro to generate model'
        }
    
    def IsActive(self):
        """Command is always active."""
        return True
    
    def Activated(self):
        """Open a file dialog to select and run a macro file, default to last used path."""
        macro_dir = App.getUserMacroDir()
        initial_path = self.last_macro_path or macro_dir
        macro_path, _ = QtGui.QFileDialog.getOpenFileName(None, "Select Macro", initial_path, "Macro Files (*.FCMacro)")
        if macro_path and os.path.exists(macro_path):
            self.last_macro_path = macro_path
            import freecad_mcp_server
            freecad_mcp_server.handle_run_macro(macro_path, None)
        else:
            import freecad_mcp_server
            freecad_mcp_server.log_error("No macro file selected or file does not exist.")

# Register commands
try:
    if not hasattr(Gui, "freecad_mcp_command"):
        Gui.addCommand('FreeCAD_MCP_Show', FreeCADMCPShowCommand())
    if not hasattr(Gui, "freecad_mcp_macro_command"):
        Gui.addCommand('FreeCAD_MCP_RunMacro', FreeCADMCPRunMacroCommand())
except Exception as e:
    App.Console.PrintError(f"注册命令错误: {str(e)}\n")

# Define the FreeCAD MCP workbench
class FreeCADMCPWorkbench(Gui.Workbench):
    MenuText = "FreeCAD MCP"
    ToolTip = "FreeCAD Model Control Protocol"
    
    def GetIcon(self):
        """Return the workbench icon."""
        icon_path = "D:/FreeCAD/Mod/freecad_mcp-main/assets/icon.svg"
        if not os.path.exists(icon_path):
            icon_path = ""
        return icon_path
    
    def Initialize(self):
        """Initialize the workbench, add commands to toolbar and menu."""
        mod_dir = "D:/FreeCAD/Mod/freecad_mcp-main"
        if mod_dir not in sys.path:
            sys.path.append(mod_dir)
        self.command_list = ["FreeCAD_MCP_Show", "FreeCAD_MCP_RunMacro"]
        self.appendToolbar("FreeCAD MCP Tools", self.command_list)
        self.appendMenu("&FreeCAD MCP", self.command_list)
        App.Console.PrintMessage("FreeCAD MCP 工作台已初始化\n")
    
    def Activated(self):
        """Called when the workbench is activated."""
        pass
    
    def Deactivated(self):
        """Called when the workbench is deactivated."""
        pass
    
    def GetClassName(self):
        """Return the C++ class name."""
        return "Gui::PythonWorkbench"

# Add the workbench
try:
    if not hasattr(Gui, "freecad_mcp_workbench"):
        Gui.addWorkbench(FreeCADMCPWorkbench())
        App.Console.PrintMessage("FreeCAD MCP 工作台已注册\n")
except Exception as e:
    App.Console.PrintError(f"注册工作台错误: {str(e)}\n")