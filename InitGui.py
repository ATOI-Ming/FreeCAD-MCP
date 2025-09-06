import FreeCAD as App
import FreeCADGui as Gui
import os
import sys
from PySide2 import QtWidgets

# 显示MCP面板的命令
class FreeCADMCPShowCommand:
    def GetResources(self):
        """定义命令的图标、菜单文本和工具提示"""
        # 安全获取项目根目录
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            # 如果__file__未定义，使用FreeCAD的Mod目录
            current_dir = os.path.join(App.getUserAppDataDir(), "Mod", "FreeCAD-MCP-main")
        icon_path = os.path.join(current_dir, "assets", "icon.svg")
        if not os.path.exists(icon_path):
            icon_path = ""
        return {
            'Pixmap': icon_path,
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
    def GetResources(self):
        """定义命令的图标、菜单文本和工具提示"""
        # 安全获取项目根目录
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            # 如果__file__未定义，使用FreeCAD的Mod目录
            current_dir = os.path.join(App.getUserAppDataDir(), "Mod", "FreeCAD-MCP-main")
        icon_path = os.path.join(current_dir, "assets", "icon.svg")
        if not os.path.exists(icon_path):
            icon_path = ""
        return {
            'Pixmap': icon_path,
            'MenuText': '启动MCP服务器',
            'ToolTip': '启动FreeCAD MCP服务器以接受外部连接'
        }
    
    def IsActive(self):
        """命令始终处于活动状态"""
        return True
    
    def Activated(self):
        """触发命令时启动MCP服务器"""
        import freecad_mcp_server
        # 创建服务器实例并启动
        server = freecad_mcp_server.FreeCADMCPServer()
        server.start()
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
    
    def GetIcon(self):
        """返回工作台图标"""
        # 安全获取项目根目录
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            # 如果__file__未定义，使用FreeCAD的Mod目录
            current_dir = os.path.join(App.getUserAppDataDir(), "Mod", "FreeCAD-MCP-main")
        icon_path = os.path.join(current_dir, "assets", "icon.svg")
        if not os.path.exists(icon_path):
            icon_path = ""
        return icon_path
    
    def Initialize(self):
        """初始化工作台，添加命令到工具栏和菜单"""
        # 安全获取项目根目录
        try:
            mod_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            # 如果__file__未定义，使用FreeCAD的Mod目录
            mod_dir = os.path.join(App.getUserAppDataDir(), "Mod", "FreeCAD-MCP-main")
        if mod_dir not in sys.path:
            sys.path.append(mod_dir)
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