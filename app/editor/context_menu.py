from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtCore import Qt

class ChineseContextMenu:
    """
    为编辑器和预览窗口提供中文右键菜单
    """
    @staticmethod
    def create_editor_menu(editor):
        """为编辑器创建中文右键菜单"""
        menu = QMenu(editor)
        
        # 添加撤销和重做操作
        undo_action = QAction("撤销(&U)", editor)
        undo_action.triggered.connect(editor.undo)
        undo_action.setEnabled(editor.document().isUndoAvailable())
        menu.addAction(undo_action)
        
        redo_action = QAction("重做(&R)", editor)
        redo_action.triggered.connect(editor.redo)
        redo_action.setEnabled(editor.document().isRedoAvailable())
        menu.addAction(redo_action)
        
        menu.addSeparator()
        
        # 添加剪切、复制和粘贴操作
        cut_action = QAction("剪切(&T)", editor)
        cut_action.triggered.connect(editor.cut)
        cut_action.setEnabled(editor.textCursor().hasSelection())
        menu.addAction(cut_action)
        
        copy_action = QAction("复制(&C)", editor)
        copy_action.triggered.connect(editor.copy)
        copy_action.setEnabled(editor.textCursor().hasSelection())
        menu.addAction(copy_action)
        
        paste_action = QAction("粘贴(&P)", editor)
        paste_action.triggered.connect(editor.paste)
        menu.addAction(paste_action)
        
        menu.addSeparator()
        
        # 添加全选操作
        select_all_action = QAction("全选(&A)", editor)
        select_all_action.triggered.connect(editor.selectAll)
        menu.addAction(select_all_action)
        
        return menu
    
    @staticmethod
    def create_preview_menu(preview):
        """为预览窗口创建中文右键菜单"""
        menu = QMenu(preview)
        
        # 预览窗口主要是复制和全选功能
        copy_action = QAction("复制(&C)", preview)
        copy_action.triggered.connect(preview.copy)
        copy_action.setEnabled(preview.textCursor().hasSelection())
        menu.addAction(copy_action)
        
        menu.addSeparator()
        
        select_all_action = QAction("全选(&A)", preview)
        select_all_action.triggered.connect(preview.selectAll)
        menu.addAction(select_all_action)
        
        return menu