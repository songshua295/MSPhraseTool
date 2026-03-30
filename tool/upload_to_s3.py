import boto3
import datetime
import os
import urllib.parse
import pathlib
import glob
import subprocess
import sys
from botocore.exceptions import ClientError

# 安装需要的库：pip install boto3 python-dotenv

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ 缺少 python-dotenv 库，请运行: pip install python-dotenv")
    exit(1)

# 加载 .env 文件
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    print("❌ 未找到 .env 配置文件")
    exit(1)

# --- 从环境变量读取配置 ---
CONFIG = {
    "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID", ""),
    "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
    "S3_BUCKET_NAME": os.getenv("S3_BUCKET_NAME", ""),
    "S3_DIRECTORY": os.getenv("S3_DIRECTORY", ""),
    "AWS_REGION": os.getenv("AWS_REGION", ""),
    "S3_ENDPOINT_URL": os.getenv("S3_ENDPOINT_URL", ""),
    "INCLUDE_LEX_FILE": os.getenv("INCLUDE_LEX_FILE", "true").lower() != "false",
    "CONVERT_BEFORE_UPLOAD": os.getenv("CONVERT_BEFORE_UPLOAD", "true").lower() != "false",
    "SYNC_FILES": [pattern.strip() for pattern in os.getenv("SYNC_FILES", "*.txt,*.csv,微软拼音短语_*.txt").split(",") if pattern.strip()],
}

# --- 验证必要配置 ---
required_configs = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "S3_BUCKET_NAME", "S3_ENDPOINT_URL"]
missing_configs = [key for key in required_configs if not CONFIG[key]]
if missing_configs:
    print(f"❌ 缺少配置: {', '.join(missing_configs)}")
    exit(1)

# --- 配置区块结束 ---


def upload_files_to_s3(config_params):
    """上传文件到 S3 存储"""
    try:
        files_to_upload = []
        current_dir = os.getcwd()
        
        # 1. 处理 lex 文件
        if config_params["INCLUDE_LEX_FILE"]:
            appdata_path = os.environ.get('APPDATA')
            if appdata_path:
                lex_file_path = os.path.join(appdata_path, 'Microsoft', 'InputMethod', 'Chs', 'ChsPinyinEUDPv1.lex')
                if os.path.isfile(lex_file_path):
                    if config_params.get("CONVERT_BEFORE_UPLOAD"):
                        try:
                            project_root = os.path.dirname(os.path.dirname(__file__))
                            convert_cmd = [
                                sys.executable,
                                "-m", "pinyin_lex_tool.cli",
                                "convert",
                                "--format", "wr",
                                "--input", lex_file_path,
                                "--output", "out"
                            ]
                            result = subprocess.run(convert_cmd, capture_output=True, text=True, cwd=project_root)
                            if result.returncode == 0:
                                converted_file = os.path.join(project_root, "out", "ChsPinyinEUDPv1.txt")
                                if os.path.isfile(converted_file):
                                    files_to_upload.append(("ChsPinyinEUDPv1.txt", converted_file))
                                else:
                                    files_to_upload.append(("ChsPinyinEUDPv1.lex", lex_file_path))
                            else:
                                files_to_upload.append(("ChsPinyinEUDPv1.lex", lex_file_path))
                        except:
                            files_to_upload.append(("ChsPinyinEUDPv1.lex", lex_file_path))
                    else:
                        files_to_upload.append(("ChsPinyinEUDPv1.lex", lex_file_path))
        
        # 2. 处理同步文件
        for pattern in config_params["SYNC_FILES"]:
            pattern = pattern.strip()
            if pattern:
                for file_path in glob.glob(os.path.join(current_dir, pattern)):
                    if os.path.isfile(file_path):
                        file_name = os.path.basename(file_path)
                        if file_name != 'upload_to_s3.py' and not file_name.startswith('.'):
                            if not any(existing_name == file_name for existing_name, _ in files_to_upload):
                                files_to_upload.append((file_name, file_path))
        
        if not files_to_upload:
            print("📭 没有找到文件")
            return
        
        # 从配置字典中获取参数
        access_key_id = config_params["AWS_ACCESS_KEY_ID"]
        secret_access_key = config_params["AWS_SECRET_ACCESS_KEY"]
        bucket_name = config_params["S3_BUCKET_NAME"]
        s3_directory = config_params["S3_DIRECTORY"]
        region_name = config_params["AWS_REGION"]
        endpoint_url = config_params["S3_ENDPOINT_URL"]
        
        # 创建 S3 客户端
        s3 = boto3.client(
            's3',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region_name,
            endpoint_url=endpoint_url,
        )
        
        # 上传文件
        success_count = 0
        fail_count = 0
        
        for file_name, local_file_path in files_to_upload:
            try:
                s3_key = os.path.join(s3_directory.strip('/'), file_name).replace('\\', '/')
                file_size_mb = os.path.getsize(local_file_path) / (1024 * 1024)
                
                print(f"🔄 上传: {file_name} ({file_size_mb:.1f}MB)")
                with open(local_file_path, 'rb') as file_content:
                    s3.put_object(Bucket=bucket_name, Key=s3_key, Body=file_content)
                
                print(f"✅ {file_name}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ {file_name} - {e}")
                fail_count += 1
        
        # 结果汇总
        print(f"\n📊 成功: {success_count}, 失败: {fail_count}")
        
        # 显示已上传文件
        if success_count > 0:
            base_url = f"{endpoint_url}/{bucket_name}/{s3_directory.strip('/')}"
            print(f"\n🔗 已上传:")
            for file_name, _ in files_to_upload:
                print(f"  📄 {file_name}: {base_url}/{file_name}")
            
            # 如果上传了 lex 文件，显示安装命令
            lex_uploaded = any(file_name in ["ChsPinyinEUDPv1.lex", "ChsPinyinEUDPv1.txt"] for file_name, _ in files_to_upload)
            if lex_uploaded:
                lex_url = f"{base_url}/ChsPinyinEUDPv1.lex"
                print(f"\n🛠️ 安装命令:")
                print(f"del /f /q \"%APPDATA%\\Microsoft\\InputMethod\\Chs\\ChsPinyinEUDPv1.lex\" & curl -o \"%APPDATA%\\Microsoft\\InputMethod\\Chs\\ChsPinyinEUDPv1.lex\" \"{lex_url}\" & pause")
        
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        error_message = e.response.get("Error", {}).get("Message")
        print(f"❌ S3错误: {error_code} - {error_message}")
    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    print(f"📋 存储桶: {CONFIG['S3_BUCKET_NAME']} 目录: {CONFIG['S3_DIRECTORY']}")
    upload_files_to_s3(CONFIG)
    input("\n按 Enter 退出...")
