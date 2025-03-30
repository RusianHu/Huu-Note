import os
import shutil

def save_file(content, file_path):
    """保存内容到指定文件路径"""
    try:
        # 确保目标目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return True
    except Exception as e:
        print(f"保存文件错误: {str(e)}")
        return False

def load_file(file_path):
    """从指定路径加载文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"加载文件错误: {str(e)}")
        return None

def open_in_system_explorer(self, path):
    """在系统资源管理器中打开指定路径"""
    try:
        # 针对不同操作系统使用不同的方法
        if os.name == 'nt':  # Windows系统
            # 对于文件，选中文件本身而不是打开它
            if os.path.isfile(path):
                # 使用列表形式传递命令和参数，避免路径解析问题
                subprocess.Popen(['explorer', '/select,', os.path.normpath(path)])
            else:
                os.startfile(os.path.normpath(path))
        elif os.name == 'posix':  # macOS 或 Linux
            if os.path.isdir(path):
                subprocess.Popen(['open', path])
            else:
                # 对于文件，在macOS中可以直接选中文件
                if 'darwin' in sys.platform:
                    subprocess.Popen(['open', '-R', path])  # -R 选项会在Finder中选中文件
                else:
                    # Linux系统打开文件所在目录
                    subprocess.Popen(['xdg-open', os.path.dirname(path)])
    except Exception as e:
        QMessageBox.critical(self, "错误", f"无法在系统资源管理器中打开: {str(e)}")