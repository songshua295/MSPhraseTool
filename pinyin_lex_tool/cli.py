"""命令行接口"""
import argparse
import sys
from typing import Optional

from .service import PinyinLexService
from .lex_reader import LexFileReader


def get_user_lex_path() -> str:
    """获取用户微软拼音自定义短语文件路径"""
    import os
    appdata = os.environ.get("APPDATA", "")
    if not appdata:
        raise RuntimeError("无法获取 APPDATA 环境变量")
    return os.path.join(appdata, "Microsoft", "InputMethod", "Chs", "ChsPinyinEUDPv1.lex")


def cmd_export(args: argparse.Namespace) -> int:
    """导出命令"""
    lex_path = args.lex if args.lex else get_user_lex_path()
    
    # 如果没有指定输出文件，使用默认文件名
    if not args.output:
        args.output = '自定义短语.csv'
    
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
    
    print("=== MSPhraseTool 调试信息 ===")
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


def cmd_convert(args: argparse.Namespace) -> int:
    """短语类型转换命令"""
    import subprocess
    from pathlib import Path
    
    # 获取转换脚本路径
    script_dir = Path(__file__).parent.parent / "tool"
    convert_script = script_dir / "phrase_converter.py"
    
    if not convert_script.exists():
        print(f"错误：转换脚本不存在：{convert_script}")
        return 1
    
    # 构建命令行参数
    cmd = [sys.executable, str(convert_script)]
    
    if args.format:
        cmd.extend(["--format", str(args.format)])
    
    if args.input:
        cmd.extend(["--input", args.input])
    
    if args.output:
        cmd.extend(["--output", args.output])
    
    if args.list_formats:
        cmd.append("--list-formats")
    
    # 执行转换脚本
    try:
        result = subprocess.run(cmd)
        return result.returncode
    except Exception as e:
        print(f"执行转换脚本时出错：{e}")
        return 1


def cmd_delete(args: argparse.Namespace) -> int:
    """删除自定义短语命令"""
    import subprocess
    from pathlib import Path
    
    # 获取删除脚本路径
    script_dir = Path(__file__).parent.parent / "tool"
    delete_script = script_dir / "delete_microsoft_phrases.py"
    
    if not delete_script.exists():
        print(f"错误：删除脚本不存在：{delete_script}")
        return 1
    
    # 构建命令行参数
    cmd = [sys.executable, str(delete_script)]
    
    if args.force:
        cmd.append("--force")
    
    if args.dry_run:
        cmd.append("--dry-run")
    
    # 执行删除脚本
    try:
        result = subprocess.run(cmd)
        return result.returncode
    except Exception as e:
        print(f"执行删除脚本时出错：{e}")
        return 1


def cmd_upload(args: argparse.Namespace) -> int:
    """上传文件到 S3 命令"""
    import subprocess
    from pathlib import Path
    
    # 获取上传脚本路径
    script_dir = Path(__file__).parent.parent / "tool"
    upload_script = script_dir / "upload_to_s3.py"
    
    if not upload_script.exists():
        print(f"错误：上传脚本不存在：{upload_script}")
        return 1
    
    # 构建命令行参数
    cmd = [sys.executable, str(upload_script)]
    
    # 执行上传脚本
    try:
        result = subprocess.run(cmd)
        return result.returncode
    except Exception as e:
        print(f"执行上传脚本时出错：{e}")
        return 1


