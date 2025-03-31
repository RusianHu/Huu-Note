from PyQt5.QtWidgets import (QTreeView, QVBoxLayout, QWidget, QPushButton, 
                            QHBoxLayout, QMenu, QAction, QMessageBox, 
                            QInputDialog, QAbstractItemView, QHeaderView,
                            QLabel)
from PyQt5.QtCore import Qt, pyqtSignal, QModelIndex, QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem

import os

class CloudFileModel(QStandardItemModel):
    """云端文件模型，用于显示云端文件结构"""
    
    def __init__(self):
        super().__init__()
        self.setHorizontalHeaderLabels(["名称", "修改时间", "大小"])
        self.root_item = self.invisibleRootItem()
        
    def clear_model(self):
        """清空模型数据"""
        self.root_item.removeRows(0, self.root_item.rowCount())
        
    def add_file_item(self, file_info, parent_item=None):
        """添加文件项到模型"""
        if parent_item is None:
            parent_item = self.root_item
            
        # 创建文件项
        name_item = QStandardItem(file_info.get("filename", ""))
        
        # 设置路径数据
        name_item.setData(file_info.get("path", ""), Qt.UserRole)
        
        # 设置图标（可以根据文件类型设置不同图标）
        if file_info.get("is_dir", False):
            name_item.setIcon(QStandardItem().icon().fromTheme("folder"))
        else:
            name_item.setIcon(QStandardItem().icon().fromTheme("text-x-generic"))
        
        # 创建修改时间项
        from datetime import datetime
        last_modified = file_info.get("last_modified", 0)
        time_str = datetime.fromtimestamp(last_modified).strftime("%Y-%m-%d %H:%M:%S")
        time_item = QStandardItem(time_str)
        
        # 创建大小项
        size = file_info.get("size", 0)
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size/1024:.1f} KB"
        else:
            size_str = f"{size/(1024*1024):.1f} MB"
        size_item = QStandardItem(size_str)
        
        # 添加到模型
        row = [name_item, time_item, size_item]
        parent_item.appendRow(row)
        
        return name_item

    def build_tree_from_list(self, files_list):
        """从文件列表构建树形结构"""
        self.clear_model()
        
        # 按路径排序，确保父目录先创建
        files_list.sort(key=lambda x: x["path"])
        
        # 创建目录映射，用于快速查找父目录
        dir_mapping = {}
        
        # 首先添加所有目录
        for file_info in files_list:
            path = file_info["path"]
            parts = path.split('/')
            
            # 处理目录
            current_path = ""
            parent_item = self.root_item
            
            for i, part in enumerate(parts[:-1]):
                if not part:  # 跳过空部分
                    continue
                    
                current_path = current_path + "/" + part if current_path else part
                
                # 如果目录不存在，创建它
                if current_path not in dir_mapping:
                    dir_info = {
                        "filename": part,
                        "path": current_path,
                        "is_dir": True
                    }
                    dir_item = self.add_file_item(dir_info, parent_item)
                    dir_mapping[current_path] = dir_item
                
                parent_item = dir_mapping[current_path]
        
        # 然后添加所有文件
        for file_info in files_list:
            if file_info.get("is_dir", False):
                continue  # 跳过目录，因为已经处理过了
                
            path = file_info["path"]
            dir_path = os.path.dirname(path)
            
            # 找到父目录项
            parent_item = self.root_item
            if dir_path in dir_mapping:
                parent_item = dir_mapping[dir_path]
                
            # 添加文件项
            self.add_file_item(file_info, parent_item)


