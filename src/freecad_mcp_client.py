# -*- coding: utf-8 -*-
"""
FreeCAD MCP客户端 - 绝对路径优化版本
确保100%的路径解析成功率
"""

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

# MCP stdio transport is UTF-8; Windows consoles default to GBK, which would
# corrupt Chinese text in JSON-RPC messages.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:
    print(f"无法导入 FastMCP: {str(e)}\n请运行 `pip install mcp`", file=sys.stderr)
    sys.exit(1)

mod_dir = os.path.join(os.path.expanduser("~"), "FreeCAD", "Mod", "freecad_mcp")
if mod_dir not in sys.path:
    sys.path.append(mod_dir)

mcp = FastMCP("freecad-bridge-absolute")
FREECAD_HOST = 'localhost'
FREECAD_PORT = 9876

def get_absolute_macro_path(macro_name: str) -> str:
    """
    获取宏文件的绝对路径
    确保路径解析100%成功
    """
    # 获取FreeCAD宏目录
    macro_dir = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "FreeCAD", "Macro")
    
    # 确保有.FCMacro扩展名
    if not macro_name.endswith('.FCMacro'):
        macro_name = f"{macro_name}.FCMacro"
    
    # 返回绝对路径
    absolute_path = os.path.join(macro_dir, macro_name)
    return absolute_path

def normalize_macro_code(code: str) -> str:
    """标准化宏代码"""
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
    return "\n".join(result_lines)

async def send_command_to_freecad(command: Dict[str, Any]) -> Dict[str, Any]:
    """发送命令到FreeCAD服务器"""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(FREECAD_HOST, FREECAD_PORT), timeout=10
        )

        # 发送命令
        command_json = json.dumps(command, ensure_ascii=False)
        writer.write(command_json.encode('utf-8'))
        await writer.drain()

        # 接收响应（响应可能分多个 TCP 包到达，持续读取直到可解析）
        response_data = b""
        response = None
        while True:
            chunk = await asyncio.wait_for(reader.read(65536), timeout=30)
            if not chunk:
                break
            response_data += chunk
            try:
                response = json.loads(response_data.decode('utf-8'))
                break
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
        if response is None:
            raise ValueError("FreeCAD 返回了无法解析的响应")

        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass

        return response

    except Exception as e:
        return {"result": "error", "message": f"连接FreeCAD服务器失败: {str(e)}"}

@mcp.tool()
def create_macro(macro_name: str, template_type: str = "default") -> Dict[str, Any]:
    """
    创建FreeCAD宏文件 - 绝对路径版本
    
    Args:
        macro_name: 宏文件名称 (仅允许字母、数字、下划线和连字符)
        template_type: 模板类型 (default, basic, part, sketch)
    """
    try:
        # 验证宏名称
        if not re.match(r'^[a-zA-Z0-9_-]+$', macro_name):
            return {"result": "error", "message": "宏名称只能包含字母、数字、下划线和连字符"}
        
        # 获取绝对路径
        absolute_path = get_absolute_macro_path(macro_name)
        print(f"创建宏文件: {absolute_path}", file=sys.stderr)
        
        command = {
            "type": "create_macro",
            "params": {
                "macro_name": macro_name,
                "template_type": template_type
            }
        }
        
        # 检查是否已有运行中的事件循环，避免冲突
        try:
            loop = asyncio.get_running_loop()
            # 如果有运行中的循环，使用线程池执行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, send_command_to_freecad(command))
                result = future.result(timeout=30)
        except RuntimeError:
            # 没有运行中的循环，可以直接使用 asyncio.run
            result = asyncio.run(send_command_to_freecad(command))
        
        return result
        
    except Exception as e:
        return {"result": "error", "message": str(e), "traceback": traceback.format_exc()}

