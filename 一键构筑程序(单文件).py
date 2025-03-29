import os
import subprocess
import sys

def build_single_file():
    try:
        # 执行pyinstaller单文件打包命令
        cmd = [
            'pyinstaller',
            '--name', 'HuuNote',
            '--windowed',
            '--onefile',
            'main.py'
        ]
        result = subprocess.run(cmd, check=True)
        
        print("\n构建成功！单文件版HuuNote已生成在dist目录")
        print("按任意键退出...")
        input()
        
    except subprocess.CalledProcessError as e:
        print(f"\n构建失败: {e}")
        print("按任意键退出...")
        input()
        sys.exit(1)

if __name__ == '__main__':
    print("正在构建HuuNote单文件版...")
    build_single_file()