class CloudExplorer(QWidget):
    """云端文件浏览器组件"""
    
    file_selected = pyqtSignal(str)  # 文件被选中的信号
    download_requested = pyqtSignal(str, str)  # 请求下载文件的信号 (云端路径, 本地路径)
    delete_requested = pyqtSignal(str)  # 请求删除云端文件的信号 (云端路径)
    
    def __init__(self, sync_manager):
        super().__init__()
        self.sync_manager = sync_manager
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建按钮布局
        btn_layout = QHBoxLayout()
        
        # 添加刷新按钮
        self.refresh_btn = QPushButton("刷新")
        btn_layout.addWidget(self.refresh_btn)
        
        # 添加下载按钮
        self.download_btn = QPushButton("下载选中")
        btn_layout.addWidget(self.download_btn)
        
        # 添加删除按钮
        self.delete_btn = QPushButton("删除选中")
        btn_layout.addWidget(self.delete_btn)
        
        # 添加按钮布局到主布局
        layout.addLayout(btn_layout)
        
        # 添加状态标签
        self.status_label = QLabel("准备就绪")
        layout.addWidget(self.status_label)
        
        # 创建文件模型
        self.model = CloudFileModel()
        
        # 创建树视图
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # 设置列宽
        self.tree_view.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree_view.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree_view.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        # 允许右键菜单
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # 添加到布局
        layout.addWidget(self.tree_view)
        self.setLayout(layout)
        
    def setup_connections(self):
        # 连接双击事件
        self.tree_view.doubleClicked.connect(self.on_item_double_clicked)
        
        # 连接右键菜单事件
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        
        # 连接按钮事件
        self.refresh_btn.clicked.connect(self.load_remote_files)
        self.download_btn.clicked.connect(self.download_selected)
        self.delete_btn.clicked.connect(self.delete_selected)
        
    def on_item_double_clicked(self, index):
        # 获取项目数据
        name_index = index.sibling(index.row(), 0)
        path = name_index.data(Qt.UserRole)
        
        # 如果是文件，发出选中信号
        if path and not path.endswith('/'):
            self.file_selected.emit(path)
            
    def show_context_menu(self, position):
        index = self.tree_view.indexAt(position)
        
        if not index.isValid():
            return
            
        # 获取项目数据
        name_index = index.sibling(index.row(), 0)
        path = name_index.data(Qt.UserRole)
        
        if not path:
            return
            
        menu = QMenu()
        
        # 下载选项
        download_action = QAction("下载", self)
        download_action.triggered.connect(lambda: self.download_item(path))
        menu.addAction(download_action)
        
        # 删除选项
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self.delete_item(path))
        menu.addAction(delete_action)
        
        menu.exec_(self.tree_view.viewport().mapToGlobal(position))
        
    def load_remote_files(self):
        """加载远程文件列表"""
        # 更新状态标签而不是显示模态对话框
        self.status_label.setText("正在从服务器获取文件列表...")
        self.refresh_btn.setEnabled(False)
        self.tree_view.setEnabled(False)
        
        # 使用QTimer延迟执行，让UI能够更新
        QTimer.singleShot(100, self._do_load_remote_files)
        
    def _do_load_remote_files(self):
        """实际执行加载远程文件的操作"""
        try:
            # 调用同步管理器获取远程文件列表
            success, message, files = self.sync_manager.list_remote_notes()
            
            if success and files:
                # 构建文件树
                self.model.build_tree_from_list(files)
                self.tree_view.expandAll()  # 展开所有节点
                self.status_label.setText(f"已加载 {len(files)} 个文件")
            else:
                self.status_label.setText(f"加载失败: {message}")
                QMessageBox.warning(self, "加载失败", f"无法获取云端文件列表: {message}")
        except Exception as e:
            self.status_label.setText(f"加载出错: {str(e)}")
            QMessageBox.warning(self, "加载错误", f"加载文件列表时发生错误: {str(e)}")
        finally:
            # 恢复按钮和树视图状态
            self.refresh_btn.setEnabled(True)
            self.tree_view.setEnabled(True)
            
    def download_selected(self):
        """下载选中的文件"""
        indexes = self.tree_view.selectedIndexes()
        if not indexes:
            QMessageBox.information(self, "提示", "请先选择要下载的文件")
            return
            
        # 获取选中项的路径
        name_index = indexes[0].sibling(indexes[0].row(), 0)
        path = name_index.data(Qt.UserRole)
        
        if not path:
            return
            
        self.download_item(path)
        
    def download_item(self, cloud_path):
        """下载指定的云端文件"""
        # 获取本地保存路径
        from PyQt5.QtWidgets import QFileDialog
        
        # 提取文件名
        filename = os.path.basename(cloud_path)
        
        # 选择保存位置
        local_path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", filename, "Markdown文件 (*.md);;所有文件 (*)")
            
        if not local_path:
            return  # 用户取消了操作
            
        # 发出下载请求信号
        self.download_requested.emit(cloud_path, local_path)
        
    def delete_selected(self):
        """删除选中的文件或文件夹"""
        indexes = self.tree_view.selectedIndexes()
        if not indexes:
            QMessageBox.information(self, "提示", "请先选择要删除的文件或文件夹")
            return
            
        # 获取选中项的路径
        name_index = indexes[0].sibling(indexes[0].row(), 0)
        path = name_index.data(Qt.UserRole)
        
        if not path:
            return
            
        self.delete_item(path)
        
    def delete_item(self, cloud_path):
        """删除指定的云端文件或文件夹"""
        # 确认删除
        is_dir = not '.' in os.path.basename(cloud_path)
        item_type = "文件夹" if is_dir else "文件"
        
        result = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除云端{item_type} '{cloud_path}' 吗?\n此操作不可恢复!",
            QMessageBox.Yes | QMessageBox.No)
            
        if result != QMessageBox.Yes:
            return
            
        # 发出删除请求信号
        self.delete_requested.emit(cloud_path)