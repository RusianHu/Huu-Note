from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QSplitter, QAction, QToolBar, QMenu, QFileDialog, 
                             QMessageBox, QDockWidget, QInputDialog, QDialog,
                             QLabel, QLineEdit, QPushButton, QFormLayout, QCheckBox)
from PyQt5.QtCore import Qt, QSize, QDir
from PyQt5.QtGui import QIcon, QKeySequence
import os

from app.editor.markdown_editor import MarkdownEditor
from app.explorer.file_explorer import FileExplorer
from app.search.search_engine import SearchDialog
from app.utils.file_operations import save_file, load_file
from app.utils.settings import Settings
from app.sync.sync_manager import SyncManager

class SyncSettingsDialog(QDialog):
    """同步设置对话框"""
    def __init__(self, sync_manager, parent=None):
        super().__init__(parent)
        self.sync_manager = sync_manager
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        self.setWindowTitle("同步设置")
        self.resize(400, 200)
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # 服务器地址
        self.server_url = QLineEdit()
        form_layout.addRow("服务器地址:", self.server_url)
        
        # API密钥
        self.api_key = QLineEdit()
        form_layout.addRow("API密钥:", self.api_key)
        
        # 启用同步
        self.enable_sync = QCheckBox("启用云端同步")
        form_layout.addRow("", self.enable_sync)
        
        layout.addLayout(form_layout)
        
        # 测试连接按钮
        self.test_button = QPushButton("测试连接")
        self.test_button.clicked.connect(self.test_connection)
        layout.addWidget(self.test_button)
        
        # 状态标签
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_settings)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
    def load_settings(self):
        """加载当前设置"""
        self.server_url.setText(self.sync_manager.get_server_url())
        self.api_key.setText(self.sync_manager.get_api_key())
        self.enable_sync.setChecked(self.sync_manager.is_sync_enabled())
        
    def save_settings(self):
        """保存设置"""
        self.sync_manager.config.set("server_url", self.server_url.text())
        self.sync_manager.set_api_key(self.api_key.text())
        self.sync_manager.enable_sync(self.enable_sync.isChecked())
        self.accept()
        
    def test_connection(self):
        """测试与服务器的连接"""
        # 临时应用当前设置
        temp_url = self.server_url.text()
        temp_key = self.api_key.text()
        
        self.sync_manager.config.set("server_url", temp_url)
        self.sync_manager.set_api_key(temp_key)
        
        # 显示正在测试
        self.status_label.setText("正在测试连接...")
        self.status_label.setStyleSheet("color: blue;")
        
        # 测试连接
        success, message = self.sync_manager.test_connection()
        
        if success:
            self.status_label.setText("连接成功！")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText(f"连接失败: {message}")
            self.status_label.setStyleSheet("color: red;")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.settings = Settings()
        self.sync_manager = SyncManager()
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_connections()
        
        # 加载编辑器布局设置
        self.load_editor_layout_setting()
        
    def setup_ui(self):
        self.setWindowTitle("老司机中文笔记")
        self.setMinimumSize(1000, 700)
        
        # 主部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 主布局
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建分隔器
        self.splitter = QSplitter(Qt.Horizontal)
        
        # 添加文件浏览器作为停靠部件
        self.file_explorer_dock = QDockWidget("笔记资源管理器", self)
        self.file_explorer_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        # 设置关闭事件处理
        self.file_explorer_dock.setFeatures(QDockWidget.DockWidgetClosable | 
                                           QDockWidget.DockWidgetMovable | 
                                           QDockWidget.DockWidgetFloatable)
        
        # 创建文件浏览器
        default_notes_path = self.settings.get("notes_directory")
        self.file_explorer = FileExplorer(default_notes_path)
        self.file_explorer_dock.setWidget(self.file_explorer)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.file_explorer_dock)
        
        # 创建Markdown编辑器
        self.editor = MarkdownEditor()
        
        # 将编辑器添加到主布局
        self.main_layout.addWidget(self.editor)
        
        # 设置状态栏
        self.statusBar().showMessage("就绪")
        
    def setup_menu(self):
        # 文件菜单
        file_menu = self.menuBar().addMenu("文件(&F)")
        
        new_action = QAction("新建(&N)", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction("打开(&O)", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("保存(&S)", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("另存为(&A)", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        import_action = QAction("导入Markdown文件(&I)", self)
        import_action.triggered.connect(self.import_markdown)
        file_menu.addAction(import_action)
        
        export_action = QAction("导出为Markdown文件(&E)", self)
        export_action.triggered.connect(self.export_markdown)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出(&Q)", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = self.menuBar().addMenu("编辑(&E)")
        
        undo_action = QAction("撤销(&U)", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.editor.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("重做(&R)", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(self.editor.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction("剪切(&T)", self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(self.editor.cut)
        edit_menu.addAction(cut_action)
        
        copy_action = QAction("复制(&C)", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.editor.copy)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("粘贴(&P)", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.editor.paste)
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        search_action = QAction("搜索(&S)", self)
        search_action.setShortcut(QKeySequence.Find)
        search_action.triggered.connect(self.show_search_dialog)
        edit_menu.addAction(search_action)
        
        # 视图菜单
        view_menu = self.menuBar().addMenu("视图(&V)")
        
        explorer_action = self.file_explorer_dock.toggleViewAction()
        explorer_action.setText("显示笔记资源管理器(&E)")
        view_menu.addAction(explorer_action)
        
        view_menu.addSeparator()
        
        # 添加布局切换菜单项
        toggle_layout_action = QAction("切换编辑器布局(&L)", self)
        toggle_layout_action.setShortcut("Ctrl+L")
        toggle_layout_action.triggered.connect(self.toggle_editor_layout)
        view_menu.addAction(toggle_layout_action)
        
        # 同步菜单 - 新增
        sync_menu = self.menuBar().addMenu("同步(&S)")
        
        sync_settings_action = QAction("同步设置(&S)", self)
        sync_settings_action.triggered.connect(self.show_sync_settings)
        sync_menu.addAction(sync_settings_action)
        
        sync_menu.addSeparator()
        
        sync_now_action = QAction("立即同步(&N)", self)
        sync_now_action.triggered.connect(self.sync_now)
        sync_menu.addAction(sync_now_action)
        
        upload_current_action = QAction("上传当前笔记(&U)", self)
        upload_current_action.triggered.connect(self.upload_current_note)
        sync_menu.addAction(upload_current_action)
        
        download_action = QAction("从云端下载笔记(&D)", self)
        download_action.triggered.connect(self.download_from_cloud)
        sync_menu.addAction(download_action)
        
        # 帮助菜单
        help_menu = self.menuBar().addMenu("帮助(&H)")
        
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        toolbar = QToolBar("主工具栏")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)
        
        # 添加工具栏按钮
        new_action = QAction("新建笔记", self)
        new_action.triggered.connect(self.new_file)
        toolbar.addAction(new_action)
        
        open_action = QAction("打开笔记", self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)
        
        save_action = QAction("保存笔记", self)
        save_action.triggered.connect(self.save_file)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # 添加布局切换按钮
        self.toggle_layout_action = QAction("切换布局", self)
        self.toggle_layout_action.setToolTip("切换编辑器和预览窗口的布局方向")
        self.toggle_layout_action.triggered.connect(self.toggle_editor_layout)
        toolbar.addAction(self.toggle_layout_action)
        
        # 接上文
        cut_action = QAction("剪切", self)
        cut_action.triggered.connect(self.editor.cut)
        toolbar.addAction(cut_action)
        
        copy_action = QAction("复制", self)
        copy_action.triggered.connect(self.editor.copy)
        toolbar.addAction(copy_action)
        
        paste_action = QAction("粘贴", self)
        paste_action.triggered.connect(self.editor.paste)
        toolbar.addAction(paste_action)
        
        toolbar.addSeparator()
        
        # Markdown格式化工具栏按钮
        bold_action = QAction("粗体", self)
        bold_action.triggered.connect(lambda: self.editor.insert_markdown_syntax("**", "**"))
        toolbar.addAction(bold_action)
        
        italic_action = QAction("斜体", self)
        italic_action.triggered.connect(lambda: self.editor.insert_markdown_syntax("*", "*"))
        toolbar.addAction(italic_action)
        
        header_action = QAction("标题", self)
        header_action.triggered.connect(lambda: self.editor.insert_markdown_syntax("# ", ""))
        toolbar.addAction(header_action)
        
        link_action = QAction("链接", self)
        link_action.triggered.connect(lambda: self.editor.insert_markdown_syntax("[", "](url)"))
        toolbar.addAction(link_action)
        
        list_action = QAction("列表", self)
        list_action.triggered.connect(lambda: self.editor.insert_markdown_syntax("- ", ""))
        toolbar.addAction(list_action)
        
        code_action = QAction("代码", self)
        code_action.triggered.connect(lambda: self.editor.insert_markdown_syntax("```\n", "\n```"))
        toolbar.addAction(code_action)
        
        toolbar.addSeparator()
        
        search_action = QAction("搜索", self)
        search_action.triggered.connect(self.show_search_dialog)
        toolbar.addAction(search_action)
        
        # 添加同步按钮
        toolbar.addSeparator()
        
        sync_action = QAction("同步", self)
        sync_action.triggered.connect(self.sync_now)
        toolbar.addAction(sync_action)
    
    def setup_connections(self):
        # 连接文件浏览器的文件打开信号
        self.file_explorer.file_selected.connect(self.load_file_from_explorer)
        # 添加对dock窗口关闭和浮动状态变化的处理
        self.file_explorer_dock.closeEvent = self.on_explorer_close
        self.file_explorer_dock.topLevelChanged.connect(self.on_explorer_floating_changed)
        
        # 连接同步管理器的信号
        self.sync_manager.sync_started.connect(self.on_sync_started)
        self.sync_manager.sync_finished.connect(self.on_sync_finished)
        self.sync_manager.sync_progress.connect(self.on_sync_progress)
        
    def on_explorer_close(self, event):
        """处理资源管理器关闭事件"""
        # 如果是浮动状态，则改为停靠而不是关闭
        if self.file_explorer_dock.isFloating():
            # 阻止默认关闭行为
            event.ignore()
            # 停靠到左侧
            self.file_explorer_dock.setFloating(False)
            self.addDockWidget(Qt.LeftDockWidgetArea, self.file_explorer_dock)
        else:
            # 如果不是浮动状态，则正常处理关闭事件
            event.accept()
            
    def on_explorer_floating_changed(self, is_floating):
        """处理资源管理器浮动状态变化"""
        # 这里可以添加额外的处理逻辑
        pass
        
    def new_file(self):
        if self.maybe_save():
            self.editor.clear()
            self.current_file = None
            self.statusBar().showMessage("新建笔记")
    
    def open_file(self):
        if self.maybe_save():
            file_path, _ = QFileDialog.getOpenFileName(
                self, "打开笔记", "", "Markdown文件 (*.md);;所有文件 (*)")
            
            if file_path:
                self.load_file(file_path)
    
    def load_file(self, file_path):
        # 检查文件扩展名
        if not file_path.lower().endswith('.md'):
            reply = QMessageBox.question(
                self, 
                "非Markdown文件", 
                f"这不是Markdown文件(.md)。\n是否使用默认方式打开？",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # 使用系统默认程序打开文件
                import subprocess
                import platform
                
                try:
                    if platform.system() == 'Windows':
                        os.startfile(file_path)
                    elif platform.system() == 'Darwin':  # macOS
                        subprocess.call(('open', file_path))
                    else:  # Linux
                        subprocess.call(('xdg-open', file_path))
                    self.statusBar().showMessage(f"已使用默认程序打开: {file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"无法打开文件: {str(e)}")
                return False
            else:
                return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                self.editor.setPlainText(content)
                self.current_file = file_path
                self.statusBar().showMessage(f"已打开: {file_path}")
                return True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开文件: {str(e)}")
            return False
            
    def load_file_from_explorer(self, file_path):
        if self.maybe_save():
            self.load_file(file_path)
    
    def save_file(self):
        if self.current_file:
            return self.save_to_file(self.current_file)
        else:
            return self.save_file_as()
    
    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存笔记", "", "Markdown文件 (*.md);;所有文件 (*)")
        
        if file_path:
            return self.save_to_file(file_path)
        return False
    
    def save_to_file(self, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(self.editor.toPlainText())
                self.current_file = file_path
                self.statusBar().showMessage(f"已保存: {file_path}")
                return True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法保存文件: {str(e)}")
            return False
    
    def maybe_save(self):
        if not self.editor.document().isModified():
            return True
            
        response = QMessageBox.question(
            self, "保存修改", 
            "笔记内容已修改，是否保存?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            
        if response == QMessageBox.Save:
            return self.save_file()
        elif response == QMessageBox.Cancel:
            return False
        return True
    
    def import_markdown(self):
        if self.maybe_save():
            file_path, _ = QFileDialog.getOpenFileName(
                self, "导入Markdown文件", "", "Markdown文件 (*.md);;所有文件 (*)")
            
            if file_path:
                default_save_path = os.path.join(
                    self.settings.get("notes_directory"), 
                    os.path.basename(file_path)
                )
                save_path, _ = QFileDialog.getSaveFileName(
                    self, "保存到笔记库", default_save_path, "Markdown文件 (*.md);;所有文件 (*)")
                
                if save_path:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as source:
                            content = source.read()
                            with open(save_path, 'w', encoding='utf-8') as target:
                                target.write(content)
                            self.load_file(save_path)
                            self.file_explorer.refresh()
                    except Exception as e:
                        QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")
    
    def export_markdown(self):
        if not self.current_file:
            QMessageBox.warning(self, "警告", "请先保存当前笔记后再导出")
            return
            
        export_path, _ = QFileDialog.getSaveFileName(
            self, "导出Markdown文件", "", "Markdown文件 (*.md);;所有文件 (*)")
            
        if export_path:
            try:
                with open(self.current_file, 'r', encoding='utf-8') as source:
                    content = source.read()
                    with open(export_path, 'w', encoding='utf-8') as target:
                        target.write(content)
                    QMessageBox.information(self, "成功", f"成功导出到: {export_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def show_search_dialog(self):
        search_dialog = SearchDialog(self.settings.get("notes_directory"), self)
        if search_dialog.exec_():
            file_path = search_dialog.get_selected_file()
            if file_path:
                self.load_file(file_path)
    
    def show_about(self):
        QMessageBox.about(
            self, 
            "关于老司机笔记", 
            "老司机笔记应用程序 v1.0\n"
            "一个简单易用的Markdown笔记应用\n"
            "支持笔记管理、Markdown编辑和全文搜索\n"
            "现已支持云端同步功能"
        )
    
    def closeEvent(self, event):
        if self.maybe_save():
            event.accept()
        else:
            event.ignore()
            
    # 以下是新增的同步相关方法
    
    def show_sync_settings(self):
        """显示同步设置对话框"""
        dialog = SyncSettingsDialog(self.sync_manager, self)
        if dialog.exec_():
            self.statusBar().showMessage("同步设置已更新")
            
    def sync_now(self):
        """立即同步笔记"""
        if not self.sync_manager.is_sync_enabled():
            QMessageBox.warning(self, "同步未启用", "请先在同步设置中启用同步功能")
            self.show_sync_settings()
            return
            
        # 保存当前笔记
        if self.current_file and self.editor.document().isModified():
            self.save_file()
            
        # 开始同步
        success, message = self.sync_manager.sync_notes()
        if success:
            # 同步成功后刷新文件浏览器
            self.file_explorer.refresh()
            
    def upload_current_note(self):
        """上传当前笔记到云端"""
        if not self.sync_manager.is_sync_enabled():
            QMessageBox.warning(self, "同步未启用", "请先在同步设置中启用同步功能")
            self.show_sync_settings()
            return
            
        if not self.current_file:
            QMessageBox.warning(self, "未打开笔记", "请先打开或保存笔记")
            return
            
        # 保存当前笔记
        if self.editor.document().isModified():
            self.save_file()
            
        # 上传笔记
        success, message, cloud_path = self.sync_manager.upload_note(self.current_file)
        if success:
            self.statusBar().showMessage(f"笔记已上传: {cloud_path}")
        else:
            QMessageBox.warning(self, "上传失败", message)
            
    def download_from_cloud(self):
        """从云端下载笔记"""
        if not self.sync_manager.is_sync_enabled():
            QMessageBox.warning(self, "同步未启用", "请先在同步设置中启用同步功能")
            self.show_sync_settings()
            return
            
        # 获取云端笔记列表
        success, message, notes = self.sync_manager.list_remote_notes()
        if not success:
            QMessageBox.warning(self, "获取云端笔记失败", message)
            return
            
        if not notes:
            QMessageBox.information(self, "云端笔记", "云端没有可下载的笔记")
            return
            
        # 创建笔记选择对话框
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout
        
        class NoteSelectDialog(QDialog):
            def __init__(self, notes, parent=None):
                super().__init__(parent)
                self.notes = notes
                self.selected_note = None
                self.setup_ui()
                
            def setup_ui(self):
                self.setWindowTitle("选择要下载的笔记")
                self.resize(500, 400)
                
                layout = QVBoxLayout(self)
                
                self.list_widget = QListWidget()
                for note in self.notes:
                    self.list_widget.addItem(note["path"])
                    
                self.list_widget.itemDoubleClicked.connect(self.accept)
                layout.addWidget(self.list_widget)
                
                button_layout = QHBoxLayout()
                
                download_button = QPushButton("下载")
                download_button.clicked.connect(self.accept)
                button_layout.addWidget(download_button)
                
                cancel_button = QPushButton("取消")
                cancel_button.clicked.connect(self.reject)
                button_layout.addWidget(cancel_button)
                
                layout.addLayout(button_layout)
                
            def get_selected_note(self):
                items = self.list_widget.selectedItems()
                if items:
                    path = items[0].text()
                    for note in self.notes:
                        if note["path"] == path:
                            return note
                return None
                
        # 显示对话框
        dialog = NoteSelectDialog(notes, self)
        if dialog.exec_():
            selected_note = dialog.get_selected_note()
            if selected_note:
                cloud_path = selected_note["path"]
                
                # 询问保存位置
                base_dir = self.settings.get("notes_directory")
                default_save_path = os.path.join(base_dir, cloud_path)
                
                save_path, _ = QFileDialog.getSaveFileName(
                    self, "保存笔记", default_save_path, "Markdown文件 (*.md);;所有文件 (*)")
                    
                if save_path:
                    # 下载笔记
                    success, message, content = self.sync_manager.download_note(cloud_path)
                    if success and content:
                        # 保存到本地
                        if save_file(content, save_path):
                            # 更新映射关系
                            self.sync_manager.config.set_file_mapping(save_path, cloud_path)
                            # 打开笔记
                            self.load_file(save_path)
                            # 刷新文件浏览器
                            self.file_explorer.refresh()
                        else:
                            QMessageBox.warning(self, "保存失败", f"无法保存文件: {save_path}")
                    else:
                        QMessageBox.warning(self, "下载失败", message)
                        
    def on_sync_started(self):
        """同步开始时的处理"""
        self.statusBar().showMessage("正在同步...")
        
    def on_sync_finished(self, success, message):
        """同步完成时的处理"""
        if success:
            self.statusBar().showMessage(message)
        else:
            self.statusBar().showMessage(f"同步失败: {message}")
            QMessageBox.warning(self, "同步失败", message)
            
    def on_sync_progress(self, message):
        """同步进度更新"""
        self.statusBar().showMessage(message)
        
    def toggle_editor_layout(self):
        """切换编辑器和预览窗口的布局方向"""
        # 调用编辑器的布局切换方法
        self.editor.toggle_layout()
        
        # 更新布局设置
        current_layout = self.editor.get_layout_orientation()
        layout_name = "horizontal" if current_layout == Qt.Horizontal else "vertical"
        self.settings.set("editor_layout", layout_name)
        
        # 更新状态栏消息
        layout_text = "左右布局" if current_layout == Qt.Horizontal else "上下布局"
        self.statusBar().showMessage(f"已切换到{layout_text}", 3000)
    
    def load_editor_layout_setting(self):
        """加载编辑器布局设置"""
        layout_setting = self.settings.get("editor_layout", "vertical")
        
        # 如果保存的设置是水平布局，则切换到水平布局
        if layout_setting == "horizontal" and self.editor.get_layout_orientation() == Qt.Vertical:
            self.editor.toggle_layout()