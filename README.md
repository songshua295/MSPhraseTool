# MSPhraseTool - 微软拼音短语管理神器


## 能做什么？

- **批量导入**：一键导入几百条自定义短语
- **导出备份**：把现有短语导出成 CSV 文件，方便编辑和备份
- **格式转换**：支持百度、搜狗、微软、Rime、多多等格式互转，自动检测编码
- **查看管理**：查看现有短语，支持搜索过滤
- **交互式编辑**：修改单个短语的拼音、位置或内容
- **安全备份**：导入前自动备份原文件，不怕搞错
- **云端同步**：支持上传到 S3 存储，多设备同步，自动生成安装命令
- **网页版**：纯静态网页（`web/` 目录），支持云端短语加载 / 在线编辑 / 上传替换
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

## 打包使用

### 使用打包的EXE文件

项目提供了打包成独立EXE文件的功能，无需安装Python环境即可使用。

**快速开始：**
```bash
# 使用打包的EXE文件
MSPhraseTool.exe --help
MSPhraseTool.exe export
MSPhraseTool.exe import 短语文件.csv
```

**详细使用指南：**
- [CLI_USAGE.md](CLI_USAGE.md) - 完整的命令行工具使用说明
- 包含安装方式、所有命令详解、常见问题等

**打包方法：**
项目包含 `build_exe.py` 脚本，可以一键打包：
```bash
# 安装PyInstaller
pip install pyinstaller

# 运行打包脚本
python build_exe.py
```

打包完成后会在 `dist` 目录生成 `MSPhraseTool.exe` 文件。

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

### convert 命令支持格式

| 格式代码 | 对应输入法 | 文件格式 |
|----------|-----------|----------|
| `bd` | 百度输入法 | UTF-8 文本 |
| `sg` | 搜狗输入法 | UTF-8 文本 |
| `dat` | 微软拼音 .dat | 二进制，UTF-16LE |
| `lex` | 微软拼音 .lex | 二进制，UTF-16LE |
| `rime` | Rime 输入法 | UTF-8 文本 |
| `dd` | 多多输入法 | UTF-8 文本 |
| `csv` | 通用 CSV | UTF-8 文本 |

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

# 微软 .lex 转 CSV（导出用）
python main.py convert --format lex --input ChsPinyinEUDPv1.lex

# 微软 .dat 转 CSV
python main.py convert --format dat --input 微软短语.dat

**支持的格式：**
- `bd` - 百度输入法（UTF-8 编码）
- `sg` - 搜狗输入法（UTF-8 编码）
- `dat` - 微软拼音 .dat 格式（二进制，内部 UTF-16LE）
- `lex` - 微软拼音 .lex 格式（二进制，内部 UTF-16LE）
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

## 网页版（在线转换与云端同步）

`web/` 目录提供纯静态网页版，无需安装任何东西，把 `web/` 托管到任意静态空间（GitHub Pages、S3 静态托管等）或本地 `python -m http.server` 后访问 `index.html` 即可。

功能：

1. **云端短语**：点击「加载短语」才从配置的源（S3 / GitHub）拉取短语文件（默认搜狗格式）进入表格编辑；编辑完成后点击「上传替换」直接覆盖远端文件（S3 覆盖上传 / GitHub 提交替换），目标可单选或多选
2. **格式转换**：本地文件 / 远程 URL / 粘贴导入，百度 / 搜狗 / 微软 .dat / .lex / Rime / 多多 / CSV 互转，表格编辑（搜索 + 分页）
3. **页脚配置命令与下载**：小鹤双拼注册表命令、微软词库 PowerShell 下载命令、各词库在线下载地址、桌面版 EXE 下载

### 网页版配置（web/.env）

复制 `web/.env.example` 为 `web/.env`（已被 .gitignore 忽略）并填写。主要配置项：

| 配置键 | 说明 |
| --- | --- |
| `ACCESS_CODE_HASH` | 访问码的 SHA-256 值，页面打开需输入访问码解锁 |
| `SYNC_TARGETS` | 同步目标，逗号分隔，可含 `s3`、`github`（可单选/多选） |
| `DEFAULT_SOURCE` | 「加载短语」的默认源；页面上也可下拉切换 |
| `PHRASE_FORMAT` | 短语文件格式，默认 `sg`（搜狗） |
| `S3_ENDPOINT_URL` / `S3_REGION` / `S3_BUCKET` / `S3_PATH` / `S3_FILENAME` | S3（兼容 S3 协议）的地址、区域、桶、路径与文件名 |
| `S3_PUBLIC_URL` | 公开读的基础 URL（加载用）；留空则用签名 GET |
| `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` | S3 凭证（建议加密存储） |
| `GITHUB_REPO` / `GITHUB_BRANCH` / `GITHUB_PATH` / `GITHUB_FILENAME` | GitHub 仓库、分支、路径与文件名 |
| `GITHUB_TOKEN` | 需要 contents 写权限的 Token（建议加密存储） |

**凭证加密**：S3 密钥和 GitHub Token 会明文出现在网页可下载的配置文件中，因此推荐用 `index.html` 页脚「配置生成器」生成：输入访问码与明文凭证，得到 `enc:v1:...` 密文（访问码派生的 AES-GCM 密钥加密）。页面解锁时在浏览器内解密，配置文件中不出现明文。

**S3 上传 CORS**：浏览器直接 PUT 需要 bucket 开启 CORS，示例（Bitiful / AWS S3 控制台均可配置）：

```json
[
  {
    "AllowedOrigins": ["https://你的站点域名"],
    "AllowedMethods": ["GET", "PUT"],
    "AllowedHeaders": ["*"]
  }
]
```

**注意**：本页必须通过 HTTP(S) 方式访问（直接双击 file:// 打开会因浏览器限制无法读取 `web/.env`，此时自动降级为仅本地转换功能）。

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

## 相关文档

- [CLI_USAGE.md](CLI_USAGE.md) - 完整的命令行工具使用说明
- 包含打包EXE使用指南、所有命令详解、常见问题解答

---
## 项目致谢：

1. https://github.com/mchudie/PinyinLexTool/releases ：功能转换参考
2. 看雪论坛：关于逆向后偏移量的问题解决

**让微软拼音输入法更好用！**
