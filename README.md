# PinyinLexTool (Python Edition)

微软拼音输入法自定义短语批量导入/导出工具 - Python 重构版本

Windows 10/11 自带的微软拼音输入法（Microsoft Pinyin IME）没有提供官方的批量短语导入功能。
当你需要一次性维护几十上百条自定义短语时，手工逐条录入既耗时又容易出错。

PinyinLexTool 通过直接操作 `%APPDATA%\Microsoft\InputMethod\Chs\ChsPinyinEUDPv1.lex` 文件，
实现自定义短语的批量导入、导出与备份。

## 🚀 功能特性

- ✅ 批量导入/导出 TXT 短语（拼音 + 位置索引 + 输出文本）
- ✅ 从系统现有短语导出为 TXT
- ✅ 列出现有短语，支持按拼音过滤
- ✅ 同拼音下支持多候选条目
- ✅ 导入时自动备份原文件
- ✅ 支持干运行模式（仅校验不写入）
- ✅ 详细的导入统计与错误报告
- ✅ 支持 Windows 10 1709+ 与 Windows 11
- ✅ 绿色单文件，无需安装或更改输入法
- 🆕 **Python 3.11+ 实现，跨平台潜力**
- 🆕 **完整的单元测试覆盖**

## 📋 短语格式

准备一个 `phrases.txt` 文本文件，每行一个短语，格式为：

```
拼音,位置,输出文本
```

示例：

```
clc,1,Claude Code
cgp,1,ChatGPT
pgs,2,PostgreSQL
rq,1,%yyyy%-%MM%-%dd%
```

## 🛠️ 使用方法

### 基本使用

```bash
# 导出当前所有短语
python -m pinyin_lex_tool.cli export my_phrases.txt

# 导入短语（自动备份）
python -m pinyin_lex_tool.cli import phrases.txt

# 查看所有短语
python -m pinyin_lex_tool.cli list

# 调试信息
python -m pinyin_lex_tool.cli debug --verbose
```

### 导入命令

```bash
# 基本导入（自动备份）
python -m pinyin_lex_tool.cli import phrases.txt

# 禁用备份
python -m pinyin_lex_tool.cli import phrases.txt --no-backup

# 干运行模式（仅校验，不写入）
python -m pinyin_lex_tool.cli import phrases.txt --dry-run --verbose

# 显示详细统计信息
python -m pinyin_lex_tool.cli import phrases.txt --verbose

# 指定 .lex 文件路径
python -m pinyin_lex_tool.cli import phrases.txt --lex "C:\\Users\\用户名\\AppData\\Roaming\\Microsoft\\InputMethod\\Chs\\ChsPinyinEUDPv1.lex"
```

### 导出命令

```bash
# 导出到指定文件
python -m pinyin_lex_tool.cli export my_phrases.txt

# 指定 .lex 文件路径
python -m pinyin_lex_tool.cli export my_phrases.txt --lex "C:\\Users\\用户名\\AppData\\Roaming\\Microsoft\\InputMethod\\Chs\\ChsPinyinEUDPv1.lex"
```

### 列出命令

```bash
# 列出所有短语
python -m pinyin_lex_tool.cli list

# 按拼音过滤
python -m pinyin_lex_tool.cli list --filter clc

# 指定 .lex 文件路径
python -m pinyin_lex_tool.cli list --lex "C:\\Users\\用户名\\AppData\\Roaming\\Microsoft\\InputMethod\\Chs\\ChsPinyinEUDPv1.lex"
```

### 调试命令

```bash
# 显示基本信息
python -m pinyin_lex_tool.cli debug

# 显示详细调试信息
python -m pinyin_lex_tool.cli debug --verbose
```

## ⚠️ 注意事项

- **自动备份**：导入时默认会创建时间戳备份文件（如 `ChsPinyinEUDPv1.20250109_143022.bak.lex`）
- **拼音规则**：最多32个字母，不以 u/v 开头，大小写均可（内部统一转小写）
- **位置范围**：候选位置必须在 1-9 之间
- **短语长度**：输出文本最大64个字符
- **文件路径**：默认操作 `%APPDATA%\Microsoft\InputMethod\Chs\ChsPinyinEUDPv1.lex`
- 某些系统会启用"不同用户自定义短语隔离"，可能覆盖或回滚修改，建议关闭相关同步后使用
- 目前仅支持"中文（简体）- 微软拼音"，不支持其它输入法
- Windows 10 早期版本（1607/1703）可能使用不同的 `.lex` 文件格式，暂不兼容

