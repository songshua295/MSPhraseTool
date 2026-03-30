"""命令行接口"""
import argparse
import sys
from typing import Optional

from .service import PinyinLexService
from .lex_reader import LexFileReader
from .paths import get_user_lex_path


def cmd_export(args: argparse.Namespace) -> int:
    """导出命令"""
    lex_path = args.lex if args.lex else get_user_lex_path()
    service = PinyinLexService(LexFileReader())
    service.export(lex_path, args.output)
    print(f"导出完成：{args.output}")
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    """导入命令"""
    lex_path = args.lex if args.lex else get_user_lex_path()
    service = PinyinLexService(LexFileReader())
    service.import_phrases(
        lex_path, 
        args.input, 
        backup=not args.no_backup,
        dry_run=args.dry_run,
        verbose=args.verbose
    )
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """列出短语命令"""
    lex_path = args.lex if args.lex else get_user_lex_path()
    service = PinyinLexService(LexFileReader())
    phrases = service.list_phrases(lex_path, args.filter)
    
    if not phrases:
        print("没有找到短语")
        return 0
    
    print(f"{'拼音':<20} {'位置':^6} {'文本'}")
    print("-" * 60)
    for p in phrases:
        print(f"{p.pinyin:<20} {p.index:^6} {p.text}")
    
    return 0


def cmd_debug(args: argparse.Namespace) -> int:
    """调试命令"""
    import sys
    from datetime import datetime
    from pathlib import Path
    
    print("=== PinyinLexTool 调试信息 ===")
    print(f"版本：1.0.1")
    print(f"运行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"操作系统：{sys.platform}")
    print(f"运行时：{sys.version}")
    print(f"工作目录：{Path.cwd()}")
    
    try:
        lex_path = get_user_lex_path()
        print(f"默认 .lex 路径：{lex_path}")
        
        if Path(lex_path).exists():
            file_stat = Path(lex_path).stat()
            print(f"文件存在：是")
            print(f"文件大小：{file_stat.st_size} 字节")
            print(f"最后修改：{datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
            
            if args.verbose:
                try:
                    service = PinyinLexService(LexFileReader())
                    phrases = service.list_phrases(lex_path)
                    print(f"短语数量：{len(phrases)}")
                    
                    if phrases:
                        print("前 5 个短语:")
                        for p in phrases[:5]:
                            print(f"  {p.pinyin} {p.index} {p.text}")
                except Exception as e:
                    print(f"读取文件时出错：{e}")
        else:
            print(f"文件存在：否")
    except Exception as e:
        print(f"错误：{e}")
        return 1
    
    print("=== 调试信息结束 ===")
    return 0


def main(args: Optional[list] = None) -> int:
    """主入口"""
    parser = argparse.ArgumentParser(
        prog='PinyinLexTool',
        description='微软拼音输入法自定义短语批量导入/导出工具'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # export 命令
    export_parser = subparsers.add_parser('export', help='导出系统当前自定义短语到 TXT 文件')
    export_parser.add_argument('output', metavar='<output>', help='输出文件路径 (TXT)')
    export_parser.add_argument('--lex', help='可选：指定 .lex 文件路径')
    export_parser.set_defaults(func=cmd_export)

    # import 命令
    import_parser = subparsers.add_parser('import', help='从 TXT 导入短语到 .lex')
    import_parser.add_argument('input', metavar='<input>', help='输入 TXT 文件路径')
    import_parser.add_argument('--lex', help='可选：指定 .lex 文件路径')
    import_parser.add_argument('--no-backup', action='store_true', help='禁用备份')
    import_parser.add_argument('--dry-run', action='store_true', help='只校验不落盘')
    import_parser.add_argument('--verbose', action='store_true', help='输出详细信息')
    import_parser.set_defaults(func=cmd_import)

    # list 命令
    list_parser = subparsers.add_parser('list', help='列出现有短语')
    list_parser.add_argument('--filter', help='可选：按拼音过滤')
    list_parser.add_argument('--lex', help='可选：指定 .lex 文件路径')
    list_parser.set_defaults(func=cmd_list)

    # debug 命令
    debug_parser = subparsers.add_parser('debug', help='显示调试信息')
    debug_parser.add_argument('--verbose', action='store_true', help='显示详细信息')
    debug_parser.set_defaults(func=cmd_debug)

    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        return 1

    return parsed_args.func(parsed_args)


if __name__ == '__main__':
    sys.exit(main())
