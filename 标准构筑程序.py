import os
import subprocess
import sys

def build_standard():
    try:
        # 执行pyinstaller标准构建命令
        cmd = ['pyinstaller', 'huu_note.spec']
        result = subprocess.run(cmd, check=True)
        
        print("\n构建成功！标准版HuuNote已生成在dist目录")
        print("按任意键退出...")
        input()
        
    except subprocess.CalledProcessError as e:
        print(f"\n构建失败: {e}")
        print("按任意键退出...")
        input()
        sys.exit(1)

if __name__ == '__main__':
    print("正在构建HuuNote标准版...")
    build_standard()
