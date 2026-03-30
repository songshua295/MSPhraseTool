#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微软短语工具 - 支持百度、搜狗、Rime、多多、微软等格式转换
order 意思：同一 code 内部的顺序

编码规范：
- 百度、搜狗、多多、自定义：使用 utf-8 编码
- Rime：使用 utf-8 编码
- 微软：二进制处理，内部使用 utf-16-le
"""

import io
import os
import struct
import sys
import time
import csv
from collections import defaultdict
from typing import List, NamedTuple, Optional


# -------------------- 基础数据结构 --------------------
class Entry(NamedTuple):
    word: str
    code: str
    order: int  # 词序 预设同一 code 内部的顺序


Table = List[Entry]


# -------------------- 编码检测与处理 --------------------
def detect_file_encoding(path: str, expected_encoding: str = "utf-8") -> str:
    """检测文件编码，如果与预期不匹配则返回检测到的编码

    Args:
        path: 文件路径
        expected_encoding: 预期的编码格式

    Returns:
        检测到的编码格式
    """
    try:
        # 读取文件前部内容进行检测
        with open(path, 'rb') as f:
            raw_data = f.read(4096)

        if not raw_data:
            return expected_encoding

        # 先尝试使用 chardet 检测编码
        try:
            import chardet
            result = chardet.detect(raw_data)
            detected_encoding = result['encoding']
            confidence = result['confidence']

            # 规范化编码名
            encoding_map = {
                'utf-8': 'utf-8',
                'utf-8-sig': 'utf-8-sig',
                'utf-16': 'utf-16-le',
                'utf-16le': 'utf-16-le',
                'utf-16-le': 'utf-16-le',
                'gb2312': 'gb2312',
                'gbk': 'gbk',
                'gb18030': 'gb18030',
                'big5': 'big5',
                'ascii': 'ascii'
            }

            detected_encoding = encoding_map.get(detected_encoding, detected_encoding)

            # 如果检测到的编码与预期一致，返回
            if detected_encoding and confidence > 0.7:
                normalized_expected = encoding_map.get(expected_encoding, expected_encoding)
                if detected_encoding.lower() == normalized_expected.lower():
                    return detected_encoding

            # 如果不一致，也返回检测结果，交给调用方处理
            return detected_encoding

        except ImportError:
            # chardet 未安装，尝试检测常见编码
            print("注意: chardet 库未安装，将使用简单检测。建议安装 pip install chardet")

            # 先尝试使用预期编码
            try:
                raw_data.decode(expected_encoding, errors='strict')
                return expected_encoding
            except UnicodeDecodeError:
                # 如果预期编码失败，尝试其他常见编码
                pass

            # 尝试检测是否为 utf-16-le 编码
            try:
                # 检查文件大小是否为偶数（utf-16-le 特征）
                if len(raw_data) >= 2 and len(raw_data) % 2 == 0:
                    # 检查是否有 BOM 标记
                    if len(raw_data) >= 2 and raw_data[:2] == b'\xff\xfe':
                        return 'utf-16-le'

                    # 尝试解码为 utf-16-le
                    raw_data.decode('utf-16-le', errors='strict')

                    # 检查：utf-16-le 文本通常有很多 0x00 字节
                    # 统计 0x00 字节的比例
                    zero_count = raw_data.count(b'\x00')
                    zero_ratio = zero_count / len(raw_data)

                    # 如果 0x00 字节比例较高，很可能是 utf-16-le
                    if zero_ratio > 0.1:  # 10% 以上的 0x00 字节
                        return 'utf-16-le'
                    else:
                        # 可能是其它编码，继续尝试其它编码
                        pass
            except UnicodeDecodeError:
                pass

            # 尝试其它常见编码
            common_encodings = ['gbk', 'gb2312', 'gb18030', 'big5', 'utf-8-sig', 'ascii']
            for enc in common_encodings:
                try:
                    raw_data.decode(enc, errors='strict')
                    # 返回检测到的编码，而不是抛出异常
                    return enc
                except UnicodeDecodeError:
                    continue

        # 如果检测失败或找不到合适编码，返回预期编码，让调用方处理
        return expected_encoding

    except Exception as e:
        print(f"编码检测失败: {e}，将使用预期编码 {expected_encoding}")
        return expected_encoding


def read_text_file(path: str, expected_encoding: str = "utf-8") -> List[str]:
    """读取文本文件，自动检测编码

    特别处理：如果检测到 utf-16-le 编码，会自动转换为 utf-8 进行处理

    Args:
        path: 文件路径
        expected_encoding: 预期的编码格式

    Returns:
        文件行列表
    """
    # 检测文件编码
    encoding = detect_file_encoding(path, expected_encoding)

    # 如果检测到 utf-16-le 编码，自动转换为 utf-8
    if encoding.lower() in ['utf-16-le', 'utf-16', 'utf-16le']:
        print(f"检测到 {encoding} 编码，自动转换为 utf-8 进行处理")
        try:
            # 以二进制模式读取文件
            with open(path, "rb") as f:
                raw_data = f.read()

            # 解码为字符串（从 utf-16-le 到 unicode）
            text = raw_data.decode("utf-16-le", errors="ignore")

            # 按行分割
            lines = text.splitlines()

            # 去除可能的 BOM
            if lines and lines[0].startswith("\ufeff"):
                lines[0] = lines[0].lstrip("\ufeff")

            return lines

        except Exception as e:
            print(f"utf-16-le 转换失败: {e}，尝试直接读取")
            # 如果转换失败，尝试直接读取
            encoding = "utf-8"

    try:
        with open(path, "r", encoding=encoding) as f:
            lines = [ln.rstrip("\n") for ln in f]
    except UnicodeDecodeError:
        # 如果使用检测到的编码失败，尝试使用预期编码
        print(f"使用编码 {encoding} 读取失败，尝试使用 {expected_encoding}")
        with open(path, "r", encoding=expected_encoding, errors="ignore") as f:
            lines = [ln.rstrip("\n") for ln in f]

    # 去除可能的 BOM
    if lines and lines[0].startswith("\ufeff"):
        lines[0] = lines[0].lstrip("\ufeff")

    return lines


def write_text_file(path: str, lines: List[str], encoding: str = "utf-8"):
    """写入文本文件，使用指定编码

    Args:
        path: 文件路径
        lines: 要写入的行列表
        encoding: 使用的编码格式
    """
    with open(path, "w", encoding=encoding) as f:
        f.writelines(f"{ln}\n" for ln in lines)
    print(f"已保存 → {path} (编码: {encoding})")


# -------------------- 百度 --------------------
def load_baidu(path: str) -> Table:
    """加载百度格式文件，使用 utf-8 编码"""
    lines = read_text_file(path, "utf-8")
    tbl = []

    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue

        try:
            # 格式: code=order,word
            if "=" not in ln or "," not in ln:
                continue

            code, order_word = ln.split("=", 1)
            order, word = order_word.split(",", 1)

            tbl.append(Entry(
                word=word.strip(),
                code=code.strip(),
                order=int(order.strip())
            ))
        except (ValueError, IndexError):
            print(f"警告：跳过无效行: {ln}")
            continue

    return tbl


def save_baidu(path: str, table: Table):
    """保存百度格式文件，使用 utf-8 编码"""
    lines = [f"{e.code}={e.order},{e.word}" for e in table]
    write_text_file(path, lines, "utf-8")


# -------------------- 搜狗 --------------------
def load_sogou(path: str) -> Table:
    """加载搜狗格式文件，使用 utf-8 编码"""
    lines = read_text_file(path, "utf-8")
    tbl = []

    for ln in lines:
        ln = ln.strip()
        if not ln or ln.startswith("#") or ln.startswith(";"):
            continue

        try:
            # 格式: code,order=word
            if "=" not in ln or "," not in ln:
                continue

            enc_order, word = ln.split("=", 1)
            enc, order = enc_order.rsplit(",", 1)

            tbl.append(Entry(
                word=word.strip(),
                code=enc.strip(),
                order=int(order.strip())
            ))
        except (ValueError, IndexError):
            print(f"警告：跳过无效行: {ln}")
            continue

    return tbl


def save_sogou(path: str, table: Table):
    """保存搜狗格式文件，使用 utf-8 编码"""
    lines = [f"{e.code},{e.order}={e.word}" for e in table]
    write_text_file(path, lines, "utf-8")


# -------------------- Rime --------------------
def load_rime(path: str) -> Table:
    """加载 Rime 格式文件，使用 utf-8 编码"""
    lines = read_text_file(path, "utf-8")
    tbl = []

    for ln in lines:
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue

        try:
            parts = ln.split("\t")
            if len(parts) < 2:
                continue

            word = parts[0]
            code = parts[1]
            weight = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 20
            order = max(1, 20 - weight)

            tbl.append(Entry(word, code, order))
        except (ValueError, IndexError):
            print(f"警告：跳过无效行: {ln}")
            continue

    return tbl


def save_rime(path: str, table: Table):
    """保存 Rime 格式文件，使用 utf-8 编码"""
    lines = []
    for e in table:
        weight = max(0, 20 - e.order)
        lines.append(f"{e.word}\t{e.code}\t{weight}")
    write_text_file(path, lines, "utf-8")


# -------------------- CSV 格式 --------------------
def load_csv(path: str) -> Table:
    """加载 CSV 格式文件，使用 utf-8 编码

    CSV 格式（与 PinyinPhrase 结构一致）：
      pinyin,index,text

    例如：
      a,1,词
      aa,1,词组
      aab,1,词组组
    """
    lines = read_text_file(path, "utf-8")
    tbl = []

    for ln in lines:
        ln = ln.strip()
        if not ln or ln.startswith("#") or ln.startswith(";"):
            continue

        try:
            parts = ln.split(",")
            if len(parts) < 3:
                continue

            pinyin = parts[0].strip()
            index = int(parts[1].strip())
            text = parts[2].strip()

            # 转换为内部 Entry 格式：word=词语, code=拼音, order=索引
            tbl.append(Entry(text, pinyin, index))
        except (ValueError, IndexError):
            print(f"警告：跳过无效行: {ln}")
            continue

    return tbl


def save_csv(path: str, table: Table):
    """保存 CSV 格式文件，使用 utf-8 编码

    输出格式：pinyin,index,text
    """
    lines = []
    for e in table:
        lines.append(f"{e.code},{e.order},{e.word}")
    write_text_file(path, lines, "utf-8")


# -------------------- 多多（核苷酸） --------------------
def load_duoduo(path: str) -> Table:
    """加载多多格式文件，使用 utf-8 编码

    多多格式：
      词语
      拼音
      词语\t拼音\torder

    order 意思：同一 code 内部顺序
    """
    lines = read_text_file(path, "utf-8")
    tbl = []
    code_order = defaultdict(int)

    for ln in lines:
        ln = ln.strip()
        if not ln or ln.startswith("#") or ln.startswith(";"):
            continue

        try:
            parts = ln.split("\t")
            if len(parts) < 2:
                continue

            word = parts[0].strip()
            code = parts[1].strip()

            # 如果第三列存在且为数字，直接作为 code 的 order
            if len(parts) >= 3 and parts[2].strip().isdigit():
                order = int(parts[2].strip())
            else:
                code_order[code] += 1
                order = code_order[code]

            tbl.append(Entry(word, code, order))
        except (ValueError, IndexError):
            print(f"警告：跳过无效行: {ln}")
            continue

    return tbl


def save_duoduo(path: str, table: Table):
    """保存多多格式文件，使用 utf-8 编码"""
    lines = [f"{e.word}\t{e.code}" for e in table]
    write_text_file(path, lines, "utf-8")


# -------------------- 微软 dat --------------------
def load_ms(path: str) -> Table:
    """加载微软格式文件，二进制格式，内部使用 utf-16-le 编码"""
    with open(path, "rb") as f:
        data = f.read()
    r = io.BytesIO(data)

    r.seek(0x10)
    off_base, entry_base, entry_end, count = struct.unpack("<4I", r.read(16))
    tbl = []

    r.seek(off_base)
    offsets = [struct.unpack("<I", r.read(4))[0] for _ in range(count)]
    offsets.append(entry_end - entry_base)

    for i in range(count):
        start = entry_base + offsets[i]
        end = entry_base + offsets[i + 1]
        r.seek(start)

        r.read(4)
        code_len = struct.unpack("<H", r.read(2))[0]
        order = r.read(1)[0]
        r.read(1 + 8)

        code = r.read(code_len * 2).decode("utf-16-le", errors="ignore")
        word_len = struct.unpack("<H", r.read(2))[0]
        r.read(6)
        word = r.read(word_len * 2).decode("utf-16-le", errors="ignore")

        if word and code:
            tbl.append(Entry(word, code, order))

    return tbl


def save_ms(path: str, table: Table):
    """保存微软格式文件，二进制格式，内部使用 utf-16-le 编码"""
    # 暂时返回错误表示该功能未实现
    raise NotImplementedError("微软格式保存功能未实现")


# -------------------- 主要转换功能 --------------------
def convert_phrases(format_name: str, src_path: str, dst_path: str) -> bool:
    """主要转换函数"""
    try:
        print(f"开始转换 {format_name} 格式...")
        table: Table = None

        # 根据格式读取输入文件
        if format_name.lower() == "baidu":
            table = load_baidu(src_path)
        elif format_name.lower() == "sogou":
            table = load_sogou(src_path)
        elif format_name.lower() == "rime":
            table = load_rime(src_path)
        elif format_name.lower() == "csv":
            table = load_csv(src_path)
        elif format_name.lower() == "duoduo":
            table = load_duoduo(src_path)
        elif format_name.lower() == "ms":
            table = load_ms(src_path)
        else:
            raise ValueError(f"不支持的格式: {format_name}")

        # 保存为指定格式
        if format_name.lower() == "baidu":
            save_baidu(dst_path, table)
        elif format_name.lower() == "sogou":
            save_sogou(dst_path, table)
        elif format_name.lower() == "rime":
            save_rime(dst_path, table)
        elif format_name.lower() == "csv":
            save_csv(dst_path, table)
        elif format_name.lower() == "duoduo":
            save_duoduo(dst_path, table)
        elif format_name.lower() == "ms":
            save_ms(dst_path, table)
        else:
            raise ValueError(f"不支持的格式: {format_name}")

        print("转换成功完成")
        return True

    except Exception as e:
        print(f"转换失败: {e}")
        return False


# -------------------- 交互式主函数 --------------------
def interactive_main():
    """交互式主函数"""
    print("微软短语工具 - 交互模式")
    print("支持格式: baidu, sogou, rime, csv, duoduo, ms")

    while True:
        try:
            format_name = input("请输入格式 (或输入 'quit' 退出): ").strip()
            if format_name.lower() == 'quit':
                break

            src_path = input("请输入源文件路径: ").strip()
            dst_path = input("请输入目标文件路径: ").strip()

            if not convert_phrases(format_name, src_path, dst_path):
                print("转换失败！")

        except KeyboardInterrupt:
            print("\n程序已退出")
            break
