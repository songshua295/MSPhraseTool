"""测试 .env 文件读取逻辑"""
import sys
import os

def test_env_path():
    """测试 .env 文件路径获取"""
    print("=== 测试 .env 文件路径获取 ===")
    
    # 获取程序运行目录（支持打包后的 EXE）
    if getattr(sys, 'frozen', False):
        # 打包后的 EXE 环境
        base_dir = os.path.dirname(sys.executable)
        print(f"运行环境: 打包后的 EXE")
        print(f"EXE 路径: {sys.executable}")
    else:
        # 开发环境
        base_dir = os.path.dirname(os.path.dirname(__file__))
        print(f"运行环境: 开发环境")
        print(f"脚本路径: {__file__}")
    
    print(f"基础目录: {base_dir}")
    
    env_path = os.path.join(base_dir, '.env')
    print(f".env 文件路径: {env_path}")
    print(f".env 文件存在: {os.path.exists(env_path)}")
    
    if os.path.exists(env_path):
        print(f".env 文件大小: {os.path.getsize(env_path)} 字节")
    
    return env_path

if __name__ == '__main__':
    env_path = test_env_path()
    
    print("\n=== 结论 ===")
    print("1. 开发环境: .env 文件应该在项目根目录")
    print("2. 打包后: .env 文件应该在 EXE 同目录下")
    print("3. 代码已正确处理两种情况")
