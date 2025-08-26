import os
import FreeCAD as App
import FreeCADGui as Gui
import json
import socket
import traceback
import time
import sys
from PySide2.QtCore import QTimer, QCoreApplication
from PySide2.QtWidgets import QMessageBox, QTextEdit, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide2.QtGui import QIcon

# 确保模块路径
mod_dir = os.path.join(App.getUserAppDataDir(), "Mod", "freecad_mcp")
if mod_dir not in sys.path:
    sys.path.append(mod_dir)

def log_message(message):
    message = f"[{time.ctime()}] {message}"
    App.Console.PrintMessage(message + "\n")
    if panel_instance and panel_instance.report_browser:
        current_text = panel_instance.report_browser.toPlainText().splitlines()
        current_text.append(message)
        if len(current_text) > FreeCADMCPServer().max_log_lines:
            current_text = current_text[-FreeCADMCPServer().max_log_lines:]
        panel_instance.report_browser.setPlainText("\n".join(current_text))
        panel_instance.report_browser.verticalScrollBar().setValue(
            panel_instance.report_browser.verticalScrollBar().maximum()
        )
    try:
        with open(FreeCADMCPServer().log_file, "a", encoding='utf-8', newline='\n') as f:
            f.write(f"{message}\n")
    except Exception as e:
        App.Console.PrintError(f"日志文件写入错误: {str(e)}\n")

def log_error(message):
    message = f"[{time.ctime()}] ERROR: {message}"
    App.Console.PrintError(message + "\n")
    if panel_instance and panel_instance.report_browser:
        current_text = panel_instance.report_browser.toPlainText().splitlines()
        current_text.append(f"<font color='red'>{message}</font>")
        if len(current_text) > FreeCADMCPServer().max_log_lines:
            current_text = current_text[-FreeCADMCPServer().max_log_lines:]
        panel_instance.report_browser.setHtml("\n".join(current_text))
        panel_instance.report_browser.verticalScrollBar().setValue(
            panel_instance.report_browser.verticalScrollBar().maximum()
        )
    try:
        with open(FreeCADMCPServer().log_file, "a", encoding='utf-8', newline='\n') as f:
            f.write(f"{message}\n")
    except Exception as e:
        App.Console.PrintError(f"日志文件写入错误: {str(e)}\n")

