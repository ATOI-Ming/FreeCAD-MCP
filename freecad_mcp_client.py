from typing import Any, Dict
import socket
import json
import asyncio
import re
import sys
import ast
import os
import argparse
import traceback
from pydantic import BaseModel

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:
    print(f"无法导入 FastMCP: {str(e)}\n请运行 `pip install mcp`")
    sys.exit(1)

mod_dir = os.path.join(os.path.expanduser("~"), "FreeCAD", "Mod", "freecad_mcp")
if mod_dir not in sys.path:
    sys.path.append(mod_dir)

mcp = FastMCP("freecad-bridge")
FREECAD_HOST = 'localhost'
FREECAD_PORT = 9876

def normalize_macro_code(code: str) -> str:
    code = code.strip()
    if not code:
        return "# FreeCAD Macro\n"
    lines = code.splitlines()
    has_freecad = any("import FreeCAD" in line for line in lines)
    has_gui = any("import FreeCADGui" in line for line in lines)
    has_part = any("import Part" in line for line in lines)
    has_math = any("import math" in line for line in lines)
    
    result_lines = []
    if not has_freecad:
        result_lines.append("import FreeCAD as App")
    if not has_gui:
        result_lines.append("import FreeCADGui as Gui")
    if not has_part:
        result_lines.append("import Part")
    if not has_math:
        result_lines.append("import math")
    if result_lines:
        result_lines.append("")
    
    result_lines.extend(lines)
    
    if not any("Gui.activeDocument" in line or "Gui.SendMsgToActiveView" in line for line in lines):
        result_lines.extend([
            "",
            "if App.ActiveDocument:",
            "    App.ActiveDocument.recompute()",
            "    Gui.activeDocument().activeView().viewAxometric()",
            "    Gui.SendMsgToActiveView(\"ViewFit\")"
        ])
    
    normalized_code = "\n".join(result_lines)
    print(f"Normalized code:\n{normalized_code}")
    return normalized_code

async def send_to_freecad(command: Dict[str, Any], retries=3, delay=1) -> Dict[str, Any]:
    for attempt in range(retries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((FREECAD_HOST, FREECAD_PORT))
            command_json = json.dumps(command)
            sock.sendall(command_json.encode('utf-8'))
            response = b''
            while True:
                data = sock.recv(32768)
                if not data:
                    break
                response += data
                if len(data) < 32768:
                    break
            sock.close()
            return json.loads(response.decode('utf-8'))
        except Exception as e:
            if attempt < retries - 1:
                print(f"连接尝试 {attempt + 1} 失败: {str(e)}，将在 {delay} 秒后重试...")
                await asyncio.sleep(delay)
                continue
            return {"status": "error", "message": f"{retries} 次尝试后失败: {str(e)}\n{traceback.format_exc()}"}

@mcp.tool()
async def create_macro(macro_name: str, template_type: str = "default") -> str:
    if not re.match(r'^[a-zA-Z0-9_]+$', macro_name):
        return json.dumps({"status": "error", "message": "无效宏文件名: 仅允许字母、数字和下划线"}, indent=2)
    command = {
        "type": "create_macro",
        "params": {
            "macro_name": macro_name,
            "template_type": template_type
        }
    }
    result = await send_to_freecad(command)
    return json.dumps(result, indent=2)

@mcp.tool()
async def update_macro(macro_name: str, code: str) -> str:
    try:
        ast.parse(code)
    except SyntaxError as e:
        return json.dumps({"status": "error", "message": f"代码语法错误: {str(e)}"}, indent=2)
    normalized_code = normalize_macro_code(code)
    command = {
        "type": "update_macro",
        "params": {
            "macro_name": macro_name,
            "code": normalized_code
        }
    }
    result = await send_to_freecad(command)
    return json.dumps(result, indent=2)

@mcp.tool()
async def run_macro(macro_path: str, params: dict = None) -> str:
    macro_path = os.path.normpath(macro_path)
    command = {
        "type": "run_macro",
        "params": {
            "macro_path": macro_path,
            "params": params
        }
    }
    result = await send_to_freecad(command)
    return json.dumps(result, indent=2)

@mcp.tool()
async def validate_macro_code(macro_name: str = None, code: str = None) -> str:
    command = {
        "type": "validate_macro_code",
        "params": {
            "macro_name": macro_name,
            "code": code
        }
    }
    result = await send_to_freecad(command)
    return json.dumps(result, indent=2)

class SetViewArguments(BaseModel):
    view_type: str

@mcp.tool()
async def set_view(params: dict) -> str:
    if isinstance(params.get("view_type"), (int, float)):
        params["view_type"] = str(int(params["view_type"]))
    
    try:
        arguments = SetViewArguments(**params)
        valid_views = ["1", "2", "3", "7"]
        if arguments.view_type not in valid_views:
            return json.dumps({"status": "error", "message": f"无效视图类型: 必须是 {valid_views} 之一"}, indent=2)
        command = {
            "type": "set_view",
            "params": {
                "view_type": arguments.view_type
            }
        }
        result = await send_to_freecad(command)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"执行 set_view 错误: {str(e)}"}, indent=2)

@mcp.tool()
async def get_report() -> str:
    command = {
        "type": "get_report",
        "params": {}
    }
    result = await send_to_freecad(command)
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FreeCAD MCP 桥接")
    parser.add_argument("--host", default="localhost", help="MCP 服务器主机")
    parser.add_argument("--port", type=int, default=9876, help="MCP 服务器端口")
    parser.add_argument("--run-macro", help="要运行的 .FCMacro 文件路径")
    parser.add_argument("--params", help="宏参数的 JSON 字符串", default=None)
    args = parser.parse_args()

    if args.run_macro:
        macro_path = os.path.normpath(args.run_macro)
        params = None
        if args.params:
            try:
                params = json.loads(args.params)
            except json.JSONDecodeError as e:
                print(f"错误: 无效的 JSON 参数: {str(e)}")
                sys.exit(1)
        
        async def execute_macro():
            result = await run_macro(macro_path, params)
            result = json.loads(result)
            if result["status"] == "success":
                print("宏执行成功")
                print(json.dumps(result["result"], indent=2))
            else:
                print(f"错误: {result['message']}")
                if "result" in result and "traceback" in result["result"]:
                    print(f"错误跟踪:\n{result['result']['traceback']}")
                sys.exit(1)
        
        asyncio.run(execute_macro())
    else:
        FREECAD_HOST = args.host
        FREECAD_PORT = args.port
        mcp.run(transport='stdio')