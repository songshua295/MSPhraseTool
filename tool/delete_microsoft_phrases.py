#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
删除微软拼音自定义短语工具
删除用户自定义短语文件：ChsPinyinEUDPv1.lex
"""

import os
import sys
from pathlib import Path


def get_lex_path():
    """获取微软拼音自定义短语文件路径"""
    appdata = os.environ.get("APPDATA", "")
    if not appdata:
        print("错误：无法获取 APPDATA 环境变量")
        return None
    lex_path = os.path.join(appdata, "Microsoft", "InputMethod", "Chs", "ChsPinyinEUDPv1.lex")
    return lex_path


def delete_lex_file(force=False):
    """删除自定义短语文件
    
    Args:
        force: 是否强制删除，不提示确认
        
    Returns:
        bool: 删除是否成功
    """
    lex_path = get_lex_path()
    
    if not lex_path:
        print("错误：无法获取 .lex 文件路径")
        return False
    
    lex_file = Path(lex_path)
    
    if not lex_file.exists():
        print(f"文件不存在：{lex_path}")
        print("当前没有自定义短语需要删除")
        return True
    
    # 确认删除
    if not force:
        print(f"即将删除文件：{lex_path}")
        print("此操作将删除所有微软拼音自定义短语！")
        confirm = input("确认删除？(y/N): ").strip().lower()
        if confirm != "y":
            print("已取消删除")
            return False
    
    try:
        lex_file.unlink()
        print(f"已成功删除：{lex_path}")
        print("请重启输入法或相关应用程序以使更改生效")
        return True
    except PermissionError:
        print(f"错误：无法删除文件，可能是文件被占用")
        print("请关闭使用输入法的应用程序后重试")
        return False
    except Exception as e:
        print(f"删除失败：{e}")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="删除微软拼音自定义短语文件"
    )
    
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="强制删除，不提示确认"
    )
    
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="只显示将要删除的文件，不实际删除"
    )
    
    args = parser.parse_args()
    
    lex_path = get_lex_path()
    
    if not lex_path:
        sys.exit(1)
    
    lex_file = Path(lex_path)
    
    if not lex_file.exists():
        print(f"文件不存在：{lex_path}")
        print("当前没有自定义短语需要删除")
        sys.exit(0)
    
    if args.dry_run:
        print(f"[Dry Run] 将要删除：{lex_path}")
        sys.exit(0)
    
    success = delete_lex_file(force=args.force)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
