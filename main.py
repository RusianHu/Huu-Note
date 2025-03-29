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
        with open("resources/styles/style.qss", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except:
        print("无法加载样式表文件")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()