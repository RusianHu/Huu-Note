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

def copy_file(source_path, target_path):
    """复制文件从源路径到目标路径"""
    try:
        # 确保目标目录存在
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # 复制文件
        shutil.copy2(source_path, target_path)
        return True
    except Exception as e:
        print(f"复制文件错误: {str(e)}")
        return False