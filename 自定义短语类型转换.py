#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜狗、百度（同手心）、微软、rime、多多 自定义短语格式转换脚本
order 语义：同一 code 内部的候选顺序
"""

import io
import os
import struct
import sys
import time
from collections import defaultdict
from typing import List, NamedTuple


# -------------------- 基础数据结构 --------------------
class Entry(NamedTuple):
    word: str
    code: str
    order: int  # ⚠️ 同一个 code 内部的顺序


Table = List[Entry]


# -------------------- UTF-16 LE 专用读写 --------------------
def read_utf16le_lines(path: str) -> List[str]:
    try:
        with open(path, "r", encoding="utf-16-le") as f:
            lines = [ln.rstrip("\n") for ln in f]
    except Exception as e:
        print(f"警告：{e}，尝试忽略错误继续读取")
        with open(path, "r", encoding="utf-16-le", errors="ignore") as f:
            lines = [ln.rstrip("\n") for ln in f]

    if lines and lines[0].startswith("\ufeff"):
        lines[0] = lines[0].lstrip("\ufeff")
    return lines


def write_utf16le_lines(path: str, lines: List[str]):
    with open(path, "w", encoding="utf-16-le") as f:
        f.writelines(f"{ln}\n" for ln in lines)
    print(f"已保存 → {path}")


# -------------------- 百度 --------------------
def load_baidu(path: str) -> Table:
    return [
        Entry(word=word, code=code, order=int(order))
        for ln in read_utf16le_lines(path)
        for code, order_word in [ln.strip().split("=", 1)]
        for order, word in [order_word.split(",", 1)]
    ]


def save_baidu(path: str, table: Table):
    write_utf16le_lines(path, [f"{e.code}={e.order},{e.word}" for e in table])


# -------------------- 搜狗 --------------------
def load_sogou(path: str) -> Table:
    tbl = []
    for ln in read_utf16le_lines(path):
        ln = ln.strip()
        if not ln or ln.startswith("#") or ln.startswith(";"):
            continue
        if "=" not in ln or "," not in ln:
            continue
        enc_order, word = ln.split("=", 1)
        enc, order = enc_order.rsplit(",", 1)
        tbl.append(Entry(word.strip(), enc.strip(), int(order.strip())))
    return tbl


def save_sogou(path: str, table: Table):
    write_utf16le_lines(path, [f"{e.code},{e.order}={e.word}" for e in table])


# -------------------- Rime --------------------
def load_rime(path: str) -> Table:
    tbl = []
    with open(path, "r", encoding="utf-8-sig") as f:
        for ln in f:
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            parts = ln.split("\t")
            if len(parts) < 2:
                continue
            word = parts[0]
            code = parts[1]
            weight = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 20
            order = max(1, 20 - weight)
            tbl.append(Entry(word, code, order))
    return tbl


def save_rime(path: str, table: Table):
    lines = []
    for e in table:
        weight = max(0, 20 - e.order)
        lines.append(f"{e.word}\t{e.code}\t{weight}")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(f"{ln}\n" for ln in lines)
    print(f"已保存 → {path}")


# -------------------- 多多（核心修正） --------------------
def load_duoduo(path: str) -> Table:
    """
    多多格式：
      词\t编码
      或
      词\t编码\torder

    order 语义：同一 code 内部顺序
    """
    tbl = []
    code_order = defaultdict(int)

    for ln in read_utf16le_lines(path):
        ln = ln.strip()
        if not ln or ln.startswith("#") or ln.startswith(";"):
            continue

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

    return tbl


def save_duoduo(path: str, table: Table):
    write_utf16le_lines(path, [f"{e.word}\t{e.code}" for e in table])


# -------------------- 微软 dat --------------------
def load_ms(path: str) -> Table:
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

    print(f"已保存 → {path}")


# -------------------- 主入口 --------------------
def main():
    print("============ 一键多格式互转（order=同 code 内顺序） ============")
    print("1. 百度 → 搜狗 + 微软 + Rime + 多多")
    print("2. 搜狗 → 百度 + 微软 + Rime + 多多")
    print("3. 微软 → 百度 + 搜狗 + Rime + 多多")
    print("4. Rime → 百度 + 搜狗 + 微软 + 多多")
    print("5. 多多 → 百度 + 搜狗 + 微软 + Rime")
    print("============================================================")

    src = int(input("请选择源格式 (默认 1): ") or 1)
    src_path = input("请输入源文件路径: ").strip(' "')

    if not os.path.isfile(src_path):
        print("文件不存在")
        return

    if src == 1:
        table = load_baidu(src_path)
    elif src == 2:
        table = load_sogou(src_path)
    elif src == 3:
        table = load_ms(src_path)
    elif src == 4:
        table = load_rime(src_path)
    elif src == 5:
        table = load_duoduo(src_path)
    else:
        return

    save_baidu("百度.ini.txt", table)
    save_sogou("PhraseEdit.txt", table)
    save_ms("微软.dat", table)
    save_rime("Rime自定义短语.txt", table)
    save_duoduo("多多自定义短语.txt", table)

    print("全部转换完成！")


if __name__ == "__main__":
    main()
