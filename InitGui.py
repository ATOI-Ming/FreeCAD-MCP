import FreeCAD as App
import FreeCADGui as Gui
import os
import sys

# PySide版本兼容性处理
try:
    from PySide2.QtWidgets import QFileDialog
except ImportError:
    try:
        from PySide.QtGui import QFileDialog
    except ImportError:
        from PySide6.QtWidgets import QFileDialog

def get_mod_path():
    """动态获取模块路径"""
    try:
        current_file = os.path.abspath(__file__)
        mod_dir = os.path.dirname(current_file)
        return mod_dir
    except:
        # 如果__file__不可用，尝试其他方法
        try:
            # 使用FreeCAD的Mod目录
            return os.path.join(App.getUserAppDataDir(), "Mod", "FreeCAD-MCP-main")
        except:
            # 最后的备用方案
            return os.getcwd()

def get_icon_path():
    """获取图标路径"""
    try:
        mod_dir = get_mod_path()
        icon_path = os.path.join(mod_dir, "assets", "icon.svg")
        if os.path.exists(icon_path):
            return icon_path
    except:
        pass
    return ""

# Command to show the MCP panel
class FreeCADMCPShowCommand:
    def GetResources(self):
        """Define the icon, menu text, and tooltip for the command."""
        try:
            icon_path = get_icon_path()
        except:
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
        try:
            icon_path = get_icon_path()
        except:
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
        macro_path, _ = QFileDialog.getOpenFileName(None, "Select Macro", initial_path, "Macro Files (*.FCMacro)")
        if macro_path and os.path.exists(macro_path):
            self.last_macro_path = macro_path
            import freecad_mcp_server
            freecad_mcp_server.handle_run_macro(macro_path, None)
        else:
            import freecad_mcp_server
            freecad_mcp_server.log_error("No macro file selected or file does not exist.")

# Register commands
try:
    # 检查命令是否已注册
    existing_commands = Gui.listCommands()
    if 'FreeCAD_MCP_Show' not in existing_commands:
        Gui.addCommand('FreeCAD_MCP_Show', FreeCADMCPShowCommand())
    if 'FreeCAD_MCP_RunMacro' not in existing_commands:
        Gui.addCommand('FreeCAD_MCP_RunMacro', FreeCADMCPRunMacroCommand())
except Exception as e:
    App.Console.PrintError(f"注册命令错误: {str(e)}\n")

# Define the FreeCAD MCP workbench
class FreeCADMCPWorkbench(Gui.Workbench):
    MenuText = "FreeCAD MCP"
    ToolTip = "FreeCAD Model Control Protocol"
    
    def GetIcon(self):
        """Return the workbench icon."""
        try:
            return get_icon_path()
        except:
            return ""
    
    def Initialize(self):
        """Initialize the workbench, add commands to toolbar and menu."""
        try:
            mod_dir = get_mod_path()
            if mod_dir not in sys.path:
                sys.path.append(mod_dir)
        except:
            # 多重备用方案
            try:
                # 尝试使用当前文件目录
                mod_dir = os.path.dirname(os.path.abspath(__file__))
            except:
                # 如果__file__不可用，尝试其他方法
                try:
                    # 使用FreeCAD的Mod目录
                    mod_dir = os.path.join(App.getUserAppDataDir(), "Mod", "FreeCAD-MCP-main")
                except:
                    # 最后的备用方案：使用当前工作目录
                    mod_dir = os.getcwd()
            
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
    # 检查工作台是否已注册
    existing_workbenches = Gui.listWorkbenches()
    if 'FreeCADMCPWorkbench' not in existing_workbenches:
        Gui.addWorkbench(FreeCADMCPWorkbench())
        App.Console.PrintMessage("FreeCAD MCP 工作台已注册\n")
except Exception as e:
    App.Console.PrintError(f"注册工作台错误: {str(e)}\n")