@mcp.tool()
def update_macro(macro_name: str, code: str) -> Dict[str, Any]:
    """
    更新FreeCAD宏文件内容 - 绝对路径版本
    
    Args:
        macro_name: 宏文件名称
        code: Python代码内容
    """
    try:
        # 获取绝对路径
        absolute_path = get_absolute_macro_path(macro_name)
        print(f"更新宏文件: {absolute_path}", file=sys.stderr)
        
        # 标准化代码
        normalized_code = normalize_macro_code(code)
        
        command = {
            "type": "update_macro",
            "params": {
                "macro_name": macro_name,
                "code": normalized_code
            }
        }
        
        # 检查是否已有运行中的事件循环，避免冲突
        try:
            loop = asyncio.get_running_loop()
            # 如果有运行中的循环，使用线程池执行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, send_command_to_freecad(command))
                result = future.result(timeout=30)
        except RuntimeError:
            # 没有运行中的循环，可以直接使用 asyncio.run
            result = asyncio.run(send_command_to_freecad(command))
        
        return result
        
    except Exception as e:
        return {"result": "error", "message": str(e), "traceback": traceback.format_exc()}

@mcp.tool()
def run_macro(macro_path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    运行FreeCAD宏 - 绝对路径版本
    
    Args:
        macro_path: 宏文件路径（将自动转换为绝对路径）
        params: 可选参数
    """
    try:
        # 相对路径/宏名交给 FreeCAD 服务端解析：它才知道自己版本化的宏目录
        # （FreeCAD 1.1 使用 v1-1 之类的版本子目录，客户端无法硬编码）。
        if os.path.isabs(macro_path):
            target_path = macro_path
        else:
            target_path = os.path.basename(macro_path)
            if not target_path.endswith('.FCMacro'):
                target_path = f"{target_path}.FCMacro"

        print(f"执行宏文件: {target_path}", file=sys.stderr)

        command = {
            "type": "run_macro",
            "params": {
                "macro_path": target_path,
                "params": params if params is not None else {}
            }
        }
        
        # 检查是否已有运行中的事件循环，避免冲突
        try:
            loop = asyncio.get_running_loop()
            # 如果有运行中的循环，使用线程池执行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, send_command_to_freecad(command))
                result = future.result(timeout=30)
        except RuntimeError:
            # 没有运行中的循环，可以直接使用 asyncio.run
            result = asyncio.run(send_command_to_freecad(command))
        
        return result
        
    except Exception as e:
        return {"result": "error", "message": str(e), "traceback": traceback.format_exc()}

@mcp.tool()
def validate_macro_code(macro_name: str = None, code: str = None) -> Dict[str, Any]:
    """
    验证宏代码语法
    
    Args:
        macro_name: 宏文件名称（可选）
        code: 代码内容（可选）
    """
    try:
        if macro_name:
            absolute_path = get_absolute_macro_path(macro_name)
            print(f"验证宏文件: {absolute_path}", file=sys.stderr)
        
        command = {
            "type": "validate_macro_code",
            "params": {
                "macro_name": macro_name if macro_name is not None else "",
                "code": code if code is not None else ""
            }
        }
        
        # 检查是否已有运行中的事件循环，避免冲突
        try:
            loop = asyncio.get_running_loop()
            # 如果有运行中的循环，使用线程池执行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, send_command_to_freecad(command))
                result = future.result(timeout=30)
        except RuntimeError:
            # 没有运行中的循环，可以直接使用 asyncio.run
            result = asyncio.run(send_command_to_freecad(command))
        
        return result
        
    except Exception as e:
        return {"result": "error", "message": str(e), "traceback": traceback.format_exc()}

@mcp.tool()
def set_view(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    设置FreeCAD视图
    
    Args:
        params: 视图参数
    """
    try:
        command = {
            "type": "set_view",
            "params": params
        }
        
        # 检查是否已有运行中的事件循环，避免冲突
        try:
            loop = asyncio.get_running_loop()
            # 如果有运行中的循环，使用线程池执行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, send_command_to_freecad(command))
                result = future.result(timeout=30)
        except RuntimeError:
            # 没有运行中的循环，可以直接使用 asyncio.run
            result = asyncio.run(send_command_to_freecad(command))
        
        return result
        
    except Exception as e:
        return {"result": "error", "message": str(e), "traceback": traceback.format_exc()}

@mcp.tool()
def get_report() -> Dict[str, Any]:
    """获取FreeCAD服务器报告"""
    try:
        command = {
            "type": "get_report",
            "params": {}
        }
        
        # 检查是否已有运行中的事件循环，避免冲突
        try:
            loop = asyncio.get_running_loop()
            # 如果有运行中的循环，使用线程池执行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, send_command_to_freecad(command))
                result = future.result(timeout=30)
        except RuntimeError:
            # 没有运行中的循环，可以直接使用 asyncio.run
            result = asyncio.run(send_command_to_freecad(command))
        
        return result
        
    except Exception as e:
        return {"result": "error", "message": str(e), "traceback": traceback.format_exc()}

def _parse_json_arg(raw, name):
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"参数 {name} 不是合法 JSON: {e}", file=sys.stderr)
        sys.exit(2)