def cmd_edit(args: argparse.Namespace) -> int:
    """交互式修改单个短语命令"""
    lex_path = args.lex if args.lex else get_user_lex_path()
    service = PinyinLexService(LexFileReader())
    
    print("=== 交互式短语修改 ===")
    print(f"当前 .lex 文件：{lex_path}")
    
    # 步骤 1：输入拼音
    while True:
        pinyin = input("请输入拼音（或输入 'quit' 退出）: ").strip()
        if pinyin.lower() == 'quit':
            return 0
        if not pinyin:
            print("拼音不能为空，请重新输入")
            continue
        if not service._validate_pinyin(pinyin):
            print("拼音格式不正确，只能包含字母，最多 32 个字符")
            continue
        break
    
    # 步骤2：显示现有短语
    print(f"\n拼音 '{pinyin}' 的现有短语：")
    existing_phrases = service.list_phrases(lex_path, pinyin)
    
    if not existing_phrases:
        print("  （没有找到现有短语）")
    else:
        print(f"{'索引':<6} {'文本'}")
        print("-" * 30)
        for phrase in existing_phrases:
            print(f"{phrase.index:<6} {phrase.text}")
    
    # 步骤3：输入索引
    while True:
        index_input = input(f"\n请输入要修改/插入的索引 (1-9) 或输入 'quit' 退出: ").strip()
        if index_input.lower() == 'quit':
            return 0
        try:
            index = int(index_input)
            if index < 1 or index > 9:
                print("索引必须在 1-9 之间")
                continue
            break
        except ValueError:
            print("请输入有效的数字")
            continue
    
    # 检查该索引是否已有内容
    existing_at_index = None
    for phrase in existing_phrases:
        if phrase.index == index:
            existing_at_index = phrase
            break
    
    if existing_at_index:
        print(f"索引 {index} 当前内容：{existing_at_index.text}")
        action = "修改"
    else:
        print(f"索引 {index} 当前为空")
        action = "插入"
    
    # 步骤4：输入文本
    while True:
        text = input(f"请输入要{action}的文本（或输入 'quit' 退出，输入空格或 'esc' 删除）: ").strip()
        if text.lower() == 'quit':
            return 0
        
        # 检查是否要删除
        if not text or text.lower() == 'esc':
            if action == "修改":
                # 确认删除
                confirm = input(f"确定要删除索引 {index} 的短语 '{existing_at_index.text}' 吗？(y/N): ").strip().lower()
                if confirm == 'y':
                    try:
                        deleted = service.delete_single_phrase(lex_path, pinyin.lower(), index, existing_at_index.text)
                        if deleted:
                            print(f"✓ 已删除索引 {index} 的短语")
                        else:
                            print("删除失败")
                        return 0
                    except Exception as e:
                        print(f"错误：{e}")
                        return 1
                else:
                    print("操作已取消")
                    return 0
            else:
                print("文本不能为空")
                continue
        
        if len(text) > 64:
            print("文本长度不能超过64个字符")
            continue
        break
    
    # 检查该文本是否已在其他位置
    existing_with_text = None
    for phrase in existing_phrases:
        if phrase.text == text and phrase.index != index:
            existing_with_text = phrase
            break
    
    if existing_with_text:
        print(f"注意：文本 '{text}' 已存在于索引 {existing_with_text.index}")
        confirm = input(f"是否将其移动到索引 {index}？(y/N): ").strip().lower()
        if confirm != 'y':
            print("操作已取消")
            return 0
    
    # 执行更新
    try:
        result = service.update_single_phrase(lex_path, pinyin.lower(), index, text)
        if result['moved']:
            print(f"✓ 已将文本 '{text}' 从索引 {result['old_index']} 移动到索引 {index}")
        elif result['updated']:
            print(f"✓ 已修改索引 {index} 的文本为：{text}")
        else:
            print(f"✓ 已在索引 {index} 插入新文本：{text}")
        
        print(f"拼音 '{pinyin}' 的短语更新完成")
        return 0
    except Exception as e:
        print(f"错误：{e}")
        return 1


