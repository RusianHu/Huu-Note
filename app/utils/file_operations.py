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
        import os, subprocess
        
        # 规范化路径
        path = os.path.normpath(path)
        
        if os.name == 'nt':  # Windows系统
            if os.path.isfile(path):
                # 尝试最简单的方法
                try:
                    # 方法1: 使用cmd.exe执行explorer命令，确保路径有引号
                    subprocess.call(f'explorer /select,"{path}"', shell=True)
                except:
                    # 方法2: 如果失败，打开所在文件夹
                    os.startfile(os.path.dirname(path))
            else:
                # 文件夹直接打开
                os.startfile(path)
        elif os.name == 'posix':  # macOS或Linux
            if os.path.isdir(path):
                subprocess.call(['open', path])
            else:
                subprocess.call(['open', os.path.dirname(path)])
    except Exception as e:
        QMessageBox.critical(self, "错误", f"无法在系统资源管理器中打开: {str(e)}")