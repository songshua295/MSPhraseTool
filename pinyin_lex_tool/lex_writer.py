"""写入.lex 文件"""
import struct
from pathlib import Path
from typing import List, Tuple, Optional

from .models import PinyinPhrase

# 类型别名：(is_replaced, pinyin_bytes, header_bytes, phrase_bytes)
Rec = Tuple[bool, bytes, bytes, bytes]


class LexFileWriter:
    """.lex 文件写入器"""

    HEADER_MAGIC = b'mschxudp'
    HEADER_LEN = 20
    PHRASE_64_POS = 0x14
    TOTAL_BYTES_POS = 0x18
    PHRASE_CNT_POS = 0x1C
    PHRASE_LEN_FIRST_POS = 0x44
    PHRASE_SEP = b'\x00\x00'

    def __init__(self):
        pass

    def upsert(self, lex_path: str, items: List[Tuple[str, int, str]]) -> int:
        """插入或更新一批短语：同拼音覆盖旧记录

        Args:
            lex_path: .lex 文件路径
            items: 短语列表 (pinyin, index, text)

        Returns:
            覆盖的记录数
        """
        if not Path(lex_path).exists():
            self._init_lex_file(lex_path)

        tail_bytes = self._get_existing_tail_bytes_or_default(lex_path)
        existing, learned_tail = self._read_existing_records(lex_path)
        
        if learned_tail is not None and len(learned_tail) >= 2:
            tail_bytes = learned_tail

        int_overwritten = 0
        filtered = []

        for r in existing:
            is_replaced = False
            for n_pinyin, _, _ in items:
                if self._bytes_equal(n_pinyin.encode('utf-16-le'), r[1]):
                    is_replaced = True
                    break
            if is_replaced:
                int_overwritten += 1
            else:
                filtered.append(r)

        for pinyin, index, text in items:
            pinyin_bytes = pinyin.encode('utf-16-le')
            phrase_bytes = text.encode('utf-16-le')
            header = self._build_header(16 + len(pinyin_bytes) + len(self.PHRASE_SEP), index, tail_bytes)
            filtered.append((False, pinyin_bytes, header, phrase_bytes))

        filtered.sort(key=lambda x: x[1])

        self._write_all(lex_path, filtered)
        return int_overwritten

    def remove_phrases(self, lex_path: str, items: List[Tuple[str, int, str]]) -> int:
        """删除指定的短语

        Args:
            lex_path: .lex 文件路径
            items: 要删除的短语列表 (pinyin, index, text)

        Returns:
            删除的记录数
        """
        if not Path(lex_path).exists():
            return 0

        existing, learned_tail = self._read_existing_records(lex_path)
        
        int_removed = 0
        filtered = []

        for r in existing:
            should_remove = False
            for n_pinyin, n_index, n_text in items:
                pinyin_bytes = n_pinyin.encode('utf-16-le')
                phrase_bytes = n_text.encode('utf-16-le')
                storage_index = self._display_index_to_storage_index(n_index)
                
                # 检查拼音、索引和文本都匹配
                if (self._bytes_equal(pinyin_bytes, r[1]) and 
                    struct.unpack('<I', r[2][6:10])[0] == storage_index and
                    self._bytes_equal(phrase_bytes, r[3])):
                    should_remove = True
                    break
            
            if should_remove:
                int_removed += 1
            else:
                filtered.append(r)

        if int_removed > 0:
            filtered.sort(key=lambda x: x[1])
            self._write_all(lex_path, filtered)
        
        return int_removed

    def _init_lex_file(self, path: str) -> None:
        """初始化空的.lex 文件"""
        dir_path = Path(path).parent
        if dir_path and not dir_path.exists():
            dir_path.mkdir(parents=True)

        with open(path, 'wb') as f:
            bw = f

            hdr = bytearray()
            hdr.extend(self.HEADER_MAGIC)
            hdr.extend(bytes([0x02, 0x00, 0x60, 0x00, 0x01, 0x00, 0x00, 0x00]))
            hdr.extend(bytes([0x40, 0, 0, 0, 0x40, 0, 0, 0, 0, 0, 0, 0]))
            bw.write(hdr)

            bw.write(bytes([0, 0, 0, 0]))
            bw.write(bytes([0x38, 0xD2, 0xA3, 0x65]))
            bw.write(bytes(32))

    def _read_existing_records(self, path: str) -> Tuple[List[Rec], Optional[bytes]]:
        """读取现有记录"""
        with open(path, 'rb') as f:
            data = f.read()

        if len(data) < self.PHRASE_LEN_FIRST_POS:
            return [], None

        phrase_cnt = struct.unpack('<I', data[self.PHRASE_CNT_POS:self.PHRASE_CNT_POS + 4])[0]
        if phrase_cnt <= 0:
            return [], None

        table_start = self.PHRASE_LEN_FIRST_POS
        first_block_pos = self.PHRASE_LEN_FIRST_POS + 4 * (phrase_cnt - 1)
        last_pos = 0
        list_recs = []
        learned_tail = None

        for i in range(phrase_cnt):
            if i == phrase_cnt - 1:
                block_pos = -1
            else:
                block_pos = struct.unpack('<I', data[table_start + i * 4:table_start + i * 4 + 4])[0]

            block_len = -1 if block_pos == -1 else (block_pos - last_pos)
            seg = self._read_slice_from_end(data, first_block_pos + last_pos, block_len)
            last_pos = block_pos

            if len(seg) < 16:
                continue

            if learned_tail is None:
                learned_tail = seg[14:16]

            if len(seg) > 9 and seg[9] == 0x00:
                body = seg[16:]
                parts = self._split_by_00(body, 2)
                if len(parts) >= 2:
                    list_recs.append((True, parts[0], seg[:16], parts[1]))

        return list_recs, learned_tail

    def _write_all(self, path: str, records: List[Rec]) -> None:
        """写入所有记录"""
        with open(path, 'r+b') as f:
            f.seek(self.PHRASE_LEN_FIRST_POS)
            f.truncate()

        tolast = 0
        total_size = self.PHRASE_LEN_FIRST_POS

        with open(path, 'r+b') as f:
            f.seek(self.PHRASE_LEN_FIRST_POS)

            for i in range(len(records) - 1):
                r = records[i]
                phrase_len = len(r[2]) + len(r[1]) + len(self.PHRASE_SEP) + len(r[3]) + len(self.PHRASE_SEP)
                tolast += phrase_len
                f.write(struct.pack('<I', tolast))
                total_size += len(self.PHRASE_SEP) * 2

            for r in records:
                f.write(r[2])
                f.write(r[1])
                f.write(self.PHRASE_SEP)
                f.write(r[3])
                f.write(self.PHRASE_SEP)
                total_size += len(r[2]) + len(r[1]) + len(r[3]) + len(self.PHRASE_SEP) * 2

        self._replace_bytes(path, self.PHRASE_64_POS, struct.pack('<I', 64 + len(records) * 4))
        self._replace_bytes(path, self.PHRASE_CNT_POS, struct.pack('<I', len(records)))
        self._replace_bytes(path, self.TOTAL_BYTES_POS, struct.pack('<I', total_size))

    def _get_existing_tail_bytes_or_default(self, lex_path: str) -> bytes:
        """获取现有的 tail 字节或使用默认值"""
        try:
            _, learned_tail = self._read_existing_records(lex_path)
            if learned_tail is not None and len(learned_tail) >= 2:
                return learned_tail
        except Exception:
            pass
        return bytes([0xA5, 0x2C])

    def _split_by_00(self, buf: bytes, min_part_bytes: int) -> List[bytes]:
        """按 00 00 分隔"""
        list_parts = []
        cur = bytearray()

        i = 0
        while i + 1 < len(buf):
            if buf[i] == 0x00 and buf[i + 1] == 0x00:
                if len(cur) >= min_part_bytes:
                    list_parts.append(bytes(cur))
                cur.clear()
            else:
                cur.append(buf[i])
                cur.append(buf[i + 1])
            i += 2

        if len(cur) >= min_part_bytes:
            list_parts.append(bytes(cur))

        return list_parts

    def _compare_bytes(self, a: bytes, b: bytes) -> int:
        """比较字节数组"""
        n = min(len(a), len(b))
        for i in range(n):
            d = a[i] - b[i]
            if d != 0:
                return d
        return len(a) - len(b)

    def _bytes_equal(self, a: bytes, b: bytes) -> bool:
        """判断字节数组是否相等"""
        if len(a) != len(b):
            return False
        return all(a[i] == b[i] for i in range(len(a)))

    def _read_slice_from_end(self, data: bytes, start: int, length: int) -> bytes:
        """从指定位置读取字节切片"""
        if length < 0:
            return data[start:]
        return data[start:start + length]

    def _display_index_to_storage_index(self, display_index: int) -> int:
        """将显示索引值（1-9）转换为存储索引值（1537-1545）
        
        Args:
            display_index: 显示索引值（1-9）
            
        Returns:
            存储索引值（1537-1545）
        """
        BASE_OFFSET = 1536  # 0x600
        storage_index = BASE_OFFSET + display_index
        
        # 确保在有效范围内
        if storage_index < 1537:
            return 1537
        if storage_index > 1545:
            return 1545
        return storage_index

    def _build_header(self, header_pinyin_len: int, index: int, tail: bytes) -> bytes:
        """构建记录头"""
        h = bytearray(16)
        struct.pack_into('<H', h, 0, 0x0010)
        struct.pack_into('<H', h, 2, 0x0010)
        struct.pack_into('<H', h, 4, header_pinyin_len)
        struct.pack_into('<I', h, 6, self._display_index_to_storage_index(index))
        struct.pack_into('<H', h, 10, 0x0006)
        struct.pack_into('<H', h, 12, 0x0000)
        h[14] = tail[0] if len(tail) > 0 else 0xA5
        h[15] = tail[1] if len(tail) > 1 else 0x2C
        return bytes(h)

    def _replace_bytes(self, path: str, position: int, value: bytes) -> None:
        """替换指定位置的字节"""
        with open(path, 'r+b') as f:
            f.seek(position)
            f.write(value)
