# MSPhraseTool - 微软拼音短语管理神器


## 能做什么？

- **批量导入**：一键导入几百条自定义短语
- **导出备份**：把现有短语导出成 CSV 文件，方便编辑和备份
- **格式转换**：支持百度、搜狗、微软、Rime、多多等格式互转，自动检测编码
- **查看管理**：查看现有短语，支持搜索过滤
- **交互式编辑**：修改单个短语的拼音、位置或内容
- **安全备份**：导入前自动备份原文件，不怕搞错
- **云端同步**：支持上传到 S3 存储，多设备同步，自动生成安装命令
- **批量删除**：清空所有自定义短语（带确认保护）

## 快速上手

### 安装要求
- Python 3.11+
- Windows 10/11 系统

### 基本用法

```bash
# 查看帮助
python main.py -h

# 针对某个模块的帮助
python main.py --help

# 导出现有短语（默认保存为"自定义短语.csv"）
python main.py export

# 导入短语文件（CSV 格式）
python main.py import 自定义短语.csv

# 查看所有现有短语
python main.py list

# 转换格式（如百度转微软）
python main.py convert --format bd --input 百度短语.txt
```

## 短语文件格式

### CSV 格式（推荐）

用于 import 和 export 命令的标准格式：

```csv
pinyin,index,text
clc,1,Claude Code
cgp,1,ChatGPT
vs,1,Visual Studio
py,1,Python
js,1,JavaScript
```

**说明：**
- **第一行是表头**：`pinyin,index,text`（必需）
- **拼音**：最多 32 个字母，大小写都行，不能用 u/v 开头
- **位置**：1-9 的数字，同个拼音可以有多个候选
- **短语**：最多 64 个字符
- **编码**：UTF-8

### 其他格式

convert 命令支持以下输入格式：
- 百度/搜狗：文本文件，每行 `短语 拼音`
- Rime：YAML 格式
- 微软：二进制 .lex 文件
- 多多：特定格式文本文件

## 命令详解

### 工作流程示例

**首次使用：**
```bash
# 1. 导出当前系统短语（备份）
python main.py export

# 2. 编辑导出的 CSV 文件，添加新短语
# 3. 导入修改后的短语
python main.py import 自定义短语.csv --verbose
```

**从其他输入法迁移：**
```bash
# 1. 转换格式（如从百度输入法）
python main.py convert --format bd --input 百度短语.txt

# 2. 查看转换结果
python main.py list

# 3. 导入到系统
python main.py import out/百度短语.csv
```

**云端同步：**
```bash
# 1. 配置 .env 文件（S3 信息）
# 2. 上传当前短语
python main.py upload

# 3. 在新设备上下载并导入
```

### 1. export - 导出短语

把系统里的自定义短语导出成 CSV 文件

```bash
# 基本用法（导出到默认文件"自定义短语.csv"）
python main.py export

# 导出到指定文件
python main.py export 我的备份.csv

# 指定词库文件路径（一般用不到）
python main.py export --lex "C:\词库路径\ChsPinyinEUDPv1.lex"
```

### 2. import - 导入短语

从 CSV 文件批量导入自定义短语到系统

```bash
# 基本导入（自动备份原文件）
python main.py import 短语文件.csv

# 查看详细信息，看看导入了多少条
python main.py import 短语文件.csv --verbose

# 只检查不实际导入（测试用）
python main.py import 短语文件.csv --dry-run

# 不备份直接导入（谨慎使用）
python main.py import 短语文件.csv --no-backup

# 指定词库文件
python main.py import 短语文件.csv --lex "自定义路径.lex"
```

**输入文件格式：**
- CSV 格式，包含表头：`pinyin,index,text`
- 每行一条短语，格式：`拼音，位置，短语内容`
- 支持 UTF-8 编码

### 3. list - 查看短语

查看系统里现有的自定义短语

```bash
# 查看所有短语
python main.py list

# 只看某个拼音开头的短语
python main.py list --filter clc

# 指定词库文件
python main.py list --lex "自定义路径.lex"
```

### 4. convert - 格式转换

在不同输入法格式之间转换短语，支持自动编码检测

```bash
# 查看支持的所有格式
python main.py convert --list-formats

# 百度格式转微软格式
python main.py convert --format bd --input 百度短语.txt

# 搜狗格式转微软格式，指定输出文件夹
python main.py convert --format sg --input 搜狗短语.txt --output 我的转换

# CSV 格式转微软格式
python main.py convert --format csv --input 我的短语.csv

# 微软格式转 CSV（导出用）
python main.py convert --format wr --input ChsPinyinEUDPv1.lex
```

**支持的格式：**
- `bd` - 百度输入法（UTF-8 编码）
- `sg` - 搜狗输入法（UTF-8 编码）
- `wr` - 微软拼音（二进制，内部 UTF-16LE）
- `rime` - Rime 输入法（UTF-8 编码）
- `dd` - 多多输入法（UTF-8 编码）
- `csv` - CSV 格式（拼音，位置，短语）

