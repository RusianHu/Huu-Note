from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QListWidget,
                             QLabel, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import os
import re

class SearchWorker(QThread):
    result_found = pyqtSignal(str, str, int)
    search_finished = pyqtSignal()
    progress_update = pyqtSignal(int, int)
    
    def __init__(self, root_path, keyword):
        super().__init__()
        self.root_path = root_path
        self.keyword = keyword.lower()
        self.running = True
        
    def run(self):
        self.search_files(self.root_path)
        self.search_finished.emit()
        
    def search_files(self, path):
        file_count = 0
        total_files = 0
        
        # 先计算总文件数
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith('.md'):
                    total_files += 1
        
        # 然后搜索
        for root, dirs, files in os.walk(path):
            for file in files:
                if not self.running:
                    return
                    
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    file_count += 1
                    self.progress_update.emit(file_count, total_files)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().lower()
                            if self.keyword in content:
                                # 获取匹配位置的上下文
                                context = self.get_context(content, self.keyword)
                                self.result_found.emit(file_path, context, content.count(self.keyword))
                    except Exception:
                        pass
    
    def get_context(self, content, keyword, context_chars=60):
        # 找到第一个匹配位置
        pos = content.find(keyword)
        if pos == -1:
            return ""
            
        # 计算上下文区域
        start = max(0, pos - context_chars)
        end = min(len(content), pos + len(keyword) + context_chars)
        
        # 获取上下文片段
        context = content[start:end]
        
        # 如果不是从开头开始，添加省略号
        if start > 0:
            context = "..." + context
        
        # 如果不是到结尾结束，添加省略号
        if end < len(content):
            context = context + "..."
            
        return context
        
    def stop(self):
        self.running = False

class SearchDialog(QDialog):
    def __init__(self, root_path, parent=None):
        super().__init__(parent)
        self.root_path = root_path
        self.selected_file = None
        self.search_worker = None
        self.setup_ui()
        self.setup_connections()
        self.setWindowTitle("搜索笔记")
        self.resize(600, 400)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 搜索输入区域
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("请输入搜索关键词...")
        search_layout.addWidget(self.search_input)
        
        self.search_button = QPushButton("搜索")
        search_layout.addWidget(self.search_button)
        
        layout.addLayout(search_layout)
        
        # 进度条
        self.progress_layout = QHBoxLayout()
        self.progress_label = QLabel("搜索进度:")
        self.progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_layout.addWidget(self.progress_bar)
        self.progress_bar.hide()
        self.progress_label.hide()
        
        layout.addLayout(self.progress_layout)
        
        # 搜索结果列表
        self.result_label = QLabel("搜索结果:")
        layout.addWidget(self.result_label)
        
        self.result_list = QListWidget()
        layout.addWidget(self.result_list)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.open_button = QPushButton("打开所选笔记")
        self.open_button.setEnabled(False)
        button_layout.addWidget(self.open_button)
        
        self.cancel_button = QPushButton("取消")
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
    def setup_connections(self):
        self.search_button.clicked.connect(self.start_search)
        self.search_input.returnPressed.connect(self.start_search)
        self.cancel_button.clicked.connect(self.reject)
        self.open_button.clicked.connect(self.accept)
        self.result_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.result_list.itemDoubleClicked.connect(self.accept)
        
    def start_search(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            return
            
        # 清除之前的结果
        self.result_list.clear()
        self.open_button.setEnabled(False)
        
        # 停止之前的搜索(如果有)
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.stop()
            self.search_worker.wait()
            
        # 显示进度条
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.progress_label.show()
        
        # 开始新的搜索
        self.search_worker = SearchWorker(self.root_path, keyword)
        self.search_worker.result_found.connect(self.add_result)
        self.search_worker.search_finished.connect(self.on_search_finished)
        self.search_worker.progress_update.connect(self.update_progress)
        self.search_worker.start()
        
    def add_result(self, file_path, context, count):
        # 创建项目文本，显示文件名和匹配数量
        file_name = os.path.basename(file_path)
        item_text = f"{file_name} ({count} 处匹配)\n{context}"
        
        # 将文件路径存储在项目的数据中
        item = self.result_list.addItem(item_text)
        self.result_list.item(self.result_list.count() - 1).setData(Qt.UserRole, file_path)
        
    def on_search_finished(self):
        self.progress_bar.hide()
        self.progress_label.hide()
        
        if self.result_list.count() == 0:
            self.result_list.addItem("未找到匹配结果")
        else:
            self.result_label.setText(f"搜索结果: 共找到 {self.result_list.count()} 个匹配文件")
            
    def update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        
    def on_selection_changed(self):
        selected_items = self.result_list.selectedItems()
        if selected_items:
            self.selected_file = selected_items[0].data(Qt.UserRole)
            self.open_button.setEnabled(True)
        else:
            self.selected_file = None
            self.open_button.setEnabled(False)
            
    def get_selected_file(self):
        return self.selected_file