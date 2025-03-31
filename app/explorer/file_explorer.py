from PyQt5.QtWidgets import (QTreeView, QFileSystemModel, 
                             QMenu, QAction, QMessageBox, QInputDialog, 
                             QVBoxLayout, QWidget, QPushButton, QHBoxLayout)
from PyQt5.QtCore import Qt, QDir, pyqtSignal, QModelIndex
import os
import shutil
import subprocess  # 用于跨平台打开文件资源管理器

class FileExplorer(QWidget):
    file_selected = pyqtSignal(str)
    
    def __init__(self, root_path):
        super().__init__()
        self.root_path = root_path
        self.sync_manager = None  # 初始化为None，稍后由MainWindow设置
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建按钮布局
        btn_layout = QHBoxLayout()
        
        # 添加新建文件夹按钮
        self.new_folder_btn = QPushButton("新建文件夹")
        btn_layout.addWidget(self.new_folder_btn)
        
        # 添加新建文件按钮
        self.new_file_btn = QPushButton("新建笔记")
        btn_layout.addWidget(self.new_file_btn)
        
        # 添加刷新按钮
        self.refresh_btn = QPushButton("刷新")
        btn_layout.addWidget(self.refresh_btn)
        
        # 添加按钮布局到主布局
        layout.addLayout(btn_layout)
        
        # 创建第二行按钮布局 - 新增
        expand_layout = QHBoxLayout()
        
        # 添加展开所有目录按钮 - 新增
        self.expand_all_btn = QPushButton("展开所有")
        expand_layout.addWidget(self.expand_all_btn)
        
        # 添加折叠所有目录按钮 - 新增
        self.collapse_all_btn = QPushButton("折叠所有")
        expand_layout.addWidget(self.collapse_all_btn)
        
        # 添加第二行按钮布局到主布局 - 新增
        layout.addLayout(expand_layout)
        
        # 创建文件系统模型
        self.model = QFileSystemModel()
        self.model.setRootPath(self.root_path)
        
        # 创建树视图
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(self.root_path))
        
        # 只显示名称列
        self.tree_view.setHeaderHidden(True)
        for i in range(1, self.model.columnCount()):
            self.tree_view.hideColumn(i)
        
        # 设置默认列宽
        self.tree_view.setColumnWidth(0, 250)
        
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
        self.new_folder_btn.clicked.connect(lambda: self.create_folder())
        self.new_file_btn.clicked.connect(lambda: self.create_file())
        self.refresh_btn.clicked.connect(self.refresh)
        
        # 连接展开和折叠按钮事件 - 新增
        self.expand_all_btn.clicked.connect(self.expand_all_directories)
        self.collapse_all_btn.clicked.connect(self.collapse_all_directories)
    
    # 新增方法：展开所有目录
    def expand_all_directories(self):
        """展开所有目录"""
        self.tree_view.expandAll()
        self.statusBar().showMessage("已展开所有目录", 3000)
    
    # 新增方法：折叠所有目录
    def collapse_all_directories(self):
        """折叠所有目录"""
        self.tree_view.collapseAll()
        self.statusBar().showMessage("已折叠所有目录", 3000)
    
    def on_item_double_clicked(self, index):
        path = self.model.filePath(index)
        if os.path.isfile(path) and path.endswith('.md'):
            self.file_selected.emit(path)
    
    def show_context_menu(self, position):
        index = self.tree_view.indexAt(position)
        
        if not index.isValid():
            return
            
        path = self.model.filePath(index)
        is_file = os.path.isfile(path)
        
        # 检查是否启用了云端同步
        sync_enabled = self.sync_manager and self.sync_manager.is_sync_enabled()
        
        menu = QMenu()
        
        # 导入笔记选项
        import_action = QAction("导入笔记", self)
        import_action.triggered.connect(lambda: self.import_note(path if not is_file else os.path.dirname(path)))
        menu.addAction(import_action)
        
        # 添加通用动作
        open_action = QAction("打开", self)
        open_action.triggered.connect(lambda: self.on_item_double_clicked(index))
        menu.addAction(open_action)
        
        # 添加"在系统资源管理器中打开"选项
        open_in_explorer_action = QAction("在系统资源管理器中打开", self)
        open_in_explorer_action.triggered.connect(lambda: self.open_in_system_explorer(path))
        menu.addAction(open_in_explorer_action)
        
        rename_action = QAction("重命名", self)
        rename_action.triggered.connect(lambda: self.rename_item(index))
        menu.addAction(rename_action)
        
        # 如果启用了云端同步，添加"同时重命名云端"选项
        if sync_enabled:
            rename_cloud_action = QAction("同时重命名云端", self)
            rename_cloud_action.triggered.connect(lambda: self.rename_item_with_cloud(index))
            menu.addAction(rename_cloud_action)
        
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self.delete_item(index))
        menu.addAction(delete_action)
        
        # 如果启用了云端同步，添加"同时删除云端"选项
        if sync_enabled:
            delete_cloud_action = QAction("同时删除云端", self)
            delete_cloud_action.triggered.connect(lambda: self.delete_item_with_cloud(index))
            menu.addAction(delete_cloud_action)
        
        # 文件夹特有选项
        if not is_file:
            create_folder_action = QAction("新建文件夹", self)
            create_folder_action.triggered.connect(
                lambda: self.create_folder(parent_path=path))
            menu.addAction(create_folder_action)
            
            create_file_action = QAction("新建笔记", self)
            create_file_action.triggered.connect(
                lambda: self.create_file(parent_path=path))
            menu.addAction(create_file_action)
            
            # 添加展开/折叠选项 - 新增
            expand_action = QAction("展开", self)
            expand_action.triggered.connect(lambda: self.tree_view.expand(index))
            menu.addAction(expand_action)
            
            collapse_action = QAction("折叠", self)
            collapse_action.triggered.connect(lambda: self.tree_view.collapse(index))
            menu.addAction(collapse_action)
        
        menu.exec_(self.tree_view.viewport().mapToGlobal(position))

    # 用于在系统资源管理器中打开文件或文件夹
    def open_in_system_explorer(self, path):
        """在系统资源管理器中打开指定路径"""
        try:
            # 针对不同操作系统使用不同的方法
            if os.name == 'nt':  # Windows系统
                # 规范化路径
                path = os.path.normpath(path)
                if os.path.isfile(path):
                    # 使用subprocess.call确保命令执行
                    subprocess.call(f'explorer /select,"{path}"', shell=True)
                else:
                    os.startfile(path)
            elif os.name == 'posix':  # macOS 或 Linux
                if os.path.isdir(path):
                    subprocess.Popen(['open', path])
                else:
                    # 对于文件，打开其所在的目录
                    subprocess.Popen(['open', os.path.dirname(path)])
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法在系统资源管理器中打开: {str(e)}")
    
    def rename_item(self, index):
        old_path = self.model.filePath(index)
        old_name = os.path.basename(old_path)
        
        new_name, ok = QInputDialog.getText(
            self, "重命名", "请输入新名称:", text=old_name)
            
        if ok and new_name:
            if os.path.isfile(old_path) and not new_name.endswith('.md'):
                new_name += '.md'
                
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            
            try:
                os.rename(old_path, new_path)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重命名失败: {str(e)}")
    
    def rename_item_with_cloud(self, index):
        """重命名文件并同步到云端"""
        if not self.sync_manager or not self.sync_manager.is_sync_enabled():
            QMessageBox.warning(self, "同步未启用", "云端同步功能未启用，无法同步重命名。")
            return
            
        old_path = self.model.filePath(index)
        old_name = os.path.basename(old_path)
        
        new_name, ok = QInputDialog.getText(
            self, "重命名（云端同步）", "请输入新名称:", text=old_name)
            
        if ok and new_name:
            if os.path.isfile(old_path) and not new_name.endswith('.md'):
                new_name += '.md'
                
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            
            try:
                # 获取云端路径
                old_cloud_path = self.sync_manager.config.get_file_mapping(old_path)
                
                if not old_cloud_path:
                    # 尝试规范化路径后再次查找
                    norm_path = os.path.normpath(old_path)
                    old_cloud_path = self.sync_manager.config.get_file_mapping(norm_path)
                    
                    if not old_cloud_path:
                        QMessageBox.warning(self, "未找到云端映射", 
                                          f"未找到文件 {old_name} 的云端映射，将只进行本地重命名。\n路径: {old_path}")
                        os.rename(old_path, new_path)
                        self.refresh()
                        return
                
                # 计算新的云端路径
                new_cloud_path = os.path.join(os.path.dirname(old_cloud_path), new_name)
                
                # 先在本地重命名
                os.rename(old_path, new_path)
                
                # 更新映射关系
                self.sync_manager.config.remove_file_mapping(old_path)
                self.sync_manager.config.set_file_mapping(new_path, new_cloud_path)
                
                # 如果是文件，上传新内容
                if os.path.isfile(new_path):
                    with open(new_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    success, message, _ = self.sync_manager.upload_note(new_path, content)
                    
                    # 删除旧文件
                    self.sync_manager.delete_note(old_cloud_path)
                    
                    if not success:
                        QMessageBox.warning(self, "云端同步失败", 
                                          f"文件已在本地重命名，但云端同步失败: {message}")
                else:
                    # 对于文件夹，需要更新所有子文件的映射
                    # 这里简化处理，只提示用户需要手动同步
                    QMessageBox.information(self, "文件夹重命名", 
                                         "文件夹已在本地重命名，请使用同步功能更新云端文件夹结构。")
                
                self.refresh()
                self.statusBar().showMessage(f"已重命名 {old_name} 为 {new_name}（本地和云端）", 3000)
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重命名失败: {str(e)}")

    
    def delete_item(self, index):
        path = self.model.filePath(index)
        name = os.path.basename(path)
        
        result = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除 '{name}' 吗?",
            QMessageBox.Yes | QMessageBox.No)
            
        if result == QMessageBox.Yes:
            try:
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")
    
    def delete_item_with_cloud(self, index):
        """删除文件并同步到云端"""
        if not self.sync_manager or not self.sync_manager.is_sync_enabled():
            QMessageBox.warning(self, "同步未启用", "云端同步功能未启用，无法同步删除。")
            return
            
        path = self.model.filePath(index)
        name = os.path.basename(path)
        
        result = QMessageBox.question(
            self, "确认删除（云端同步）", 
            f"确定要删除 '{name}' 吗？此操作将同时删除本地和云端文件。",
            QMessageBox.Yes | QMessageBox.No)
            
        if result == QMessageBox.Yes:
            try:
                # 获取云端路径
                cloud_path = self.sync_manager.config.get_file_mapping(path)
                
                if not cloud_path:
                    # 尝试规范化路径后再次查找
                    norm_path = os.path.normpath(path)
                    cloud_path = self.sync_manager.config.get_file_mapping(norm_path)
                    
                    if not cloud_path:
                        # 输出更详细的调试信息
                        QMessageBox.warning(self, "未找到云端映射", 
                                          f"未找到文件 {name} 的云端映射，将只进行本地删除。\n路径: {path}")
                        if os.path.isfile(path):
                            os.remove(path)
                        else:
                            shutil.rmtree(path)
                        self.refresh()
                        return
                
                # 先删除本地文件
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
                
                # 删除云端文件
                success, message = self.sync_manager.delete_note(cloud_path)
                
                if not success:
                    QMessageBox.warning(self, "云端删除失败", 
                                      f"文件已在本地删除，但云端删除失败: {message}")
                else:
                    self.statusBar().showMessage(f"已删除 {name}（本地和云端）", 3000)
                
                self.refresh()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")
    
    def create_folder(self, parent_path=None):
        if parent_path is None:
            parent_path = self.root_path
        
        # 添加类型检查，明确报告错误类型
        if isinstance(parent_path, bool):
            QMessageBox.critical(self, "错误", f"无效的路径类型：<class 'bool'>")
            return
        
        # 确保路径是字符串
        try:
            if not isinstance(parent_path, str):
                parent_path = str(parent_path)
        except:
            QMessageBox.critical(self, "错误", "路径转换失败")
            return
                
        folder_name, ok = QInputDialog.getText(
            self, "新建文件夹", "请输入文件夹名称:")
                
        if ok and folder_name:
            try:
                os.makedirs(os.path.join(parent_path, folder_name), exist_ok=True)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建文件夹失败: {str(e)}")
    
    def create_file(self, parent_path=None):
        if parent_path is None:
            parent_path = self.root_path
            
        file_name, ok = QInputDialog.getText(
            self, "新建笔记", "请输入笔记名称:")
            
        if ok and file_name:
            if not file_name.endswith('.md'):
                file_name += '.md'
                
            try:
                with open(os.path.join(parent_path, file_name), 'w', encoding='utf-8') as f:
                    f.write("# " + file_name.replace('.md', '') + "\n\n")
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建笔记失败: {str(e)}")
    
    def refresh(self):
        self.model.setRootPath(self.root_path)
        self.tree_view.setRootIndex(self.model.index(self.root_path))
        
    def import_note(self, target_dir):
        """导入笔记文件到指定目录"""
        from PyQt5.QtWidgets import QFileDialog
        
        # 设置文件过滤器，支持多种文本格式
        file_filter = "文本文件 (*.md *.txt);;所有文件 (*)"
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择要导入的笔记", "", file_filter)
            
        if not file_paths:
            return
            
        for src_path in file_paths:
            # 验证文件格式
            if not src_path.lower().endswith(('.md', '.txt')):
                QMessageBox.warning(self, "格式不支持", 
                                  f"不支持导入 {os.path.basename(src_path)}: 仅支持.md和.txt文件")
                continue
                
            # 构建目标路径
            filename = os.path.basename(src_path)
            if filename.lower().endswith('.txt'):
                # 如果是.txt文件，转换为.md
                dst_path = os.path.join(target_dir, filename[:-4] + '.md')
                try:
                    # 读取.txt内容并写入.md文件
                    with open(src_path, 'r', encoding='utf-8') as src_file:
                        content = src_file.read()
                    with open(dst_path, 'w', encoding='utf-8') as dst_file:
                        dst_file.write(content)
                    QMessageBox.information(self, "导入成功", 
                                          f"已成功将 {filename} 转换为.md格式")
                except Exception as e:
                    QMessageBox.warning(self, "导入失败", 
                                      f"转换 {filename} 失败: {str(e)}")
            else:
                # 其他文件直接复制
                dst_path = os.path.join(target_dir, filename)
                from app.utils.file_operations import copy_file
                if copy_file(src_path, dst_path):
                    QMessageBox.information(self, "导入成功", 
                                          f"已成功导入 {filename}")
                else:
                    QMessageBox.warning(self, "导入失败", 
                                      f"导入 {filename} 失败")
        
        # 刷新文件列表
        self.refresh()
        
    # 获取状态栏方法 - 新增
    def statusBar(self):
        """获取主窗口的状态栏"""
        # 查找父窗口中的状态栏
        parent = self.parent()
        while parent:
            if hasattr(parent, 'statusBar') and callable(parent.statusBar):
                return parent.statusBar()
            parent = parent.parent()
        
        # 如果找不到状态栏，则返回一个模拟对象
        class DummyStatusBar:
            def showMessage(self, message, timeout=0):
                pass
        
        return DummyStatusBar()