**智能编码检测：**
- 自动检测文件编码（需要安装 chardet 库）
- 支持 utf-16-le 自动转换为 utf-8
- 非预期编码会报错提示

### 5. debug - 调试信息

查看系统信息和词库状态

```bash
# 基本调试信息
python main.py debug

# 详细调试信息
python main.py debug --verbose
```

### 6. delete - 删除短语

清空微软拼音的自定义短语

```bash
# 查看将要删除什么（安全检查）
python main.py delete --dry-run

# 确认删除（会提示确认）
python main.py delete

# 强制删除，不提示确认
python main.py delete --force
```

### 7. edit - 交互式编辑

修改单个短语（交互式操作）

```bash
# 启动交互式编辑
python main.py edit

# 指定词库文件
python main.py edit --lex "自定义路径.lex"
```

### 8. upload - 上传到云端

上传短语文件到 S3 存储，支持自动转换和生成安装命令

```bash
# 上传当前短语（自动转换并上传）
python main.py upload
```

**功能特点：**
- 自动将 .lex 文件转换为文本格式后上传
- 支持同步多个自定义文件（通过 .env 配置）
- 上传后显示文件 URL 和安装命令
- 支持配置是否转换格式再上传

**配置说明（.env 文件）：**
```env
# 是否包含 .lex 文件
INCLUDE_LEX_FILE=true

# 上传前是否转换格式
CONVERT_BEFORE_UPLOAD=true

# 要同步的文件模式（逗号分隔）
SYNC_FILES=*.txt,*.csv，微软拼音短语_*.txt
```

## 实用场景

### 程序员必备短语
```
clc,1,Claude Code
cgp,1,ChatGPT
vs,1,Visual Studio
py,1,Python
js,1,JavaScript
git,1,git status
npm,1,npm install
```

### 数据库工程师
```
pgs,1,PostgreSQL
mss,1,Microsoft SQL Server
mysql,1,MySQL
redis,1,Redis
mongo,1,MongoDB
```

### 时间日期快捷输入
```
rq,1,%yyyy%-%MM%-%dd%
sj,1,%hh%:%mm%
week,1,本周
month,1,本月
year,1,今年
```

### 办公常用
```
zh,1,中华人民共和国
gk,1,高考
jw,1,教务处
xsc,1,学生处
bm,1,部门
```

## 注意事项

- **备份很重要**：导入前会自动备份，文件名带时间戳
- **拼音规则**：不能用 u/v 开头，最多 32 个字母
- **位置范围**：必须是 1-9 的数字
- **短语长度**：最多 64 个字符
- **系统兼容**：某些系统有"用户短语隔离"功能，可能影响同步
- **文件位置**：默认操作 `%APPDATA%\Microsoft\InputMethod\Chs\ChsPinyinEUDPv1.lex`

## 高级配置

### 环境变量配置

创建 `.env` 文件可以配置一些高级选项：

```env
# S3 上传配置
AWS_ACCESS_KEY_ID=你的密钥
AWS_SECRET_ACCESS_KEY=你的密钥
S3_BUCKET_NAME=你的桶名
S3_ENDPOINT_URL=https://s3.amazonaws.com
S3_DIRECTORY=upload/

# 上传前是否转换格式
CONVERT_BEFORE_UPLOAD=true
```

### 常见问题

**Q: 导入后没生效？**
A: 重启输入法或者重启电脑试试，某些系统需要刷新

**Q: 提示文件被占用？**
A: 关闭所有正在使用输入法的程序，或者重启电脑

**Q: 短语太多导入失败？**
A: 分批导入，一次几百条比较稳妥

## 项目结构

```
MSPhraseTool/
├── pinyin_lex_tool/          # 核心代码
│   ├── cli.py               # 命令行界面
│   ├── service.py           # 业务逻辑
│   ├── models.py            # 数据模型
│   ├── lex_reader.py        # 读取词库文件
│   ├── lex_writer.py        # 写入词库文件
│   └── paths.py             # 路径工具
├── tool/                    # 工具脚本
│   ├── phrase_converter.py  # 格式转换
│   └── upload_to_s3.py      # S3 上传
└── README.md               # 说明文档
```

## 贡献

欢迎提问题和改进建议！

1. Fork 项目
2. 创建分支 (`git checkout -b feature/新功能`)
3. 提交更改 (`git commit -m '添加新功能'`)
4. 推送分支 (`git push origin feature/新功能`)
5. 提交 Pull Request

## 许可证

MIT License - 随便用

---
## 项目致谢：

1. https://github.com/mchudie/PinyinLexTool/releases ：功能转换参考
2. 看雪论坛：关于逆向后偏移量的问题解决

**让微软拼音输入法更好用！**
