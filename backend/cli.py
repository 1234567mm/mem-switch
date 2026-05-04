#!/usr/bin/env python3
"""
Mem-Switch Backend CLI Entry Point
用于 PyInstaller 打包的独立可执行文件入口
"""
import os
import sys

# 设置环境变量确保正确的默认行为
os.environ.setdefault('MEM_SWITCH_PORT', '8000')

# 从 backend.main 导入 FastAPI app 实例
from main import app

# 导入 uvicorn 用于启动
import uvicorn


def main():
    """主入口函数"""
    # 从环境变量读取端口，默认 8000
    port = int(os.environ.get('MEM_SWITCH_PORT', '8000'))
    host = '127.0.0.1'  # 固定绑定本地地址

    print(f"Mem-Switch Backend starting on {host}:{port}")
    print(f"Python version: {sys.version}")
    print(f"Process ID: {os.getpid()}")

    # 使用 uvicorn 运行 FastAPI 应用
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
