"""启动器 - 判断运行模式"""
import sys
import os

# 确保项目根目录在 Python 路径中
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def run_gui():
    """运行 GUI 模式"""
    from pinyin_lex_tool.gui import main
    main()


def run_cli():
    """运行 CLI 模式"""
    from pinyin_lex_tool.cli import main
    main()


def main():
    """主入口 - 根据参数判断运行模式"""
    # 如果有命令行参数，使用 CLI 模式
    # 否则使用 GUI 模式
    if len(sys.argv) > 1:
        run_cli()
    else:
        run_gui()


if __name__ == "__main__":
    main()
