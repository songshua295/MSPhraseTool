# MSPhraseTool 命令行使用指南

## 目录
- [快速开始](#快速开始)
- [安装方式](#安装方式)
- [基本命令](#基本命令)
- [详细命令说明](#详细命令说明)
- [打包成EXE](#打包成exe)
- [常见问题](#常见问题)

## 快速开始

### 使用Python运行
```bash
# 查看帮助
python main.py --help

# 导出现有短语
python main.py export

# 导入短语文件
python main.py import 自定义短语.csv

# 查看所有短语
python main.py list
```

### 使用打包的EXE运行
```bash
# 查看帮助
MSPhraseTool.exe --help

# 导出现有短语
MSPhraseTool.exe export

# 导入短语文件
MSPhraseTool.exe import 自定义短语.csv

# 查看所有短语
MSPhraseTool.exe list
```

## 安装方式

### 方式一：Python环境运行
1. 确保已安装 Python 3.11+
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 运行工具：
   ```bash
   python main.py [命令]
   ```

### 方式二：使用打包的EXE（推荐）
1. 下载 `MSPhraseTool.exe` 文件
2. 直接双击运行或通过命令行使用
3. 无需安装Python环境

### 方式三：使用批处理包装器
1. 下载 `MSPhraseTool.bat` 和 `MSPhraseTool.exe`
2. 将两个文件放在同一目录
3. 双击 `MSPhraseTool.bat` 或通过命令行使用

## 基本命令

### 1. 查看帮助
```bash
# 查看所有命令
MSPhraseTool.exe --help

# 查看特定命令的帮助
MSPhraseTool.exe export --help
MSPhraseTool.exe import --help
```

### 2. 工作流程示例

**首次使用：**
```bash
# 1. 导出当前系统短语（备份）
MSPhraseTool.exe export

# 2. 编辑导出的 CSV 文件，添加新短语
# 3. 导入修改后的短语
MSPhraseTool.exe import 自定义短语.csv --verbose
```

**从其他输入法迁移：**
```bash
# 1. 转换格式（如从百度输入法）
MSPhraseTool.exe convert --format bd --input 百度短语.txt

# 2. 查看转换结果
MSPhraseTool.exe list

# 3. 导入到系统
MSPhraseTool.exe import out/百度短语.csv
```

## 详细命令说明

### export - 导出短语
导出系统当前的自定义短语到CSV文件。

```bash
# 导出到默认文件"自定义短语.csv"
MSPhraseTool.exe export

# 导出到指定文件
MSPhraseTool.exe export my_phrases.csv

# 导出指定词库文件
MSPhraseTool.exe export --lex "自定义路径.lex"
```

**输出格式：**
```csv
pinyin,index,text
clc,1,Claude Code
cgp,1,ChatGPT
vs,1,Visual Studio
```

### import - 导入短语
从CSV文件导入短语到系统。

```bash
# 基本导入（自动备份原文件）
MSPhraseTool.exe import 短语文件.csv

# 查看详细信息
MSPhraseTool.exe import 短语文件.csv --verbose

# 只检查不实际导入（测试用）
MSPhraseTool.exe import 短语文件.csv --dry-run

# 不备份直接导入（谨慎使用）
MSPhraseTool.exe import 短语文件.csv --no-backup
```

**输入文件要求：**
- CSV格式，UTF-8编码
- 包含表头：`pinyin,index,text`
- 每行一条短语

### list - 查看短语
查看系统里现有的自定义短语。

```bash
# 查看所有短语
MSPhraseTool.exe list

# 按拼音过滤
MSPhraseTool.exe list --filter clc

# 查看指定词库文件
MSPhraseTool.exe list --lex "自定义路径.lex"
```

### convert - 格式转换
在不同输入法格式之间转换短语。

```bash
# 查看支持的格式
MSPhraseTool.exe convert --list-formats

# 百度格式转微软格式
MSPhraseTool.exe convert --format bd --input 百度短语.txt

# 搜狗格式转微软格式，指定输出文件夹
MSPhraseTool.exe convert --format sg --input 搜狗短语.txt --output 我的转换

# CSV格式转微软格式
MSPhraseTool.exe convert --format csv --input 我的短语.csv

# 微软格式转CSV（导出用）
MSPhraseTool.exe convert --format wr --input ChsPinyinEUDPv1.lex
```

**支持的格式：**
- `bd`: 百度格式
- `sg`: 搜狗格式  
- `wr`: 微软 .dat 格式
- `lex`: 微软 .lex 格式
- `rime`: Rime格式
- `dd`: 多多格式
- `csv`: CSV格式

### delete - 删除短语
删除微软拼音自定义短语。

```bash
# 交互式删除（需要确认）
MSPhraseTool.exe delete

# 强制删除（不提示确认）
MSPhraseTool.exe delete --force

# 只显示将要删除的文件，不实际删除
MSPhraseTool.exe delete --dry-run
```

### edit - 交互式编辑
交互式修改单个短语。

```bash
# 启动交互式编辑器
MSPhraseTool.exe edit

# 编辑指定词库文件
MSPhraseTool.exe edit --lex "自定义路径.lex"
```

### upload - 上传到S3
上传文件到S3存储（需要配置.env文件）。

```bash
# 上传文件到S3
MSPhraseTool.exe upload
```

**需要配置：**
在项目根目录创建 `.env` 文件，包含以下配置：
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=your_bucket_name
S3_ENDPOINT_URL=https://your-s3-endpoint.com
```

### debug - 调试信息
显示调试信息。

```bash
# 显示基本调试信息
MSPhraseTool.exe debug

# 显示详细信息（包括短语列表）
MSPhraseTool.exe debug --verbose
```

## 打包成EXE

### 方法一：使用提供的打包脚本
项目包含 `build_exe.py` 脚本，可以一键打包：

```bash
# 安装PyInstaller
pip install pyinstaller

# 运行打包脚本
python build_exe.py
```

打包完成后会在 `dist` 目录生成 `MSPhraseTool.exe` 文件。

### 方法二：手动打包
```bash
# 安装依赖
pip install -r requirements.txt
pip install pyinstaller

# 打包成单文件EXE
pyinstaller --onefile --name=MSPhraseTool --console \
  --add-data=tool;tool \
  --add-data=pinyin_lex_tool;pinyin_lex_tool \
  --hidden-import=chardet \
  --hidden-import=boto3 \
  --hidden-import=botocore \
  --hidden-import=python_dotenv \
  --clean \
  main.py
```

### 打包注意事项
1. **文件大小**：打包后的EXE文件约20-30MB
2. **依赖包含**：所有Python依赖都已打包到EXE中
3. **无需Python**：用户无需安装Python即可运行
4. **兼容性**：在Windows 10/11上测试通过

## 常见问题

### Q1: EXE文件运行报错怎么办？
**可能原因：**
1. 缺少VC++运行库
2. 系统权限问题
3. 文件损坏

**解决方案：**
1. 安装 [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. 以管理员身份运行
3. 重新下载或打包EXE文件

### Q2: 导入时提示"文件不存在"？
**检查：**
1. 文件路径是否正确
2. 文件是否被其他程序占用
3. 是否有读写权限

### Q3: 转换格式时编码错误？
**解决方案：**
1. 确保源文件使用UTF-8编码
2. 对于其他编码，先转换为UTF-8
3. 使用 `--verbose` 参数查看详细错误信息

### Q4: 如何批量操作？
**示例：批量导入多个文件**
```bash
# Windows批处理
for %%f in (*.csv) do (
    MSPhraseTool.exe import "%%f"
)
```

### Q5: 如何备份和恢复？
**备份：**
```bash
MSPhraseTool.exe export backup.csv
```

**恢复：**
```bash
MSPhraseTool.exe import backup.csv
```

## 高级用法

### 环境变量配置
可以通过环境变量配置工具行为：

```bash
# 设置默认词库路径
set MS_PHRASE_LEX_PATH=C:\path\to\custom.lex
MSPhraseTool.exe list

# 设置输出编码
set PYTHONIOENCODING=utf-8
MSPhraseTool.exe export
```

### 脚本集成
可以将MSPhraseTool集成到其他脚本中：

```python
# Python脚本示例
import subprocess
import json

# 导出短语到JSON
result = subprocess.run(
    ['MSPhraseTool.exe', 'export', 'phrases.csv'],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("导出成功")
else:
    print(f"导出失败: {result.stderr}")
```

### 自动化工作流
```bash
# 每日备份脚本
@echo off
set DATE=%date:~0,4%%date:~5,2%%date:~8,2%
MSPhraseTool.exe export backup_%DATE%.csv
echo 备份完成: backup_%DATE%.csv
pause
```

## 更新日志

### v1.0.0
- 初始版本发布
- 支持基本导入/导出功能
- 支持格式转换
- 支持打包成EXE

### v1.0.1
- 修复UTF-16-LE编码支持
- 优化打包脚本
- 添加详细使用文档

---

**提示：** 使用 `MSPhraseTool.exe --help` 查看最新命令帮助信息。