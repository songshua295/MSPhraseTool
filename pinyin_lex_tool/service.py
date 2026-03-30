"""拼音短语导入/导出服务"""
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional

from .models import PinyinPhrase
from .lex_reader import LexFileReader
from .lex_writer import LexFileWriter


class PinyinLexService:
    """拼音短语导入/导出服务"""

    def __init__(self, reader: LexFileReader):
        self._reader = reader

    def export(self, lex_path: str, output_path: str) -> None:
        """将 .lex 中的短语导出为 TXT 文件

        Args:
            lex_path: .lex 路径
            output_path: 输出 TXT 路径
        """
        phrases = self._reader.read_all(lex_path)

        lines = []
        for p in sorted(phrases, key=lambda x: (x.pinyin, x.index)):
            lines.append(f"{p.pinyin},{p.index},{p.text}")

        output_dir = Path(output_path).parent
        if output_dir and not output_dir.exists():
            output_dir.mkdir(parents=True)

        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            for i, line in enumerate(lines):
                f.write(line)
                if i < len(lines) - 1:
                    f.write('\n')

    def import_phrases(self, lex_path: str, input_path: str, backup: bool = True, 
                       dry_run: bool = False, verbose: bool = False) -> None:
        """从 TXT 导入短语到 .lex 文件

        Args:
            lex_path: .lex 文件路径
            input_path: 输入 TXT，格式：拼音 空格 索引 空格 文本
            backup: 是否备份原文件
            dry_run: 只校验不落盘
            verbose: 输出详细信息
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()

        lines = text.replace('\r\n', '\n').split('\n')

        total = 0
        ok = 0
        skipped = 0
        reasons = []
        items = []

        for raw in lines:
            total += 1
            line = raw.strip()
            
            if not line or line.startswith('#'):
                continue

            m = re.match(r'^\s*(\S+)\s*,\s*(\d+)\s*,\s*(.+?)\s*$', line)
            if not m:
                skipped += 1
                reasons.append(f"第{total}行：格式不匹配")
                continue

            pinyin = m.group(1).strip()
            index_str = m.group(2)
            text_part = m.group(3).strip()

            try:
                index = int(index_str)
            except ValueError:
                skipped += 1
                reasons.append(f"第{total}行：位置不是数字")
                continue

            if not self._validate_pinyin(pinyin):
                skipped += 1
                reasons.append(f"第{total}行：拼音不合法")
                continue

            if index < 1 or index > 9:
                skipped += 1
                reasons.append(f"第{total}行：位置超出 1..9")
                continue

            if not text_part or len(text_part) > 64:
                skipped += 1
                reasons.append(f"第{total}行：短语长度超限")
                continue

            items.append((pinyin.lower(), index, text_part))
            ok += 1

        if verbose:
            print(f"读取完成：共 {total} 行，合规 {ok}，跳过 {skipped}")
            for r in reasons:
                print(r)

        if dry_run:
            print(f"干运行：将写入 {ok} 条（未实际落盘）")
            return

        if backup and Path(lex_path).exists():
            dir_path = Path(lex_path).parent
            name = Path(lex_path).stem
            ext = Path(lex_path).suffix
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            bak_path = dir_path / f"{name}.{ts}.bak{ext}"
            shutil.copy2(lex_path, bak_path)

        writer = LexFileWriter()
        overwritten = writer.upsert(lex_path, items)

        print(f"导入完成：写入 {ok} 条，覆盖 {overwritten} 条，跳过 {skipped} 条")

    def list_phrases(self, lex_path: str, filter_pinyin: Optional[str] = None) -> List[PinyinPhrase]:
        """列出短语，支持按拼音过滤

        Args:
            lex_path: .lex 文件路径
            filter_pinyin: 可选的拼音过滤

        Returns:
            短语列表
        """
        phrases = self._reader.read_all(lex_path)

        if filter_pinyin:
            phrases = [p for p in phrases if p.pinyin.lower() == filter_pinyin.lower()]

        return phrases

    def _validate_pinyin(self, pinyin: str) -> bool:
        """校验拼音：最多 32 个小写字母"""
        if not pinyin or len(pinyin) > 32:
            return False

        for c in pinyin:
            if not ('a' <= c <= 'z' or 'A' <= c <= 'Z'):
                return False

        return True