def _parse_code_arg(raw):
    # Shells don't expand \n inside quoted arguments, so accept literal "\n"
    # as a newline to keep the documented one-line examples usable.
    if raw is None:
        return None
    return raw.replace("\\n", "\n")


def run_cli(args):
    """执行单条命令行请求（不经 MCP，直接走 TCP）。"""
    if args.create_macro:
        return create_macro(args.create_macro, args.template_type)
    if args.update_macro:
        return update_macro(args.update_macro, _parse_code_arg(args.code) or "")
    if args.run_macro:
        params = _parse_json_arg(args.params, "--params") if args.params else None
        return run_macro(args.run_macro, params)
    if args.validate_macro_code is not None:
        return validate_macro_code(args.validate_macro_code or None, _parse_code_arg(args.code))
    if args.set_view is not None:
        return set_view(_parse_json_arg(args.set_view, "--set-view"))
    if args.get_report:
        return get_report()
    return None


def main():
    """主函数：带子命令时执行单条请求，否则以 stdio MCP 服务器运行。"""
    parser = argparse.ArgumentParser(description='FreeCAD MCP客户端')
    parser.add_argument('--host', default='localhost', help='FreeCAD服务器主机')
    parser.add_argument('--port', type=int, default=9876, help='FreeCAD服务器端口')

    commands = parser.add_mutually_exclusive_group()
    commands.add_argument('--create-macro', metavar='NAME', help='创建宏文件')
    commands.add_argument('--update-macro', metavar='NAME', help='更新宏文件内容（配合 --code）')
    commands.add_argument('--run-macro', metavar='MACRO', help='运行宏（相对宏名由 FreeCAD 服务端解析）')
    commands.add_argument('--validate-macro-code', metavar='NAME', nargs='?', const='',
                          help='校验宏代码（配合 --code；NAME 可选）')
    commands.add_argument('--set-view', metavar='JSON', help='设置视图，例如 {"view_type": "7"}')
    commands.add_argument('--get-report', action='store_true', help='获取服务器日志')

    parser.add_argument('--template-type', default='default',
                        choices=['default', 'basic', 'part', 'sketch'], help='宏模板类型')
    parser.add_argument('--code', help='宏代码内容')
    parser.add_argument('--params', help='运行宏时的 JSON 参数')

    args = parser.parse_args()

    global FREECAD_HOST, FREECAD_PORT
    FREECAD_HOST = args.host
    FREECAD_PORT = args.port

    result = run_cli(args)
    if result is not None:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result.get("result") == "success" else 1)

    print(f"FreeCAD MCP客户端启动", file=sys.stderr)
    print(f"连接到: {FREECAD_HOST}:{FREECAD_PORT}", file=sys.stderr)

    # 启动MCP服务器
    mcp.run()

if __name__ == "__main__":
    main()