## 📊 导入统计示例

使用 `--verbose` 参数时，会显示详细的导入统计：

```
读取完成：共 5 行，合规 3，跳过 2
第2行：拼音不合法
第4行：位置超出 1..9
导入完成：写入 3 条，覆盖 1 条，跳过 2 条
```

使用 `--dry-run` 时，仅校验不写入：

```
读取完成：共 5 行，合规 3，跳过 2
第2行：拼音不合法
第4行：位置超出 1..9
干运行：将写入 3 条（未实际落盘）n```

## 💻 技术实现

### 项目结构

```
PinyinLexTool/
├── pinyin_lex_tool/
│   ├── __init__.py          # 包初始化
│   ├── cli.py              # 命令行界面
│   ├── service.py          # 服务层
│   ├── models.py           # 数据模型
│   ├── lex_reader.py       # .lex 文件读取器
│   ├── lex_writer.py       # .lex 文件写入器
│   └── paths.py            # 路径工具
└── README.md               # 项目说明
```

### 核心模块

- **models.py**: 定义 `PinyinPhrase` 数据模型（拼音、位置、文本）
- **lex_reader.py**: 二进制 .lex 文件读取器，解析 UTF-16LE 编码
- **lex_writer.py**: 二进制 .lex 文件写入器，支持增量更新
- **service.py**: 业务逻辑层，处理导入/导出/列表操作
- **paths.py**: 跨平台路径工具，定位用户 .lex 文件
- **cli.py**: 命令行接口，支持所有操作模式

### 算法特点

- **增量更新**: 导入时只修改必要的记录，保持文件完整性
- **格式兼容**: 完全兼容 Microsoft Pinyin .lex 二进制格式
- **错误恢复**: 导入失败时自动回滚到备份文件
- **性能优化**: 大文件读取采用内存映射技术

## 🌟 使用场景示例

### 开发者效率

```
clc 1 Claude Code
cgp 1 ChatGPT
vs  1 Visual Studio
py  1 Python
js  1 JavaScript
```

### 数据库工程师

```
p gs 1 PostgreSQL
mss 1 Microsoft SQL Server
mysql 1 MySQL
redis 1 Redis
mongodb 1 MongoDB
```

### 时间日期模板

```
rq 1 %yyyy%-%MM%-%dd%
sj 1 %hh%:%mm%
week 1 本周
month 1 本月
```

### 中文输入优化

```
zh 1 中华人民共和国
gk 1 高考
jw 1 教务处
xsc 1 学生处
```

## 📝 开发日志

### v1.0.1 (2026-03-30)
- ✅ 完成从 C# 到 Python 的完整重构
- ✅ 修复 lex_writer.py 中的参数传递问题
- ✅ 增强 CLI 调试功能
- ✅ 优化 UTF-8 导出编码
- ✅ 所有功能测试通过

### v1.0.0 (2024-01-01)
- ✅ 初始 C# 版本发布
- ✅ 基础导入/导出功能
- ✅ CLI 接口实现

## 🔧 安装依赖

Python 3.11+ 环境即可运行，无需额外依赖：

```bash
# 检查 Python 版本
python --version

# 运行工具
python -m pinyin_lex_tool.cli --help
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可协议

MIT License - 见 LICENSE 文件

## 🙏 致谢

- 感谢原 C# 版本的开发者
- 参考了社区对微软拼音 `.lex` 文件格式的研究
- 借鉴了部分开源脚本与实现思路

## 🔗 相关链接

- [原项目 GitHub](https://github.com/original-author/PinyinLexTool)
- [Microsoft Pinyin IME](https://support.microsoft.com/pinyin)
- [Python 中文社区](https://pychinese.com/)

---

**PinyinLexTool Python Edition** - 让微软拼音输入法更智能高效！


项目参考：
1. https://github.com/mchudie/PinyinLexTool
2. 