import sys
from PyQt5.QtWidgets import QApplication
from app.main_window import MainWindow
import os

def main():
    # 确保应用程序目录存在
    os.makedirs(os.path.expanduser("~/markdown_notes"), exist_ok=True)
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("中文笔记")
    
    # 加载样式表
    try:
        # 获取脚本所在目录的绝对路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建样式表文件的绝对路径
        style_path = os.path.join(script_dir, "resources", "styles", "style.qss")
        
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print(f"无法加载样式表文件: {e}")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()