"""启动器 - CLI 模式"""
import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def main():
    from pinyin_lex_tool.cli import main as cli_main
    cli_main()


if __name__ == "__main__":
    main()
