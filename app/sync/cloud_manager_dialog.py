from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QMessageBox, QLabel, QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal

from app.sync.cloud_explorer import CloudExplorer
from app.utils.file_operations import save_file

class CloudManagerDialog(QDialog):
    """云端文件管理对话框"""
    
    def __init__(self, sync_manager, parent=None):
        super().__init__(parent)
        self.sync_manager = sync_manager
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        self.setWindowTitle("云端笔记管理")
        self.setMinimumSize(800, 600)
        
        # 创建主布局
        layout = QVBoxLayout(self)
        
        # 添加状态标签
        self.status_label = QLabel("准备就绪")
        layout.addWidget(self.status_label)
        
        # 添加云端文件浏览器
        self.cloud_explorer = CloudExplorer(self.sync_manager)
        layout.addWidget(self.cloud_explorer)
        
        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 添加按钮布局
        btn_layout = QHBoxLayout()
        
        # 添加关闭按钮
        self.close_btn = QPushButton("关闭")
        btn_layout.addWidget(self.close_btn)
        
        # 添加按钮布局到主布局
        layout.addLayout(btn_layout)
        
    def setup_connections(self):
        # 连接按钮事件
        self.close_btn.clicked.connect(self.accept)
        
        # 连接云端文件浏览器信号
        self.cloud_explorer.download_requested.connect(self.handle_download)
        self.cloud_explorer.delete_requested.connect(self.handle_delete)
        
    def showEvent(self, event):
        """对话框显示时加载云端文件列表"""
        super().showEvent(event)
        self.cloud_explorer.load_remote_files()
        
    def handle_download(self, cloud_path, local_path):
        """处理下载请求"""
        self.status_label.setText(f"正在下载: {cloud_path}")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        
        # 下载文件
        success, message, content = self.sync_manager.download_note(cloud_path, local_path)
        
        self.progress_bar.setValue(50)
        
        if success and content:
            # 保存到本地
            if save_file(content, local_path):
                self.status_label.setText(f"下载成功: {cloud_path}")
                QMessageBox.information(self, "下载成功", f"文件已保存到: {local_path}")
            else:
                self.status_label.setText(f"保存失败: {local_path}")
                QMessageBox.warning(self, "保存失败", f"无法保存文件到: {local_path}")
        else:
            self.status_label.setText(f"下载失败: {message}")
            QMessageBox.warning(self, "下载失败", f"无法下载文件: {message}")
            
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        
    def handle_delete(self, cloud_path):
        """处理删除请求"""
        self.status_label.setText(f"正在删除: {cloud_path}")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(30)
        
        # 删除文件
        success, message = self.sync_manager.delete_note(cloud_path)
        
        self.progress_bar.setValue(70)
        
        if success:
            self.status_label.setText(f"删除成功: {cloud_path}")
            QMessageBox.information(self, "删除成功", f"已从云端删除: {cloud_path}")
            # 刷新文件列表
            self.cloud_explorer.load_remote_files()
        else:
            self.status_label.setText(f"删除失败: {message}")
            QMessageBox.warning(self, "删除失败", f"无法删除文件: {message}")
            
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)