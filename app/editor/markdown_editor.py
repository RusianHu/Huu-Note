from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter, QTextEdit, QLabel
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
        self.timer.start(1000)  # 每1秒更新一次预览
        
    def setup_ui(self):
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建分隔器
        self.splitter = QSplitter(Qt.Vertical)
        
        # 创建编辑器
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Microsoft YaHei", 11))
        self.editor.setTabStopWidth(40)
        self.editor.setLineWrapMode(QTextEdit.WidgetWidth)
        self.editor.textChanged.connect(self.on_text_changed)
        
        # 创建预览区
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        
        # 应用Markdown语法高亮
        self.highlighter = MarkdownHighlighter(self.editor.document())
        
        # 将组件添加到分隔器
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        self.splitter.setSizes([500, 500])  # 初始大小
        
        # 将分隔器添加到布局
        layout.addWidget(self.splitter)
        
        self.setLayout(layout)
    
    def on_text_changed(self):
        # 当文本发生变化时，将在1秒后更新预览（防止频繁更新）
        self.timer.start(1000)
    
    def update_preview(self):
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
        self.preview.setHtml(html)
    
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