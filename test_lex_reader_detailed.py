#!/usr/bin/env python3
"""测试 lex 文件读取（详细）"""
import sys
import os
import struct

# 确保项目根目录在 Python 路径中
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from pinyin_lex_tool.lex_reader import LexFileReader


def test_lex_reader_detailed():
    """测试 lex 文件读取（详细）"""
    lex_path = "test_fix6/微软.lex"
    
    if not os.path.exists(lex_path):
        print(f"文件不存在: {lex_path}")
        return
    
    # 直接读取文件并分析
    with open(lex_path, 'rb') as f:
        data = f.read()
    
    PHRASE_CNT_POS = 0x1C
    PHRASE_LEN_FIRST_POS = 0x44
    
    if len(data) < PHRASE_LEN_FIRST_POS:
        print("文件长度不足")
        return
    
    phrase_count = struct.unpack('<I', data[PHRASE_CNT_POS:PHRASE_CNT_POS + 4])[0]
    print(f"短语数量: {phrase_count}")
    
    first_offset_pos = PHRASE_LEN_FIRST_POS
    first_block_pos = first_offset_pos + 4 * (phrase_count - 1)
    
    print(f"偏移表位置: {first_offset_pos}")
    print(f"记录开始位置: {first_block_pos}")
    
    # 打印偏移表
    print("偏移表:")
    for i in range(phrase_count - 1):
        offset_pos = first_offset_pos + i * 4
        offset = struct.unpack('<I', data[offset_pos:offset_pos + 4])[0]
        print(f"  偏移 {i}: {offset}")
    
    # 读取记录
    print("记录:")
    last_pos = 0
    for i in range(phrase_count):
        if i == phrase_count - 1:
            block_pos = -1
        else:
            offset_pos = first_offset_pos + i * 4
            block_pos = struct.unpack('<I', data[offset_pos:offset_pos + 4])[0]
        
        block_len = -1 if block_pos == -1 else (block_pos - last_pos)
        if block_len < 0:
            seg = data[first_block_pos + last_pos:]
        else:
            seg = data[first_block_pos + last_pos:first_block_pos + last_pos + block_len]
        last_pos = block_pos
        
        print(f"  记录 {i}:")
        print(f"    长度: {len(seg)}")
        if len(seg) >= 16:
            # 打印头部
            header_len = struct.unpack('<I', seg[0:4])[0]
            print(f"    头部长度: {header_len}")
            
            # 打印索引
            storage_index = struct.unpack('<I', seg[8:12])[0]
            print(f"    存储索引: {storage_index}")
            print(f"    显示索引: {storage_index - 1536}")
            
            # 打印内容
            body = seg[16:]
            print(f"    内容长度: {len(body)}")
            if body:
                # 按 00 00 分割
                parts = []
                current = bytearray()
                for j in range(0, len(body), 2):
                    if j + 1 < len(body):
                        if body[j] == 0x00 and body[j+1] == 0x00:
                            if len(current) >= 2:
                                parts.append(bytes(current))
                                current.clear()
                        else:
                            current.append(body[j])
                            current.append(body[j+1])
                
                if len(current) >= 2:
                    parts.append(bytes(current))
                
                print(f"    分割后部分数: {len(parts)}")
                for k, part in enumerate(parts):
                    try:
                        print(f"    部分 {k}: {part.decode('utf-16-le')}")
                    except:
                        print(f"    部分 {k}: 无法解码")


if __name__ == "__main__":
    test_lex_reader_detailed()
