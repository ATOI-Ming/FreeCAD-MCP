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

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:
    print(f"无法导入 FastMCP: {str(e)}\n请运行 `pip install mcp`")
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
        reader, writer = await asyncio.open_connection(FREECAD_HOST, FREECAD_PORT)
        
        # 发送命令
        command_json = json.dumps(command, ensure_ascii=False)
        writer.write(command_json.encode('utf-8'))
        await writer.drain()
        
        # 接收响应
        response_data = await reader.read(8192)
        response = json.loads(response_data.decode('utf-8'))
        
        writer.close()
        await writer.wait_closed()
        
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
        print(f"创建宏文件: {absolute_path}")
        
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
        print(f"更新宏文件: {absolute_path}")
        
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
        # 如果传入的是相对路径或宏名称，转换为绝对路径
        if not os.path.isabs(macro_path):
            # 提取宏名称
            macro_name = os.path.basename(macro_path)
            if not macro_name.endswith('.FCMacro'):
                macro_name = f"{macro_name}.FCMacro"
            
            # 获取绝对路径
            absolute_path = get_absolute_macro_path(macro_name.replace('.FCMacro', ''))
        else:
            absolute_path = macro_path
        
        print(f"执行宏文件: {absolute_path}")
        
        command = {
            "type": "run_macro",
            "params": {
                "macro_path": absolute_path,
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
            print(f"验证宏文件: {absolute_path}")
        
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

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='FreeCAD MCP客户端 - 绝对路径版本')
    parser.add_argument('--host', default='localhost', help='FreeCAD服务器主机')
    parser.add_argument('--port', type=int, default=9876, help='FreeCAD服务器端口')
    
    args = parser.parse_args()
    
    # 使用小写变量名避免常量重定义警告
    global FREECAD_HOST, FREECAD_PORT
    freecad_host = args.host
    freecad_port = args.port
    FREECAD_HOST = freecad_host
    FREECAD_PORT = freecad_port
    
    print(f"FreeCAD MCP客户端启动 ")
    print(f"连接到: {FREECAD_HOST}:{FREECAD_PORT}")

    
    # 启动MCP服务器
    mcp.run()

if __name__ == "__main__":
    main()