def main(args: Optional[list] = None) -> int:
    """主入口"""
    parser = argparse.ArgumentParser(
        prog='main',
        description='微软拼音输入法自定义短语批量导入/导出工具&自定义短语格式转换工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
可用命令:
  export    导出系统当前自定义短语到 CSV 文件
    用法: main export [output] [--lex LEX]
    参数: 
      output    输出文件路径 (CSV)，不指定时默认为"自定义短语.csv"
      --lex     可选：指定 .lex 文件路径

  import    从 TXT 导入短语到 .lex
    用法: main import <input> [--lex LEX] [--no-backup] [--dry-run] [--verbose]
    参数:
      input       输入 TXT 文件路径
      --lex       可选：指定 .lex 文件路径
      --no-backup 禁用备份
      --dry-run   只校验不落盘
      --verbose   输出详细信息

  list      列出现有短语
    用法: main list [--filter FILTER] [--lex LEX]
    参数:
      --filter    可选：按拼音过滤
      --lex       可选：指定 .lex 文件路径

  debug     显示调试信息
    用法: main debug [--verbose]
    参数:
      --verbose   显示详细信息

  convert   短语类型转换（百度/搜狗/微软/Rime/多多/CSV互转）
    用法: main convert --format FORMAT --input FILE [--output DIR] [--list-formats]
    参数:
      --format, -f    源文件格式 (bd:百度，sg:搜狗，wr:微软，rime:Rime, dd:多多, csv:CSV)
      --input, -i     源文件路径
      --output, -o    输出文件夹路径 (默认：out)
      --list-formats, -l  列出支持的格式

  delete    删除微软拼音自定义短语
    用法: main delete [--force] [--dry-run]
    参数:
      --force, -f     强制删除，不提示确认
      --dry-run, -n   只显示将要删除的文件，不实际删除

  edit      交互式修改单个短语
    用法：main edit [--lex LEX]
    参数:
      --lex       可选：指定 .lex 文件路径
    说明：交互式修改，会提示输入拼音、索引和文本

  upload    上传文件到 S3 存储
    用法：main upload
    说明：根据 .env 配置上传 lex 文件和其他文件到 S3 存储，显示 URL 列表和安装命令

示例:
  main export phrases.txt
  main import phrases.txt
  main list --filter hx
  main debug --verbose
  main convert --format bd --input baidu.txt
  main delete --dry-run
  main edit
  main upload
  
使用 "main <命令> --help" 查看命令的详细帮助信息
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # export 命令
    export_parser = subparsers.add_parser('export', help='导出系统当前自定义短语到 CSV 文件')
    export_parser.add_argument('output', nargs='?', help='输出文件路径 (CSV)，不指定时默认为"自定义短语.csv"')
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

    # convert 命令
    convert_parser = subparsers.add_parser('convert', help='短语类型转换（百度/搜狗/微软/Rime/多多互转）')
    convert_parser.add_argument('--format', '-f', type=str, choices=['bd', 'sg', 'wr', 'rime', 'dd', 'csv'], 
                                help='源文件格式 (bd:百度，sg:搜狗，wr:微软，rime:Rime, dd:多多, csv:CSV)')
    convert_parser.add_argument('--input', '-i', type=str, help='源文件路径')
    convert_parser.add_argument('--output', '-o', type=str, default='out', help='输出文件夹路径 (默认：out)')
    convert_parser.add_argument('--list-formats', '-l', action='store_true', help='列出支持的格式')
    convert_parser.set_defaults(func=cmd_convert)

    # delete 命令
    delete_parser = subparsers.add_parser('delete', help='删除微软拼音自定义短语')
    delete_parser.add_argument('--force', '-f', action='store_true', help='强制删除，不提示确认')
    delete_parser.add_argument('--dry-run', '-n', action='store_true', help='只显示将要删除的文件，不实际删除')
    delete_parser.set_defaults(func=cmd_delete)

    # edit 命令
    edit_parser = subparsers.add_parser('edit', help='交互式修改单个短语')
    edit_parser.add_argument('--lex', help='可选：指定 .lex 文件路径')
    edit_parser.set_defaults(func=cmd_edit)

    # upload 命令
    upload_parser = subparsers.add_parser('upload', help='上传文件到 S3 存储')
    upload_parser.set_defaults(func=cmd_upload)

    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        return 1

    return parsed_args.func(parsed_args)


if __name__ == '__main__':
    sys.exit(main())
