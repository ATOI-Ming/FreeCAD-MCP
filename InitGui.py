import FreeCAD as App
import FreeCADGui as Gui
import os
import sys

try:  # FreeCAD 1.x uses Qt6 / PySide6
    from PySide6 import QtWidgets
except ImportError:  # FreeCAD 0.21 and older use Qt5 / PySide2
    from PySide2 import QtWidgets

def _locate_addon_dir():
    """FreeCAD executes InitGui.py without defining __file__, so resolve the
    addon directory from __file__ when available, else from sys.path."""
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        pass
    for entry in sys.path:
        if os.path.basename(os.path.normpath(entry)).lower() == "freecad-mcp":
            return entry
    return os.path.join(App.getUserAppDataDir(), "Mod", "FreeCAD-MCP")

# Make the addon directory importable as soon as the workbench is registered,
# so the commands also work before the workbench is activated.
_addon_dir = _locate_addon_dir()
if _addon_dir not in sys.path:
    sys.path.append(_addon_dir)

# FreeCAD executes InitGui.py with exec(code, globals, locals): module-level
# assignments land in `locals` and are invisible inside class bodies/methods,
# which look names up in `globals`. Publish the resolved paths there.
_ICON_PATH = ""
for _base in [_addon_dir] + [p for p in sys.path if p]:
    _candidate = os.path.join(_base, "assets", "icon.svg")
    if os.path.exists(_candidate):
        _ICON_PATH = _candidate
        break

try:
    globals().update({"_addon_dir": _addon_dir, "_ICON_PATH": _ICON_PATH})
except Exception:
    pass

# 显示MCP面板的命令
class FreeCADMCPShowCommand:
    def GetResources(self, _icon=_ICON_PATH):
        """定义命令的图标、菜单文本和工具提示"""
        return {
            'Pixmap': _icon,
            'MenuText': '显示FreeCAD MCP面板',
            'ToolTip': '显示FreeCAD模型控制协议面板'
        }
    
    def IsActive(self):
        """命令始终处于活动状态"""
        return True
    
    def Activated(self):
        """触发命令时显示MCP面板"""
        import freecad_mcp_server
        freecad_mcp_server.show_panel()

# 启动MCP服务器的命令
class FreeCADMCPStartServerCommand:
    def GetResources(self, _icon=_ICON_PATH):
        """定义命令的图标、菜单文本和工具提示"""
        return {
            'Pixmap': _icon,
            'MenuText': '启动MCP服务器',
            'ToolTip': '启动FreeCAD MCP服务器以接受外部连接'
        }
    
    def IsActive(self):
        """命令始终处于活动状态"""
        return True
    
    def Activated(self):
        """触发命令时启动MCP服务器"""
        import freecad_mcp_server
        # start_server() keeps a module-level reference so the socket is not GC'd
        server = freecad_mcp_server.start_server()
        if server.running:
            freecad_mcp_server.log_message("MCP服务器已启动")
        else:
            freecad_mcp_server.log_error("MCP服务器启动失败")

# 注册命令
try:
    if not hasattr(Gui, "freecad_mcp_command"):
        Gui.addCommand('FreeCAD_MCP_Show', FreeCADMCPShowCommand())
    if not hasattr(Gui, "freecad_mcp_server_command"):
        Gui.addCommand('FreeCAD_MCP_StartServer', FreeCADMCPStartServerCommand())
except Exception as e:
    App.Console.PrintError(f"注册命令错误: {str(e)}\n")

# 定义FreeCAD MCP工作台
class FreeCADMCPWorkbench(Gui.Workbench):
    MenuText = "FreeCAD MCP"
    ToolTip = "FreeCAD模型控制协议"
    
    def GetIcon(self, _icon=_ICON_PATH):
        """返回工作台图标"""
        return _icon
    
    def Initialize(self, _mod_dir=_addon_dir):
        """初始化工作台，添加命令到工具栏和菜单"""
        if _mod_dir not in sys.path:
            sys.path.append(_mod_dir)
        self.command_list = ["FreeCAD_MCP_Show", "FreeCAD_MCP_StartServer"]
        self.appendToolbar("FreeCAD MCP工具", self.command_list)
        self.appendMenu("&FreeCAD MCP", self.command_list)
        App.Console.PrintMessage("FreeCAD MCP 工作台已初始化\n")
    
    def Activated(self):
        """工作台被激活时调用"""
        pass
    
    def Deactivated(self):
        """工作台被停用时调用"""
        pass
    
    def GetClassName(self):
        """返回C++类名"""
        return "Gui::PythonWorkbench"

# 添加工作台
try:
    if not hasattr(Gui, "freecad_mcp_workbench"):
        Gui.addWorkbench(FreeCADMCPWorkbench())
        App.Console.PrintMessage("FreeCAD MCP 工作台已注册\n")
except Exception as e:
    App.Console.PrintError(f"注册工作台错误: {str(e)}\n")
