#!/usr/bin/env python3
"""测试 lex 文件读取"""
import sys
import os

# 确保项目根目录在 Python 路径中
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from pinyin_lex_tool.lex_reader import LexFileReader


def test_lex_reader():
    """测试 lex 文件读取"""
    lex_path = "test_fix4/微软.lex"
    
    if not os.path.exists(lex_path):
        print(f"文件不存在: {lex_path}")
        return
    
    reader = LexFileReader()
    phrases = reader.read_all(lex_path)
    
    print(f"读取到 {len(phrases)} 个短语")
    for phrase in phrases:
        print(f"拼音: {phrase.pinyin}, 索引: {phrase.index}, 文本: {phrase.text}")


if __name__ == "__main__":
    test_lex_reader()
