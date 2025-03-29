from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QSplitter, QAction, QToolBar, QMenu, QFileDialog, 
                             QMessageBox, QDockWidget)
from PyQt5.QtCore import Qt, QSize, QDir
from PyQt5.QtGui import QIcon, QKeySequence
import os

from app.editor.markdown_editor import MarkdownEditor
from app.explorer.file_explorer import FileExplorer
from app.search.search_engine import SearchDialog
from app.utils.file_operations import save_file, load_file

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_connections()
        
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
        default_notes_path = os.path.expanduser("~/markdown_notes")
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
    
    def setup_connections(self):
        # 连接文件浏览器的文件打开信号
        self.file_explorer.file_selected.connect(self.load_file_from_explorer)
        # 添加对dock窗口关闭和浮动状态变化的处理
        self.file_explorer_dock.closeEvent = self.on_explorer_close
        self.file_explorer_dock.topLevelChanged.connect(self.on_explorer_floating_changed)
        
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
                    os.path.expanduser("~/markdown_notes"), 
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
        search_dialog = SearchDialog(os.path.expanduser("~/markdown_notes"), self)
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
            "支持笔记管理、Markdown编辑和全文搜索"
        )
    
    def closeEvent(self, event):
        if self.maybe_save():
            event.accept()
        else:
            event.ignore()