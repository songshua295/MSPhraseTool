"""数据模型定义"""
from dataclasses import dataclass
from typing import NamedTuple


class PinyinPhrase(NamedTuple):
    """表示一个自定义短语条目"""
    pinyin: str
    index: int
    text: str
