#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜狗、百度（同手心）、微软、rime、多多 自定义短语格式转换脚本
order 语义：同一 code 内部的候选顺序

编码规范：
- 百度、搜狗、多多：使用 utf-8 编码
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
    order: int  # ⚠️ 同一个 code 内部的顺序


Table = List[Entry]


# -------------------- 编码检测与处理 --------------------
def detect_file_encoding(path: str, expected_encoding: str = "utf-8") -> str:
    """检测文件编码，如果与预期不符则报错

    Args:
        path: 文件路径
        expected_encoding: 预期的编码格式

    Returns:
        检测到的编码格式

    Raises:
        ValueError: 文件编码与预期不符
    """
    try:
        # 读取文件前部分内容进行检测
        with open(path, 'rb') as f:
            raw_data = f.read(4096)

        if not raw_data:
            return expected_encoding

        # 尝试使用 chardet 检测编码
        try:
            import chardet
            result = chardet.detect(raw_data)
            detected_encoding = result['encoding']
            confidence = result['confidence']

            # 规范化编码名称
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

            # 如果检测到的编码与预期不符，但如果是 utf-16-le 则自动支持
            if detected_encoding and confidence > 0.7:
                normalized_expected = encoding_map.get(expected_encoding, expected_encoding)
                if detected_encoding.lower() != normalized_expected.lower():
                    # 如果是 utf-16-le 编码，自动支持，不报错
                    if detected_encoding.lower() in ['utf-16-le', 'utf-16', 'utf-16le']:
                        print(f"检测到 {detected_encoding} 编码，将自动转换为 utf-8 处理")
                        return detected_encoding
                    raise ValueError(
                        f"文件编码检测为 {detected_encoding} (置信度: {confidence:.2f})，"
                        f"但预期为 {expected_encoding}。请检查文件编码。"
                    )
                return detected_encoding

        except ImportError:
            # chardet 未安装，尝试检测常见编码
            print("警告: chardet 库未安装，尝试检测常见编码。建议安装: pip install chardet")

            # 首先尝试使用预期编码
            try:
                raw_data.decode(expected_encoding, errors='strict')
                return expected_encoding
            except UnicodeDecodeError:
                # 如果预期编码失败，尝试其他常见编码
                pass

            # 尝试检测是否是 utf-16-le 编码
            try:
                # 检查文件大小是否为偶数（utf-16-le 特征）
                if len(raw_data) >= 2 and len(raw_data) % 2 == 0:
                    # 检查是否有 BOM 标记（UTF-16 LE BOM 是 FF FE）
                    if len(raw_data) >= 2 and raw_data[:2] == b'\xff\xfe':
                        return 'utf-16-le'

                    # 尝试解码为 utf-16-le
                    raw_data.decode('utf-16-le', errors='strict')

                    # 额外的检查：utf-16-le 文本通常有很多 0x00 字节
                    # 统计 0x00 字节的比例
                    zero_count = raw_data.count(b'\x00')
                    zero_ratio = zero_count / len(raw_data)

                    # 如果 0x00 字节比例较高，很可能是 utf-16-le
                    if zero_ratio > 0.1:  # 10% 以上的 0x00 字节
                        return 'utf-16-le'
                    else:
                        # 可能是其他编码，继续尝试其他编码
                        pass
            except UnicodeDecodeError:
                pass

            # 尝试其他常见编码
            common_encodings = ['gbk', 'gb2312', 'gb18030', 'big5', 'utf-8-sig', 'ascii']
            for enc in common_encodings:
                try:
                    raw_data.decode(enc, errors='strict')
                    raise ValueError(
                        f"文件编码检测为 {enc}，但预期为 {expected_encoding}。"
                        f"请检查文件编码或安装 chardet 库进行更准确的检测。"
                    )
                except UnicodeDecodeError:
                    continue

        # 如果检测置信度低或 chardet 不可用，尝试使用预期编码
        try:
            raw_data.decode(expected_encoding, errors='strict')
            return expected_encoding
        except UnicodeDecodeError:
            # 尝试常见编码
            common_encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'gb18030', 'big5']
            for enc in common_encodings:
                try:
                    raw_data.decode(enc, errors='strict')
                    raise ValueError(
                        f"文件编码检测为 {enc}，但预期为 {expected_encoding}。"
                        f"请检查文件编码或安装 chardet 库进行更准确的检测。"
                    )
                except UnicodeDecodeError:
                    continue

            # 如果所有常见编码都失败，使用预期编码并忽略错误
            print(f"警告: 无法确定文件编码，将使用 {expected_encoding} 并忽略错误")
            return expected_encoding

    except Exception as e:
        if isinstance(e, ValueError):
            raise  # 重新抛出编码不匹配错误
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

            # 移除可能的 BOM
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

    # 移除可能的 BOM
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
      a,1,啊
      aa,1,阿
      aab,1,阿爸
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

            # 转换为内部 Entry 格式：word=短语, code=拼音, order=index
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


