from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTextEdit, QLabel, QScrollBar
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QTextCursor
import markdown
from .markdown_highlighter import MarkdownHighlighter

class MarkdownEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_preview)
        self.timer.setSingleShot(True)  # 设置为单次触发模式
        # 不再自动启动定时器，只在文本变化时触发
        
        # 用于控制滚动同步的标志
        self.editor_scrolling = False
        self.preview_scrolling = False
        
    def setup_ui(self):
        # 创建主布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # 默认使用垂直布局（上下分布）
        self.current_layout = Qt.Vertical
        
        # 创建分隔器
        self.splitter = QSplitter(self.current_layout)
        
        # 创建编辑器
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Microsoft YaHei", 11))
        self.editor.setTabStopWidth(40)
        self.editor.setLineWrapMode(QTextEdit.WidgetWidth)
        self.editor.textChanged.connect(self.on_text_changed)
        
        # 创建预览区
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        
        # 连接滚动条信号
        self.editor.verticalScrollBar().valueChanged.connect(self.sync_preview_scroll)
        self.preview.verticalScrollBar().valueChanged.connect(self.sync_editor_scroll)
        
        # 应用Markdown语法高亮
        self.highlighter = MarkdownHighlighter(self.editor.document())
        
        # 将组件添加到分隔器
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        self.splitter.setSizes([500, 500])  # 初始大小
        
        # 将分隔器添加到布局
        self.layout.addWidget(self.splitter)
        
        self.setLayout(self.layout)
    
    def on_text_changed(self):
        # 当文本发生变化时，将在1秒后更新预览（防止频繁更新）
        # 只有在文本变化时才触发预览更新
        self.timer.start(1000)
    
    def update_preview(self):
        # 获取编辑器当前滚动比例，用于更新后同步预览窗口位置
        editor_scrollbar = self.editor.verticalScrollBar()
        editor_ratio = 0
        if editor_scrollbar.maximum() > 0:
            editor_ratio = editor_scrollbar.value() / editor_scrollbar.maximum()
        
        content = self.editor.toPlainText()
        html = markdown.markdown(
            content, 
            extensions=['tables', 'fenced_code', 'codehilite']
        )
        
        # 添加一些基本的CSS样式
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Microsoft YaHei', sans-serif; line-height: 1.6; }}
                h1, h2, h3, h4, h5, h6 {{ color: #333; }}
                code {{ background-color: #f5f5f5; padding: 2px 4px; border-radius: 3px; }}
                pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; }}
                blockquote {{ border-left: 4px solid #ddd; padding-left: 10px; color: #777; }}
                img {{ max-width: 100%; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """
        
        # 设置标志防止触发滚动同步
        self.preview_scrolling = True
        self.preview.setHtml(html)
        
        # 根据编辑器的滚动比例设置预览窗口的滚动位置
        preview_scrollbar = self.preview.verticalScrollBar()
        if preview_scrollbar.maximum() > 0:
            preview_scrollbar.setValue(int(editor_ratio * preview_scrollbar.maximum()))
        
        # 重置标志
        self.preview_scrolling = False
    
    def insert_markdown_syntax(self, prefix, suffix):
        cursor = self.editor.textCursor()
        selected_text = cursor.selectedText()
        
        # 如果有选中文本，在选中文本两端添加语法标记
        if selected_text:
            cursor.insertText(f"{prefix}{selected_text}{suffix}")
        else:
            # 如果没有选中文本，只插入标记并将光标置于两者之间
            cursor.insertText(prefix)
            current_position = cursor.position()
            cursor.insertText(suffix)
            cursor.setPosition(current_position)
            self.editor.setTextCursor(cursor)
    
    def clear(self):
        self.editor.clear()
        self.preview.clear()
    
    def toPlainText(self):
        return self.editor.toPlainText()
    
    def setPlainText(self, text):
        self.editor.setPlainText(text)
    
    def undo(self):
        self.editor.undo()
    
    def redo(self):
        self.editor.redo()
    
    def cut(self):
        self.editor.cut()
    
    def copy(self):
        self.editor.copy()
    
    def paste(self):
        self.editor.paste()
        
    # 添加新方法，返回内部编辑器的document对象
    def document(self):
        return self.editor.document()
    
    def sync_preview_scroll(self, value):
        # 防止循环触发
        if self.preview_scrolling:
            return
            
        self.editor_scrolling = True
        
        # 计算滚动比例
        editor_scrollbar = self.editor.verticalScrollBar()
        preview_scrollbar = self.preview.verticalScrollBar()
        
        # 如果编辑器滚动条最大值为0，则不进行同步
        if editor_scrollbar.maximum() == 0:
            self.editor_scrolling = False
            return
            
        # 计算相对位置比例
        ratio = value / editor_scrollbar.maximum()
        
        # 设置预览窗口的滚动位置
        preview_scrollbar.setValue(int(ratio * preview_scrollbar.maximum()))
        
        self.editor_scrolling = False
    
    def sync_editor_scroll(self, value):
        # 防止循环触发
        if self.editor_scrolling:
            return
            
        self.preview_scrolling = True
        
        # 计算滚动比例
        editor_scrollbar = self.editor.verticalScrollBar()
        preview_scrollbar = self.preview.verticalScrollBar()
        
        # 如果预览窗口滚动条最大值为0，则不进行同步
        if preview_scrollbar.maximum() == 0:
            self.preview_scrolling = False
            return
            
        # 计算相对位置比例
        ratio = value / preview_scrollbar.maximum()
        
        # 设置编辑器窗口的滚动位置
        editor_scrollbar.setValue(int(ratio * editor_scrollbar.maximum()))
        
        self.preview_scrolling = False
        
    def toggle_layout(self):
        """切换编辑器和预览窗口的布局方向"""
        # 保存当前分隔器的大小比例
        sizes = self.splitter.sizes()
        total_size = sum(sizes)
        ratio = [size / total_size for size in sizes]
        
        # 切换布局方向
        if self.current_layout == Qt.Vertical:
            self.current_layout = Qt.Horizontal
        else:
            self.current_layout = Qt.Vertical
        
        # 记录当前内容和滚动位置
        content = self.editor.toPlainText()
        editor_scroll_value = self.editor.verticalScrollBar().value()
        preview_scroll_value = self.preview.verticalScrollBar().value()
        
        # 移除旧的分隔器
        old_splitter = self.splitter
        self.layout.removeWidget(old_splitter)
        
        # 创建新的分隔器
        self.splitter = QSplitter(self.current_layout)
        
        # 重新创建编辑器和预览区
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Microsoft YaHei", 11))
        self.editor.setTabStopWidth(40)
        self.editor.setLineWrapMode(QTextEdit.WidgetWidth)
        self.editor.textChanged.connect(self.on_text_changed)
        self.editor.setPlainText(content)
        
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        
        # 重新连接滚动条信号
        self.editor.verticalScrollBar().valueChanged.connect(self.sync_preview_scroll)
        self.preview.verticalScrollBar().valueChanged.connect(self.sync_editor_scroll)
        
        # 重新应用Markdown语法高亮
        self.highlighter = MarkdownHighlighter(self.editor.document())
        
        # 将组件添加到分隔器
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        
        # 将分隔器添加到布局
        self.layout.addWidget(self.splitter)
        
        # 恢复分隔器的大小比例
        new_sizes = [int(r * total_size) for r in ratio]
        self.splitter.setSizes(new_sizes)
        
        # 立即更新预览
        self.update_preview()
        
        # 恢复滚动位置
        QTimer.singleShot(100, lambda: self.editor.verticalScrollBar().setValue(editor_scroll_value))
        QTimer.singleShot(100, lambda: self.preview.verticalScrollBar().setValue(preview_scroll_value))
        
        # 销毁旧的分隔器
        old_splitter.deleteLater()
        
    def get_layout_orientation(self):
        """获取当前布局方向"""
        return self.current_layout