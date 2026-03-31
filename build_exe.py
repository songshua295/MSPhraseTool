#!/usr/bin/env python3
"""
MSPhraseTool 打包脚本
用于将项目打包成独立的可执行文件
支持构建不同架构的EXE文件
"""

import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path

def clean_build_dirs():
    """清理构建目录"""
    # 要清理的目录
    dirs_to_clean = ['build', 'dist', 'dist_64bit', 'dist_32bit']
    
    # 清理目录
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name) and os.path.isdir(dir_name):
            print(f"清理目录: {dir_name}")
            shutil.rmtree(dir_name)
    
    # 清理spec文件
    spec_files = ['MSPhraseTool.spec']
    for file_name in spec_files:
        if os.path.exists(file_name) and os.path.isfile(file_name):
            print(f"清理文件: {file_name}")
            os.remove(file_name)
    
    # 清理可能存在的bat文件（使用通配符模式）
    import glob
    bat_files = glob.glob('MSPhraseTool_*.bat') + glob.glob('MSPhraseTool_v*.bat')
    for file_name in bat_files:
        if os.path.exists(file_name) and os.path.isfile(file_name):
            print(f"清理文件: {file_name}")
            os.remove(file_name)

def create_spec_file():
    """创建PyInstaller spec文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 包含工具模块
        ('tool/*.py', 'tool'),
        # 包含pinyin_lex_tool模块
        ('pinyin_lex_tool/__init__.py', 'pinyin_lex_tool'),
        ('pinyin_lex_tool/*.py', 'pinyin_lex_tool'),
        # 包含README和LICENSE
        ('README.md', '.'),
        ('LICENSE', '.'),
        # 包含配置文件模板
        ('.env.案例', '.'),
    ],
    hiddenimports=[
        'chardet',
        'boto3',
        'boto3.resources',
        'boto3.session',
        'botocore',
        'botocore.exceptions',
        'botocore.client',
        'dotenv',
        'pinyin_lex_tool',
        'pinyin_lex_tool.cli',
        'pinyin_lex_tool.service',
        'pinyin_lex_tool.lex_reader',
        'pinyin_lex_tool.lex_writer',
        'pinyin_lex_tool.models',
        'pinyin_lex_tool.paths',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)

# 添加运行时钩子来处理Windows控制台
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MSPhraseTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 保持控制台窗口可见
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标文件路径
)

# 如果需要单文件exe，使用下面的配置
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='MSPhraseTool'
# )
'''
    
    with open('MSPhraseTool.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("创建: MSPhraseTool.spec")

def build_exe(arch='auto'):
    """
    构建可执行文件
    
    Args:
        arch: 目标架构，可选值：
            - 'auto': 自动检测当前Python架构（默认）
            - '64bit': 构建64位版本
            - '32bit': 构建32位版本
    """
    print(f"开始构建可执行文件...")
    
    # 确定目标架构
    if arch == 'auto':
        import platform
        current_arch = platform.architecture()[0]
        print(f"自动检测到当前Python架构: {current_arch}")
        target_arch = '64bit' if '64' in current_arch else '32bit'
    else:
        target_arch = arch
    
    
    # 生成包含架构和版本的文件名
    exe_name = f"MSPhraseTool_{target_arch}"
    print(f"目标架构: {target_arch}")
    print(f"EXE文件名: {exe_name}")
    
    # 基础命令
    cmd = [
        'pyinstaller',
        '--onefile',  # 单文件exe
        f'--name={exe_name}',
        '--console',  # 控制台程序
        '--add-data=tool;tool',  # 包含tool目录
        '--add-data=pinyin_lex_tool;pinyin_lex_tool',  # 包含pinyin_lex_tool目录
        '--hidden-import=chardet',
        '--hidden-import=boto3',
        '--hidden-import=boto3.resources',
        '--hidden-import=boto3.session',
        '--hidden-import=botocore',
        '--hidden-import=botocore.exceptions',
        '--hidden-import=botocore.client',
        '--hidden-import=dotenv',
        '--hidden-import=glob',
        '--hidden-import=pinyin_lex_tool',
        '--hidden-import=pinyin_lex_tool.cli',
        '--hidden-import=pinyin_lex_tool.service',
        '--hidden-import=pinyin_lex_tool.lex_reader',
        '--hidden-import=pinyin_lex_tool.lex_writer',
        '--hidden-import=pinyin_lex_tool.models',
        '--hidden-import=pinyin_lex_tool.paths',
        '--clean',  # 清理临时文件
    ]
    
    # 根据架构添加不同的输出目录
    output_dir = f'dist_{target_arch}'
    cmd.extend(['--distpath', output_dir])
    
    # 添加主程序文件
    cmd.append('main.py')
    
    print(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("构建成功!")
        print(f"输出目录: {os.path.abspath(output_dir)}")
        
        # 显示生成的文件
        dist_dir = Path(output_dir)
        if dist_dir.exists():
            print("\n生成的文件:")
            for file in dist_dir.iterdir():
                print(f"  - {file.name} ({file.stat().st_size / 1024 / 1024:.2f} MB)")
    else:
        print("构建失败!")
        print("标准输出:", result.stdout)
        print("错误输出:", result.stderr)
        return False
    
    return exe_name

def create_bat_wrapper(arch='auto', exe_name=None):
    """
    创建批处理文件包装器，方便使用
    
    Args:
        arch: 目标架构，用于确定EXE文件路径
        exe_name: EXE文件名（不含扩展名）
    """
    # 确定目标架构
    if arch == 'auto':
        import platform
        current_arch = platform.architecture()[0]
        target_arch = '64bit' if '64' in current_arch else '32bit'
    else:
        target_arch = arch
    
    # 如果没有提供exe_name，则使用默认名称
    exe_name = f"MSPhraseTool_{target_arch}"
    
    exe_path = f'dist_{target_arch}/{exe_name}.exe'
    
    bat_content = f'''@echo off
chcp 65001 >nul
echo MSPhraseTool - 微软拼音短语管理工具 ({target_arch})
echo.
if "%1"=="" (
    "{exe_path}" --help
) else (
    "{exe_path}" %*
)
pause
'''
    
    bat_filename = f'{exe_name}.bat'
    with open(bat_filename, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    print(f"创建: {bat_filename} (包装器，指向 {exe_path})")
    
    return bat_filename

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='MSPhraseTool 打包工具')
    parser.add_argument('--arch', choices=['auto', '64bit', '32bit'], default='auto',
                       help='目标架构: auto(自动检测), 64bit(64位), 32bit(32位)')
    parser.add_argument('--clean-only', action='store_true',
                       help='仅清理构建目录，不进行构建')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("MSPhraseTool 打包工具")
    print("=" * 60)
    print(f"目标架构: {args.arch}")
    
    # 检查PyInstaller是否安装
    try:
        import PyInstaller
        print(f"PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("错误: PyInstaller 未安装")
        print("请运行: pip install pyinstaller")
        return 1
    
    # 清理旧构建
    clean_build_dirs()
    
    # 如果只清理，则退出
    if args.clean_only:
        print("清理完成，退出构建过程")
        return 0
    
    # 构建exe
    exe_name = build_exe(args.arch)
    if not exe_name:
        return 1
    
    # 创建批处理包装器
    bat_filename = create_bat_wrapper(args.arch, exe_name)
    
    # 确定输出目录
    if args.arch == 'auto':
        import platform
        current_arch = platform.architecture()[0]
        target_arch = '64bit' if '64' in current_arch else '32bit'
    else:
        target_arch = args.arch
    
    output_dir = f'dist_{target_arch}'
    
    print("\n" + "=" * 60)
    print("打包完成!")
    print("=" * 60)
    print(f"\n架构信息:")
    print(f"  目标架构: {target_arch}")
    print(f"  输出目录: {output_dir}/")
    
    print("\n使用方法:")
    print(f"1. 直接运行 {output_dir}/MSPhraseTool.exe")
    print(f"2. 或使用 {bat_filename} 包装器")
    
    print("\n常用命令:")
    print(f"  {output_dir}/{exe_name}.exe --help         查看帮助")
    print(f"  {output_dir}/{exe_name}.exe export         导出现有短语")
    print(f"  {output_dir}/{exe_name}.exe import file.csv 导入短语")
    print(f"  {output_dir}/{exe_name}.exe list           查看所有短语")
    
    print("\n文件位置:")
    print(f"  EXE文件: {os.path.abspath(f'{output_dir}/{exe_name}.exe')}")
    print(f"  包装器: {os.path.abspath(bat_filename)}")
    
    print("\n注意事项:")
    print("  1. 32位EXE需要在32位系统或兼容模式下运行")
    print("  2. 64位EXE只能在64位系统上运行")
    print("  3. 要构建32位版本，需要使用32位Python解释器")
    
    print("\n配置文件说明:")
    print("  .env 文件不会被打包进 EXE，需要在 EXE 同目录下手动创建")
    print("  请参考 .env.案例 文件创建你的 .env 配置文件")
    print("  .env 文件位置: 与 EXE 文件在同一目录下")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())