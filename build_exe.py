#!/usr/bin/env python3
"""
MSPhraseTool 打包脚本
用于将项目打包成独立的可执行文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def clean_build_dirs():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist', 'MSPhraseTool.spec']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"清理: {dir_name}")
            if os.path.isdir(dir_name):
                shutil.rmtree(dir_name)
            else:
                os.remove(dir_name)

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
    ],
    hiddenimports=[
        'chardet',
        'boto3',
        'botocore',
        'python_dotenv',
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

def build_exe():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    # 使用PyInstaller构建
    cmd = [
        'pyinstaller',
        '--onefile',  # 单文件exe
        '--name=MSPhraseTool',
        '--console',  # 控制台程序
        '--add-data=tool;tool',  # 包含tool目录
        '--add-data=pinyin_lex_tool;pinyin_lex_tool',  # 包含pinyin_lex_tool目录
        '--hidden-import=chardet',
        '--hidden-import=boto3',
        '--hidden-import=botocore',
        '--hidden-import=python_dotenv',
        '--hidden-import=pinyin_lex_tool',
        '--hidden-import=pinyin_lex_tool.cli',
        '--hidden-import=pinyin_lex_tool.service',
        '--hidden-import=pinyin_lex_tool.lex_reader',
        '--hidden-import=pinyin_lex_tool.lex_writer',
        '--hidden-import=pinyin_lex_tool.models',
        '--hidden-import=pinyin_lex_tool.paths',
        '--clean',  # 清理临时文件
        'main.py'
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("构建成功!")
        print(f"输出目录: {os.path.abspath('dist')}")
        
        # 显示生成的文件
        dist_dir = Path('dist')
        if dist_dir.exists():
            print("\n生成的文件:")
            for file in dist_dir.iterdir():
                print(f"  - {file.name} ({file.stat().st_size / 1024 / 1024:.2f} MB)")
    else:
        print("构建失败!")
        print("标准输出:", result.stdout)
        print("错误输出:", result.stderr)
        return False
    
    return True

def create_bat_wrapper():
    """创建批处理文件包装器，方便使用"""
    bat_content = '''@echo off
chcp 65001 >nul
echo MSPhraseTool - 微软拼音短语管理工具
echo.
if "%1"=="" (
    MSPhraseTool.exe --help
) else (
    MSPhraseTool.exe %*
)
pause
'''
    
    with open('MSPhraseTool.bat', 'w', encoding='utf-8') as f:
        f.write(bat_content)
    print("创建: MSPhraseTool.bat (包装器)")

def main():
    """主函数"""
    print("=" * 60)
    print("MSPhraseTool 打包工具")
    print("=" * 60)
    
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
    
    # 构建exe
    if not build_exe():
        return 1
    
    # 创建批处理包装器
    create_bat_wrapper()
    
    print("\n" + "=" * 60)
    print("打包完成!")
    print("=" * 60)
    print("\n使用方法:")
    print("1. 直接运行 dist/MSPhraseTool.exe")
    print("2. 或使用 MSPhraseTool.bat 包装器")
    print("\n常用命令:")
    print("  MSPhraseTool.exe --help         查看帮助")
    print("  MSPhraseTool.exe export         导出现有短语")
    print("  MSPhraseTool.exe import file.csv 导入短语")
    print("  MSPhraseTool.exe list           查看所有短语")
    print("\n文件位置:")
    print(f"  EXE文件: {os.path.abspath('dist/MSPhraseTool.exe')}")
    print(f"  包装器: {os.path.abspath('MSPhraseTool.bat')}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())