"""读取.lex 文件"""
import struct
from pathlib import Path
from typing import List, Optional

from .models import PinyinPhrase


class LexFileReader:
    """.lex 文件读取器"""

    def __init__(self):
        self.PHRASE_CNT_POS = 0x1C
        self.PHRASE_LEN_FIRST_POS = 0x44

    def read_all(self, lex_path: str) -> List[PinyinPhrase]:
        """读取 .lex 文件中的所有短语

        Args:
            lex_path: .lex 文件完整路径

        Returns:
            短语列表
        """
        with open(lex_path, 'rb') as f:
            data = f.read()

        if len(data) < self.PHRASE_LEN_FIRST_POS:
            return []

        phrase_count = struct.unpack('<I', data[self.PHRASE_CNT_POS:self.PHRASE_CNT_POS + 4])[0]
        if phrase_count <= 0:
            return []

        first_offset_pos = self.PHRASE_LEN_FIRST_POS
        first_block_pos = first_offset_pos + 4 * (phrase_count - 1)

        result = []
        last_pos = 0

        for i in range(phrase_count):
            if i == phrase_count - 1:
                block_pos = -1
            else:
                offset_pos = first_offset_pos + i * 4
                block_pos = struct.unpack('<I', data[offset_pos:offset_pos + 4])[0]

            block_len = -1 if block_pos == -1 else (block_pos - last_pos)
            seg = self._read_slice_from_end(data, first_block_pos + last_pos, block_len)
            last_pos = block_pos

            if len(seg) < 16:
                continue

            if len(seg) > 9 and seg[9] != 0x00:
                continue

            body = seg[16:]
            parts = self._split_by_00(body, min_part_bytes=2)

            if len(parts) < 2:
                continue

            pinyin = parts[0].decode('utf-16-le').strip()
            phrase = parts[1].decode('utf-16-le').replace('\r\n', '\n').strip()

            storage_index = struct.unpack('<I', seg[6:10])[0]
            display_index = self._storage_index_to_display_index(storage_index)

            if not pinyin or not phrase:
                continue

            result.append(PinyinPhrase(pinyin=pinyin, index=display_index, text=phrase))

        result.sort(key=lambda x: (x.pinyin, x.index))
        return result

    def _split_by_00(self, buf: bytes, min_part_bytes: int) -> List[bytes]:
        """按 00 00 分隔字节数组"""
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

    def _read_slice_from_end(self, data: bytes, start: int, length: int) -> bytes:
        """从指定位置读取字节切片"""
        if length < 0:
            return data[start:]
        return data[start:start + length]

    def _storage_index_to_display_index(self, storage_index: int) -> int:
        """将存储的索引值转换为显示索引值（1-9）
        
        Args:
            storage_index: 从文件读取的存储索引值
            
        Returns:
            显示索引值（1-9）
        """
        BASE_OFFSET = 1536  # 0x600
        display_index = storage_index - BASE_OFFSET
        
        # 确保在有效范围内
        if display_index < 1:
            return 1
        if display_index > 9:
            return 9
        return display_index