class FreeCADMCPServer:
    def __init__(self, host='localhost', port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.clients = []
        self.buffer = {}
        self.timer = None
        self.log_file = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp", "freecad_mcp_log.txt")
        self.max_log_lines = 100

    def start(self):
        if not App.GuiUp:
            QMessageBox.critical(None, "错误", "FreeCAD GUI 未初始化，请在图形界面中运行 FreeCAD")
            log_error("FreeCAD GUI 未初始化，服务器启动失败")
            return
        self.running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.socket.setblocking(False)
            self.timer = QTimer()
            self.timer.timeout.connect(self._process_server)
            self.timer.start(50)
            log_message(f"FreeCAD MCP 服务器启动于 {self.host}:{self.port}")
        except Exception as e:
            QMessageBox.critical(None, "服务器错误", f"服务器启动失败: {str(e)}\n请检查端口 {self.port} 是否被占用。")
            log_error(f"服务器启动失败: {str(e)}")
            self.stop()

    def stop(self):
        self.running = False
        if self.timer:
            self.timer.stop()
            self.timer = None
        if self.socket:
            self.socket.close()
        for client in self.clients:
            client.close()
        self.socket = None
        self.clients = []
        self.buffer = {}
        log_message("FreeCAD MCP 服务器已停止")

    def _process_server(self):
        if not self.running:
            return
        try:
            try:
                client, address = self.socket.accept()
                client.setblocking(False)
                self.clients.append(client)
                self.buffer[client] = b''
                log_message(f"连接到客户端: {address}")
            except BlockingIOError:
                pass
            for client in self.clients[:]:
                try:
                    data = client.recv(32768)
                    if data:
                        self.buffer[client] += data
                        try:
                            command = json.loads(self.buffer[client].decode('utf-8'))
                            self.buffer[client] = b''
                            response = self.execute_command(command)
                            response_json = json.dumps(response)
                            client.sendall(response_json.encode('utf-8'))
                        except json.JSONDecodeError:
                            pass
                    else:
                        log_message("客户端断开连接")
                        client.close()
                        self.clients.remove(client)
                        del self.buffer[client]
                except BlockingIOError:
                    pass
                except Exception as e:
                    log_error(f"接收数据错误: {str(e)}")
                    client.close()
                    self.clients.remove(client)
                    del self.buffer[client]
        except Exception as e:
            log_error(f"服务器错误: {str(e)}")

    def execute_command(self, command):
        try:
            cmd_type = command.get("type")
            params = command.get("params", {})
            handlers = {
                "create_macro": self.handle_create_macro,
                "update_macro": self.handle_update_macro,
                "run_macro": self.handle_run_macro,
                "validate_macro_code": self.handle_validate_macro_code,
                "set_view": self.handle_set_view,
                "get_report": self.handle_get_report
            }
            if cmd_type in handlers:
                log_message(f"执行 {cmd_type} 处理器")
                result = handlers[cmd_type](**params)
                return {"status": "success", "result": result}
            else:
                return {"status": "error", "message": f"未知命令类型: {cmd_type}"}
        except Exception as e:
            log_error(f"执行命令错误: {str(e)}")
            return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

    def handle_create_macro(self, macro_name, template_type="default"):
        try:
            macro_dir = App.getUserMacroDir()
            if not os.path.exists(macro_dir):
                os.makedirs(macro_dir)
            macro_path = os.path.join(macro_dir, f"{macro_name}.FCMacro")
            if os.path.exists(macro_path):
                return {"result": "error", "message": f"宏文件 '{macro_path}' 已存在"}
            template = {
                "default": "# FreeCAD Macro\n",
                "basic": "# FreeCAD Macro\nimport FreeCAD as App\ndoc = App.ActiveDocument\n",
                "part": "# FreeCAD Macro\nimport FreeCAD as App\nimport Part\ndoc = App.ActiveDocument\n",
                "sketch": "# FreeCAD Macro\nimport FreeCAD as App\nimport Sketcher\ndoc = App.ActiveDocument\n"
            }.get(template_type, "# FreeCAD Macro\n")
            with open(macro_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(template)
            log_message(f"创建宏文件: {macro_path}，模板: {template_type}")
            return {"result": "success", "macro_path": macro_path}
        except Exception as e:
            log_error(f"创建宏文件错误: {str(e)}")
            return {"result": "error", "message": str(e), "traceback": traceback.format_exc()}

    def handle_update_macro(self, macro_name, code):
        try:
            macro_dir = App.getUserMacroDir()
            macro_path = os.path.join(macro_dir, f"{macro_name}.FCMacro")
            if not os.path.exists(macro_path):
                return {"result": "error", "message": f"宏文件 '{macro_path}' 未找到"}
            with open(macro_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(code)
            with open(macro_path, 'r', encoding='utf-8') as f:
                written_code = f.read()
                log_message(f"更新宏文件: {macro_path}\n内容:\n{written_code}")
            return {"result": "success", "macro_path": macro_path}
        except Exception as e:
            log_error(f"更新宏文件错误: {str(e)}")
            return {"result": "error", "message": str(e), "traceback": traceback.format_exc()}

    def handle_run_macro(self, macro_path, params=None):
        try:
            macro_path = os.path.normpath(macro_path)
            if not os.path.exists(macro_path):
                return {"result": "error", "message": f"宏文件 '{macro_path}' 未找到"}
            if not App.GuiUp:
                return {"result": "error", "message": "FreeCAD GUI 未初始化"}
            with open(macro_path, 'r', encoding='utf-8') as f:
                code = f.read()
            namespace = {
                "App": App,
                "Gui": Gui,
                "FreeCAD": App,
                "FreeCADGui": Gui,
                "Part": __import__("Part"),
                "math": __import__("math"),
                "time": __import__("time"),
                "params": params or {}
            }
            result = [None]
            def execute_in_main_thread():
                try:
                    if not App.ActiveDocument:
                        App.newDocument("ComplexFlangeModel")
                        log_message("创建新文档: ComplexFlangeModel")
                    namespace["doc"] = App.ActiveDocument
                    log_message(f"运行宏文件: {macro_path}, ActiveDocument: {App.ActiveDocument.Name}")
                    before_objects = set(obj.Name for obj in App.ActiveDocument.Objects)
                    exec(code, namespace)
                    after_objects = set(obj.Name for obj in App.ActiveDocument.Objects)
                    result[0] = {"result": "success", "affected_objects": list(after_objects - before_objects)}
                except Exception as e:
                    result[0] = {"result": "error", "message": str(e), "traceback": traceback.format_exc()}
            QTimer.singleShot(0, execute_in_main_thread)
            timeout = 10
            start_time = time.time()
            while result[0] is None and time.time() - start_time < timeout:
                QCoreApplication.processEvents()
                time.sleep(0.05)
            if result[0] is None:
                log_error(f"宏文件 '{macro_path}' 执行超时")
                return {"result": "error", "message": "执行超时"}
            if result[0]["result"] == "success":
                log_message(f"执行宏文件: {macro_path}，受影响对象: {result[0]['affected_objects']}")
                return result[0]
            else:
                log_error(f"执行宏文件错误: {result[0]['message']}")
                return result[0]
        except Exception as e:
            log_error(f"执行宏文件错误: {str(e)}")
            return {"result": "error", "message": str(e), "traceback": traceback.format_exc()}

    def handle_validate_macro_code(self, macro_name=None, code=None):
        try:
            if macro_name:
                macro_path = os.path.join(App.getUserMacroDir(), f"{macro_name}.FCMacro")
                if not os.path.exists(macro_path):
                    return {"result": "error", "message": f"宏文件 '{macro_path}' 未找到"}
                with open(macro_path, 'r', encoding='utf-8') as f:
                    code = f.read()
            if not code:
                return {"result": "error", "message": "未提供代码"}
            try:
                __import__('ast').parse(code)
            except SyntaxError as e:
                log_error(f"语法错误: {str(e)}")
                return {"result": "error", "message": f"语法错误: {str(e)}"}
            namespace = {
                "App": App,
                "Gui": Gui,
                "FreeCAD": App,
                "FreeCADGui": Gui,
                "Part": __import__("Part"),
                "math": __import__("math"),
                "time": __import__("time")
            }
            result = [None]
            def validate_in_main_thread():
                try:
                    if not App.ActiveDocument:
                        App.newDocument("ValidationDoc")
                        log_message("创建验证文档: ValidationDoc")
                    namespace["doc"] = App.ActiveDocument
                    exec(code, namespace)
                    result[0] = {"result": "success"}
                except Exception as e:
                    result[0] = {"result": "error", "message": str(e), "traceback": traceback.format_exc()}
            QTimer.singleShot(0, validate_in_main_thread)
            timeout = 5
            start_time = time.time()
            while result[0] is None and time.time() - start_time < timeout:
                QCoreApplication.processEvents()
                time.sleep(0.05)
            if result[0] is None:
                log_error("代码验证超时")
                return {"result": "error", "message": "验证超时"}
            if result[0]["result"] == "success":
                affected_objects = [obj.Name for obj in App.ActiveDocument.Objects if hasattr(obj, "Modified") and obj.Modified] if App.ActiveDocument else []
                log_message(f"代码验证成功，受影响对象: {affected_objects}")
                return {"result": "success", "message": "代码有效", "affected_objects": affected_objects}
            else:
                log_error(f"运行时错误: {result[0]['message']}")
                return result[0]
        except Exception as e:
            log_error(f"验证代码错误: {str(e)}")
            return {"result": "error", "message": str(e), "traceback": traceback.format_exc()}

    def handle_set_view(self, view_type):
        try:
            if not App.GuiUp or not Gui.ActiveDocument or not hasattr(Gui.ActiveDocument, 'ActiveView') or not Gui.ActiveDocument.ActiveView:
                log_error("无活动视图或 GUI 未初始化")
                return {"result": "error", "message": "无活动视图或 GUI 未初始化"}
            view = Gui.ActiveDocument.ActiveView
            view_map = {
                "1": ("front", view.viewFront),
                "2": ("top", view.viewTop),
                "3": ("right", view.viewRight),
                "7": ("isometric", view.viewIsometric)
            }
            if view_type not in view_map:
                log_error(f"无效视图类型: {view_type}")
                return {"result": "error", "message": f"无效视图类型: {view_type}"}
            view_name, view_func = view_map[view_type]
            def set_view_in_main_thread():
                try:
                    log_message(f"尝试调整到 {view_name} 视图 (view_type: {view_type})")
                    view_func()
                    view.fitAll()
                    Gui.updateGui()
                    log_message(f"成功调整到 {view_name} 视图")
                except Exception as e:
                    log_error(f"视图调整失败: {str(e)}")
                    raise
            QTimer.singleShot(100, set_view_in_main_thread)
            return {"result": "success", "view_name": view_name}
        except Exception as e:
            log_error(f"调整视图错误: {str(e)}")
            return {"result": "error", "message": str(e), "traceback": traceback.format_exc()}

    def handle_get_report(self):
        try:
            if not panel_instance or not panel_instance.report_browser:
                show_panel()
            report = panel_instance.report_browser.toPlainText()
            log_message("获取报告")
            return {"result": "success", "report": report}
        except Exception as e:
            log_error(f"获取报告错误: {str(e)}")
            return {"result": "error", "message": str(e), "traceback": traceback.format_exc()}

class FreeCADMCPPanel:
    def __init__(self):
        from PySide2.QtWidgets import QWidget
        self.form = QWidget()
        self.form.setWindowTitle("FreeCAD MCP 控制面板")
        layout = QVBoxLayout(self.form)
        self.status_label = QLabel("服务器状态: 已停止")
        layout.addWidget(self.status_label)
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("启动服务器")
        self.stop_button = QPushButton("停止服务器")
        self.clear_button = QPushButton("清除日志")
        self.stop_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_server)
        self.stop_button.clicked.connect(self.stop_server)
        self.clear_button.clicked.connect(self.clear_logs)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.clear_button)
        layout.addLayout(button_layout)
        self.report_browser = QTextEdit()
        self.report_browser.setReadOnly(True)
        self.report_browser.setPlaceholderText("代码执行和验证结果将显示在此处")
        layout.addWidget(QLabel("报告浏览器:"))
        layout.addWidget(self.report_browser)
        view_layout = QHBoxLayout()
        view_buttons = [
            ("前视图 (1)", lambda: self.set_view("1")),
            ("俯视图 (2)", lambda: self.set_view("2")),
            ("右视图 (3)", lambda: self.set_view("3")),
            ("等轴测视图 (7)", lambda: self.set_view("7"))
        ]
        for label, callback in view_buttons:
            btn = QPushButton(label)
            btn.clicked.connect(callback)
            view_layout.addWidget(btn)
        layout.addLayout(view_layout)
        self.server = None

    def start_server(self):
        if not self.server:
            self.server = FreeCADMCPServer()
            self.server.start()
            if self.server.running:
                self.status_label.setText("服务器状态: 运行中")
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.report_browser.append("服务器已启动")

    def stop_server(self):
        if self.server:
            self.server.stop()
            self.server = None
            self.status_label.setText("服务器状态: 已停止")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.report_browser.append("服务器已停止")

    def set_view(self, view_type):
        if self.server:
            result = self.server.handle_set_view(view_type)
            if result["result"] == "success":
                self.report_browser.append(f"调整到 {result['view_name']} 视图")
            else:
                self.report_browser.append(f"调整视图错误: {result['message']}")

    def clear_logs(self):
        self.report_browser.clear()
        log_message("日志已清除")

panel_instance = None

def show_panel():
    global panel_instance
    try:
        panel_instance = FreeCADMCPPanel()
        Gui.Control.showDialog(panel_instance)
        App.Console.PrintMessage("MCP 面板已显示\n")
    except Exception as e:
        App.Console.PrintError(f"显示面板错误: {str(e)}\n")