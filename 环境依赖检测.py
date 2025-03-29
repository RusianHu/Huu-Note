import subprocess
import sys
from typing import List

def get_requirements() -> List[str]:
    """读取requirements.txt文件获取依赖列表"""
    try:
        with open('requirements.txt', 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("错误：未找到requirements.txt文件")
        sys.exit(1)

def is_package_installed(package: str) -> bool:
    """检查指定包是否已安装"""
    try:
        # 获取包名（去除版本号）
        pkg_name = package.split('==')[0].split('>')[0].split('<')[0]
        subprocess.run(
            [sys.executable, '-m', 'pip', 'show', pkg_name],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return True
    except subprocess.CalledProcessError:
        return False

def install_package(package: str):
    """安装指定的包"""
    print(f"正在安装: {package}")
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', package],
            check=True
        )
        print(f"成功安装: {package}")
    except subprocess.CalledProcessError as e:
        print(f"安装失败: {package}, 错误: {e}")

def main():
    print("开始检查环境依赖...")
    requirements = get_requirements()
    
    for req in requirements:
        if not is_package_installed(req):
            install_package(req)
        else:
            print(f"已安装: {req}")
    
    print("依赖检查完成")

if __name__ == "__main__":
    main()
