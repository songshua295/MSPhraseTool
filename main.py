"""
MSPhraseTool - 微软拼音短语管理工具
主入口文件 - 自动判断运行模式
"""
import sys
import os

# 确保项目根目录在 Python 路径中
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def main():
    """主入口 - 调用 launcher 判断运行模式"""
    from launcher import main as launcher_main
    launcher_main()


if __name__ == "__main__":
    main()