# -------------------- 多多（核心修正） --------------------
    """加载多多格式文件，使用 utf-8 编码

    多多格式：
      词\t编码
      或
      词\t编码\torder

    order 语义：同一 code 内部顺序
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

            # 如果第三列存在且为数字，直接作为 code 内 order
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

        code_bytes = r.read(code_len - 0x12)
        r.read(2)
        word_bytes = r.read(end - r.tell())

        code = code_bytes.decode("utf-16-le", errors="ignore")
        word = word_bytes.split(b"\x00\x00")[0].decode("utf-16-le", errors="ignore")

        tbl.append(Entry(word, code, order))

    return tbl


def save_ms(path: str, table: Table):
    """保存微软格式文件，二进制格式，内部使用 utf-16-le 编码"""
    buf = io.BytesIO()
    stamp = int(time.time())

    buf.write(b"mschxudp\x02\x00`\x00\x01\x00\x00\x00")
    buf.write(struct.pack("<I", 0x40))
    entry_table_offset = 0x40 + 4 * len(table)
    buf.write(struct.pack("<I", entry_table_offset))
    buf.write(b"\x00" * 4)
    buf.write(struct.pack("<I", len(table)))
    buf.write(struct.pack("<I", stamp))
    buf.write(b"\x00" * 32)

    entries_blob = []
    offset = 0

    for e in table:
        code_bytes = e.code.encode("utf-16-le")
        word_bytes = e.word.encode("utf-16-le")

        entry_head = (
            b"\x10\x00\x10\x00"
            + struct.pack("<H", len(code_bytes) + 18)
            + e.order.to_bytes(1, "little", signed=False)
            + b"\x06"
            + b"\x00\x00\x00\x00"
            + struct.pack("<I", stamp)
        )

        entry_blob = entry_head + code_bytes + b"\x00\x00" + word_bytes + b"\x00\x00"
        entries_blob.append(entry_blob)

        if len(entries_blob) < len(table):
            offset += len(entry_blob)
            buf.write(struct.pack("<I", offset))

    for blob in entries_blob:
        buf.write(blob)

    final = buf.getvalue()
    final = final[:0x18] + struct.pack("<I", len(final)) + final[0x1C:]

    with open(path, "wb") as f:
        f.write(final)

    print(f"已保存 → {path} (二进制格式)")


# -------------------- 转换函数 --------------------
def convert_phrases(src_format: str, src_path: str, out_dir: str = "out") -> bool:
    """转换自定义短语格式

    Args:
        src_format: 源格式 (bd:百度, sg:搜狗, wr:微软, rime:Rime, dd:多多)
        src_path: 源文件路径
        out_dir: 输出文件夹路径

    Returns:
        bool: 转换是否成功
    """
    if not os.path.isfile(src_path):
        print(f"错误: 文件不存在: {src_path}")
        return False

    # 加载源文件
    if src_format == "bd":
        table = load_baidu(src_path)
    elif src_format == "sg":
        table = load_sogou(src_path)
    elif src_format == "wr":
        table = load_ms(src_path)
    elif src_format == "rime":
        table = load_rime(src_path)
    elif src_format == "dd":
        table = load_duoduo(src_path)
    elif src_format == "csv":
        table = load_csv(src_path)
    else:
        print(f"错误: 不支持的源格式: {src_format}")
        print("支持的格式: bd(百度), sg(搜狗), wr(微软), rime(Rime), dd(多多), csv(CSV)")
        return False

    if not table:
        print("警告: 未加载到任何短语数据")
        return False

    # 创建输出文件夹（如果不存在）
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        print(f"已创建输出文件夹: {out_dir}")

    # 保存到输出文件夹下
    save_baidu(os.path.join(out_dir, "百度.ini.txt"), table)
    save_sogou(os.path.join(out_dir, "PhraseEdit.txt"), table)
    save_ms(os.path.join(out_dir, "微软.dat"), table)
    save_rime(os.path.join(out_dir, "Rime自定义短语.txt"), table)
    save_duoduo(os.path.join(out_dir, "多多自定义短语.txt"), table)
    save_csv(os.path.join(out_dir, "自定义短语.csv"), table)

    print(f"转换完成！输出文件已保存到 {out_dir} 文件夹下")
    return True


# -------------------- 交互式主入口 --------------------
def interactive_main():
    """交互式运行模式"""
    print("============ 一键多格式互转（order=同 code 内顺序） ============")
    print("bd. 百度 → 搜狗 + 微软 + Rime + 多多 + CSV")
    print("sg. 搜狗 → 百度 + 微软 + Rime + 多多 + CSV")
    print("wr. 微软 → 百度 + 搜狗 + Rime + 多多 + CSV")
    print("rime. Rime → 百度 + 搜狗 + 微软 + 多多 + CSV")
    print("dd. 多多 → 百度 + 搜狗 + 微软 + Rime + CSV")
    print("csv. CSV → 百度 + 搜狗 + 微软 + Rime + 多多")
    print("============================================================")

    src = input("请选择源格式 (默认 bd): ").strip() or "bd"

    # 如果是微软格式，默认使用系统 lex 文件路径
    if src == "wr":
        import os
        default_path = os.path.join(os.getenv("APPDATA", ""), "Microsoft", "InputMethod", "Chs", "ChsPinyinEUDPv1.lex")
        src_path = input(f"请输入源文件路径 (默认：{default_path}): ").strip(' "')
        if not src_path:
            src_path = default_path
    else:
        src_path = input("请输入源文件路径：").strip(' "')

    success = convert_phrases(src, src_path)
    if success:
        print("全部转换完成！")
    else:
        print("转换失败！")


# -------------------- 命令行主入口 --------------------
def main():
    """命令行入口点，支持命令行参数和交互式运行"""
    import argparse

    parser = argparse.ArgumentParser(
        description="自定义短语格式转换工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 交互式模式
  python phrase_converter.py

  # 命令行模式
  python phrase_converter.py --format bd --input baidu.txt --output my_output

  # 支持的格式:
  #   bd: 百度格式
  #   sg: 搜狗格式
  #   wr: 微软格式
  #   rime: Rime格式
  #   dd: 多多格式
        """
    )

    parser.add_argument(
        "--format", "-f",
        type=str,
        choices=["bd", "sg", "wr", "rime", "dd", "csv"],
        help="源文件格式 (bd:百度, sg:搜狗, wr:微软, rime:Rime, dd:多多, csv:CSV)"
    )

    parser.add_argument(
        "--input", "-i",
        type=str,
        help="源文件路径"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        default="out",
        help="输出文件夹路径 (默认: out)"
    )

    parser.add_argument(
        "--list-formats", "-l",
        action="store_true",
        help="列出支持的格式"
    )

    args = parser.parse_args()

    # 列出支持的格式
    if args.list_formats:
        print("支持的格式:")
        print("  bd: 百度格式 (code=order,word)")
        print("  sg: 搜狗格式 (code,order=word)")
        print("  wr: 微软格式 (二进制 .dat 文件)")
        print("  rime: Rime格式 (word\\tcode\\tweight)")
        print("  dd: 多多格式 (word\\tcode 或 word\\tcode\\torder)")
        print("  csv: CSV格式 (pinyin,index,text，与PinyinPhrase结构一致)")
        return

    # 如果提供了命令行参数，使用命令行模式
    if args.format is not None and args.input is not None:
        success = convert_phrases(args.format, args.input, args.output)
        if not success:
            sys.exit(1)
    else:
        # 否则使用交互式模式
        interactive_main()


if __name__ == "__main__":
    main()
