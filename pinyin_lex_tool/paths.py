"""路径管理"""
import os
from pathlib import Path


def get_user_lex_path() -> str:
    """获取当前用户的 .lex 文件路径"""
    appdata = os.environ.get('APPDATA', '')
    if not appdata:
        raise RuntimeError("无法找到 APPDATA 环境变量")
    
    lex_path = Path(appdata) / "Microsoft" / "InputMethod" / "Chs" / "ChsPinyinEUDPv1.lex"
    return str(lex_path)
