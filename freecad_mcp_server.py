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
        current_text.append(message)  # 修复：统一使用纯文本格式
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

class FreeCADMCPServer:
    def __init__(self, host='localhost', port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.clients = []
        self.buffer = {}
        self.timer = None
        # 修复：使用更通用的临时目录路径
        import tempfile
        self.log_file = os.path.join(tempfile.gettempdir(), "freecad_mcp_log.txt")
        self.max_log_lines = 100
        self.connection_timeout = 30  # 连接超时设置
        self.max_clients = 5  # 最大客户端连接数
        self.buffer_size = 32768  # 缓冲区大小
        self.max_buffer_size = 1024 * 1024  # 最大缓冲区大小(1MB)
        self.client_timeouts = {}  # 客户端超时跟踪

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
            # 接受新连接
            try:
                client, address = self.socket.accept()
                # 检查最大连接数限制
                if len(self.clients) >= self.max_clients:
                    log_message(f"达到最大连接数限制，拒绝连接: {address}")
                    client.close()
                else:
                    client.setblocking(False)
                    client.settimeout(self.connection_timeout)  # 设置超时
                    self.clients.append(client)
                    self.buffer[client] = b''
                    self.client_timeouts[client] = time.time()  # 记录连接时间
                    log_message(f"连接到客户端: {address}")
            except BlockingIOError:
                pass
            
            # 处理现有客户端
            for client in self.clients[:]:
                try:
                    data = client.recv(self.buffer_size)
                    if data:
                        self.buffer[client] += data
                        # 检查缓冲区大小，防止内存溢出
                        if len(self.buffer[client]) > self.max_buffer_size:
                            log_error("客户端数据过大，断开连接")
                            self._cleanup_client(client)
                            continue
                        
                        # 更新客户端活动时间
                        self.client_timeouts[client] = time.time()
                        
                        try:
                            command = json.loads(self.buffer[client].decode('utf-8'))
                            self.buffer[client] = b''
                            response = self.execute_command(command)
                            response_json = json.dumps(response, ensure_ascii=False)
                            client.sendall(response_json.encode('utf-8'))
                        except json.JSONDecodeError:
                            # 数据可能不完整，继续等待
                            pass
                        except UnicodeDecodeError as e:
                            log_error(f"编码错误: {str(e)}")
                            self._cleanup_client(client)
                    else:
                        log_message("客户端断开连接")
                        self._cleanup_client(client)
                except BlockingIOError:
                    pass
                except Exception as e:
                    log_error(f"处理客户端数据错误: {str(e)}")
                    self._cleanup_client(client)
            
            # 检查客户端超时
            self._check_client_timeouts()
        except Exception as e:
            log_error(f"服务器处理错误: {str(e)}")

    def _cleanup_client(self, client):
        """清理客户端连接的辅助方法"""
        try:
            if client in self.clients:
                self.clients.remove(client)
            if client in self.buffer:
                del self.buffer[client]
            if client in self.client_timeouts:
                del self.client_timeouts[client]
            client.close()
        except Exception as e:
            log_error(f"清理客户端连接时出错: {str(e)}")
    
    def _check_client_timeouts(self):
        """检查并清理超时的客户端连接"""
        current_time = time.time()
        timeout_clients = []
        
        for client, last_activity in self.client_timeouts.items():
            if current_time - last_activity > self.connection_timeout:
                timeout_clients.append(client)
        
        for client in timeout_clients:
            log_message("客户端连接超时，断开连接")
            self._cleanup_client(client)

    def execute_command(self, command):
        command_type = command.get("type")
        params = command.get("params", {})
        if command_type == "create_macro":
            return self.handle_create_macro(params.get("macro_name"), params.get("template_type"))
        elif command_type == "update_macro":
            return self.handle_update_macro(params.get("macro_name"), params.get("code"))
        elif command_type == "run_macro":
            return self.handle_run_macro(params.get("macro_path"), params.get("params"))
        elif command_type == "validate_macro_code":
            return self.handle_validate_macro_code(params.get("macro_name"), params.get("code"))
        elif command_type == "set_view":
            return self.handle_set_view(params.get("view_type"))
        elif command_type == "get_report":
            return self.handle_get_report()
        return {"result": "error", "message": f"未知命令: {command_type}"}

    def handle_create_macro(self, macro_name, template_type="default"):
        try:
            macro_dir = App.getUserMacroDir()
            macro_path = os.path.join(macro_dir, f"{macro_name}.FCMacro")
            template_map = {
                "default": "# FreeCAD Macro\n",
                "basic": "import FreeCAD as App\nimport FreeCADGui as Gui\n\n",
                "part": "import FreeCAD as App\nimport FreeCADGui as Gui\nimport Part\n\n",
                "sketch": "import FreeCAD as App\nimport FreeCADGui as Gui\nimport Sketcher\n\n"
            }
            template = template_map.get(template_type, "# FreeCAD Macro\n")
            with open(macro_path, "w", encoding='utf-8') as f:
                f.write(template)
            log_message(f"宏文件创建成功: {macro_path}")
            return {"result": "success", "message": f"宏文件创建成功: {macro_path}"}
        except Exception as e:
            log_error(f"创建宏文件错误: {str(e)}")
            return {"result": "error", "message": str(e), "traceback": traceback.format_exc()}

    def handle_update_macro(self, macro_name, code):
        try:
            macro_dir = App.getUserMacroDir()
            macro_path = os.path.join(macro_dir, f"{macro_name}.FCMacro")
            with open(macro_path, "w", encoding='utf-8') as f:
                f.write(code)
            log_message(f"宏文件更新成功: {macro_path}")
            return {"result": "success", "message": f"宏文件更新成功: {macro_path}"}
        except Exception as e:
            log_error(f"更新宏文件错误: {str(e)}")
            return {"result": "error", "message": str(e), "traceback": traceback.format_exc()}

    def handle_run_macro(self, macro_path, params):
        try:
            # 智能路径处理 - 支持相对路径和绝对路径
            original_macro_path = macro_path
            resolved_path = None
            
            # 路径解析策略
            search_paths = []
            
            if os.path.isabs(macro_path):
                # 绝对路径直接使用
                search_paths.append(macro_path)
            else:
                # 相对路径多重查找策略
                macro_dir = App.getUserMacroDir()
                
                # 1. 在FreeCAD宏目录中查找
                search_paths.append(os.path.join(macro_dir, macro_path))
                
                # 2. 如果没有.FCMacro扩展名，自动添加
                if not macro_path.endswith('.FCMacro'):
                    search_paths.append(os.path.join(macro_dir, f"{macro_path}.FCMacro"))
                
                # 3. 在当前工作目录查找
                search_paths.append(os.path.abspath(macro_path))
                
                # 4. 在项目目录查找
                project_dir = os.path.dirname(__file__)
                search_paths.append(os.path.join(project_dir, macro_path))
            
            # 按优先级查找文件
            for path in search_paths:
                if os.path.exists(path):
                    resolved_path = path
                    log_message(f"找到宏文件: {resolved_path}")
                    break
            
            # 验证宏文件路径
            if not resolved_path:
                search_info = "\n".join([f"  - {path}" for path in search_paths])
                log_error(f"宏文件不存在: {original_macro_path}\n搜索路径:\n{search_info}")
                return {"result": "error", "message": f"宏文件不存在: {original_macro_path}"}
            
            macro_path = resolved_path
            
            if not macro_path.endswith('.FCMacro'):
                log_error(f"无效的宏文件扩展名: {macro_path}")
                return {"result": "error", "message": "宏文件必须以.FCMacro结尾"}
            
            # 获取和验证文档名称
            doc_name = self._get_document_name(macro_path, params)
            
            # 文档管理
            doc_created = False
            try:
                existing_doc = App.getDocument(doc_name) if doc_name in App.listDocuments() else None
                
                if existing_doc:
                    App.setActiveDocument(doc_name)
                    log_message(f"使用现有文档: {doc_name}")
                else:
                    App.newDocument(doc_name)
                    App.setActiveDocument(doc_name)
                    doc_created = True
                    log_message(f"创建新文档: {doc_name}")
                
                # 确保活动文档有效
                if not App.ActiveDocument:
                    raise Exception("无法设置活动文档")
                
                # 执行宏文件
                self._execute_macro_file(macro_path)
                
                # 重新计算和更新视图
                self._update_document_view()
                
                log_message(f"宏文件 {macro_path} 执行成功于文档 {doc_name}")
                return {"result": "success", "message": f"宏执行成功于文档 {doc_name}", "document": doc_name}
                
            except Exception as e:
                # 如果是新创建的文档且执行失败，清理文档
                if doc_created and App.ActiveDocument and App.ActiveDocument.Name == doc_name:
                    try:
                        App.closeDocument(doc_name)
                        log_message(f"清理失败的文档: {doc_name}")
                    except:
                        pass
                raise e
                
        except Exception as e:
            log_error(f"运行宏错误: {str(e)}")
            return {"result": "error", "message": str(e), "traceback": traceback.format_exc()}

    def _get_document_name(self, macro_path, params):
        """获取并验证文档名称"""
        import re
        
        if params and "doc_name" in params and params["doc_name"]:
            doc_name = params["doc_name"]
        elif params is None and App.ActiveDocument:
            # GUI 调用，使用当前活动文档
            doc_name = App.ActiveDocument.Name
        else:
            # 使用宏文件名
            doc_name = os.path.splitext(os.path.basename(macro_path))[0]
        
        # 确保文档名称合法
        doc_name = re.sub(r'[^\w\-]', '_', doc_name)
        if not doc_name or doc_name.isdigit():
            doc_name = f"Document_{doc_name}"
        
        return doc_name

    def _execute_macro_file(self, macro_path):
        """安全执行宏文件"""
        try:
            with open(macro_path, 'r', encoding='utf-8') as f:
                macro_code = f.read()
            
            # 创建安全的执行环境
            safe_globals = {
                "App": App,
                "Gui": Gui,
                "__name__": "__main__",
                "__file__": macro_path
            }
            
            # 添加常用模块
            import Part, Draft, Sketcher, math
            safe_globals.update({
                "Part": Part,
                "Draft": Draft, 
                "Sketcher": Sketcher,
                "math": math
            })
            
            exec(macro_code, safe_globals)
            
        except Exception as e:
            raise Exception(f"宏执行失败: {str(e)}")

    def _update_document_view(self):
        """更新文档视图"""
        try:
            if App.ActiveDocument:
                App.ActiveDocument.recompute()
            
            if App.GuiUp and Gui.ActiveDocument and hasattr(Gui.ActiveDocument, 'ActiveView') and Gui.ActiveDocument.ActiveView:
                Gui.ActiveDocument.ActiveView.viewAxometric()
                Gui.ActiveDocument.ActiveView.fitAll()
                Gui.updateGui()
        except Exception as e:
            log_error(f"更新视图失败: {str(e)}")

    def handle_validate_macro_code(self, macro_name=None, code=None):
        try:
            if not code:
                if not macro_name or not os.path.exists(os.path.join(App.getUserMacroDir(), f"{macro_name}.FCMacro")):
                    log_error("宏文件名无效或文件不存在")
                    return {"result": "error", "message": "宏文件名无效或文件不存在"}
                with open(os.path.join(App.getUserMacroDir(), f"{macro_name}.FCMacro"), 'r', encoding='utf-8') as f:
                    code = f.read()
            temp_doc = App.newDocument("TempValidateDoc")
            exec(code, {"App": App, "Gui": Gui})
            App.closeDocument("TempValidateDoc")
            log_message("宏代码验证成功")
            return {"result": "success", "message": "宏代码验证成功"}
        except Exception as e:
            log_error(f"验证宏代码错误: {str(e)}")
            return {"result": "error", "message": str(e), "traceback": traceback.format_exc()}

    def handle_set_view(self, view_type):
        try:
            # 检查GUI和文档状态
            if not App.GuiUp:
                log_error("FreeCAD GUI 未启动")
                return {"result": "error", "message": "FreeCAD GUI 未启动，无法调整视图"}
            
            if not App.ActiveDocument:
                log_error("没有活动文档")
                return {"result": "error", "message": "没有活动文档，请先创建或打开文档"}
            
            if not Gui.ActiveDocument:
                log_error("GUI文档未初始化")
                return {"result": "error", "message": "GUI文档未初始化"}
            
            if not hasattr(Gui.ActiveDocument, 'ActiveView') or not Gui.ActiveDocument.ActiveView:
                log_error("没有活动视图")
                return {"result": "error", "message": "没有活动视图"}
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