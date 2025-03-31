from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTextEdit, QLabel, QScrollBar, QCheckBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QTextCursor
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
import markdown
import re
from .markdown_highlighter import MarkdownHighlighter
from .context_menu import ChineseContextMenu

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
        
        # HTML 支持标志
        self.html_enabled = False
        
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
        # 设置编辑器的自定义右键菜单
        self.editor.setContextMenuPolicy(Qt.CustomContextMenu)
        self.editor.customContextMenuRequested.connect(self.show_editor_context_menu)
        
        # 创建预览区 - 使用QWebEngineView替代QTextEdit
        self.preview = QWebEngineView()
        # 设置预览区的自定义右键菜单
        self.preview.setContextMenuPolicy(Qt.CustomContextMenu)
        self.preview.customContextMenuRequested.connect(self.show_preview_context_menu)
        
        # 配置WebEngine页面设置
        self.preview_page = QWebEnginePage(self.preview)
        self.preview.setPage(self.preview_page)
        
        # 连接滚动条信号
        self.editor.verticalScrollBar().valueChanged.connect(self.sync_preview_scroll)
        
        # WebEngine页面不直接提供滚动事件，我们使用定时器定期检查
        self.scroll_check_timer = QTimer()
        self.scroll_check_timer.timeout.connect(self.check_preview_scroll_position)
        self.scroll_check_timer.setInterval(500)  # 每500毫秒检查一次
        self.scroll_check_timer.start()
        
        # 应用Markdown语法高亮
        self.highlighter = MarkdownHighlighter(self.editor.document())
        
        # 将组件添加到分隔器
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        self.splitter.setSizes([500, 500])  # 初始大小
        
        # 添加HTML支持选项
        self.html_checkbox = QCheckBox("启用HTML支持")
        self.html_checkbox.setToolTip("启用后可以在Markdown中嵌入HTML代码（不执行JavaScript）")
        self.html_checkbox.stateChanged.connect(self.toggle_html_support)
        
        # 将分隔器和HTML选项添加到布局
        self.layout.addWidget(self.splitter)
        self.layout.addWidget(self.html_checkbox)
        
        self.setLayout(self.layout)
    
    def on_text_changed(self):
        # 当文本发生变化时，将在1秒后更新预览（防止频繁更新）
        # 只有在文本变化时才触发预览更新
        self.timer.start(1000)
    
    def update_preview(self):
        # 记录编辑器当前滚动比例，用于更新后同步预览窗口位置
        editor_scrollbar = self.editor.verticalScrollBar()
        editor_ratio = 0
        if editor_scrollbar.maximum() > 0:
            editor_ratio = editor_scrollbar.value() / editor_scrollbar.maximum()
        
        content = self.editor.toPlainText()
        
        # 根据HTML支持选项决定处理方式
        if self.html_enabled:
            # 启用HTML支持时，直接使用HTML内容
            # 首先尝试使用markdown解析
            try:
                # 使用markdown解析非HTML部分
                html = markdown.markdown(
                    content, 
                    extensions=['tables', 'fenced_code', 'codehilite', 'md_in_html']
                )
                
                # 安全过滤：只移除JavaScript相关内容，保留其他HTML标签
                html = self.sanitize_html(html)
            except Exception as e:
                # 如果解析失败，直接使用原始内容
                html = f"<pre>{content}</pre>"
                print(f"Markdown解析错误: {str(e)}")
        else:
            # 禁用HTML支持时，将HTML标签转义
            html = markdown.markdown(
                content, 
                extensions=['tables', 'fenced_code', 'codehilite']
            )
        
        # 添加一些基本的CSS样式
        html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: 'Microsoft YaHei', sans-serif; line-height: 1.6; padding: 20px; }}
                h1, h2, h3, h4, h5, h6 {{ color: #333; }}
                code {{ background-color: #f5f5f5; padding: 2px 4px; border-radius: 3px; }}
                pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                blockquote {{ border-left: 4px solid #ddd; padding-left: 10px; color: #777; }}
                img {{ max-width: 100%; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                svg {{ max-width: 100%; height: auto; display: block; }}
            </style>
        </head>
        <body>
            {html}
            <div id="end-marker" style="height: 10px;"></div>
        </body>
        </html>
        """
        
        # 设置标志防止触发滚动同步
        self.preview_scrolling = True
        
        # 使用QWebEngineView加载HTML内容
        self.preview.setHtml(html)
        
        # 设置滚动位置 - 使用JS处理
        if editor_ratio > 0:
            script = f"document.addEventListener('DOMContentLoaded', function() {{ window.scrollTo(0, document.body.scrollHeight * {editor_ratio}); }});"
            self.preview.page().runJavaScript(script)
        
        # 重置标志
        self.preview_scrolling = False
    
    def sanitize_html(self, html):
        """
        安全过滤HTML内容，只移除JavaScript相关内容，保留其他HTML标签
        特别注意保留SVG标签和属性
        """
        # 移除所有script标签
        html = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', html)
        
        # 移除所有on*事件属性
        html = re.sub(r' on\w+="[^"]*"', '', html)
        html = re.sub(r" on\w+='[^']*'", '', html)
        html = re.sub(r' on\w+=\w+', '', html)
        
        # 移除iframe标签
        html = re.sub(r'<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>', '', html)
        
        # 移除object标签
        html = re.sub(r'<object\b[^<]*(?:(?!<\/object>)<[^<]*)*<\/object>', '', html)
        
        # 移除embed标签
        html = re.sub(r'<embed\b[^<]*(?:(?!<\/embed>)<[^<]*)*<\/embed>', '', html)
        
        # 移除javascript:协议
        html = re.sub(r'javascript:', 'disabled-javascript:', html)
        
        return html
    
    def direct_html_preview(self, content):
        """
        直接预览HTML内容，用于处理复杂的HTML内容如SVG
        """
        # 提取HTML块
        html_blocks = []
        in_html_block = False
        current_block = []
        
        for line in content.split('\n'):
            if line.strip().startswith('<') and not in_html_block:
                in_html_block = True
                current_block = [line]
            elif in_html_block:
                current_block.append(line)
                if line.strip().startswith('</'):
                    html_blocks.append('\n'.join(current_block))
                    in_html_block = False
            
        return '\n'.join(html_blocks)
    
    def toggle_html_support(self, state):
        """切换HTML支持"""
        self.html_enabled = (state == Qt.Checked)
        self.update_preview()
    
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
    
    def insert_html_template(self, template_type):
        """插入HTML模板"""
        templates = {
            "div": "<div>\n    内容\n</div>",
            "table": "<table>\n    <tr>\n        <th>表头1</th>\n        <th>表头2</th>\n    </tr>\n    <tr>\n        <td>数据1</td>\n        <td>数据2</td>\n    </tr>\n</table>",
            "style": "<style>\n    .custom-class {\n        color: blue;\n        font-weight: bold;\n    }\n</style>",
            "details": "<details>\n    <summary>点击展开</summary>\n    <p>这里是详细内容</p>\n</details>",
            "svg": """<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
    <!-- SVG内容 -->
    <circle cx="100" cy="100" r="50" fill="#3498db" />
    <text x="100" y="110" font-family="Arial" font-size="16" text-anchor="middle" fill="white">SVG示例</text>
</svg>"""
        }
        
        if template_type in templates:
            cursor = self.editor.textCursor()
            cursor.insertText(templates[template_type])
            self.editor.setFocus()
    
    def clear(self):
        self.editor.clear()
        self.preview.setHtml("")
    
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
    
    # 添加显示自定义右键菜单的方法
    def show_editor_context_menu(self, position):
        """显示编辑器的中文右键菜单"""
        menu = ChineseContextMenu.create_editor_menu(self.editor)
        
        # 如果启用了HTML支持，添加HTML模板菜单
        if self.html_enabled:
            html_menu = menu.addMenu("插入HTML模板")
            
            div_action = html_menu.addAction("DIV容器")
            div_action.triggered.connect(lambda: self.insert_html_template("div"))
            
            table_action = html_menu.addAction("表格")
            table_action.triggered.connect(lambda: self.insert_html_template("table"))
            
            style_action = html_menu.addAction("样式")
            style_action.triggered.connect(lambda: self.insert_html_template("style"))
            
            details_action = html_menu.addAction("折叠块")
            details_action.triggered.connect(lambda: self.insert_html_template("details"))
            
            svg_action = html_menu.addAction("SVG图形")
            svg_action.triggered.connect(lambda: self.insert_html_template("svg"))
        
        menu.exec_(self.editor.mapToGlobal(position))
        
    def show_preview_context_menu(self, position):
        """显示预览窗口的中文右键菜单"""
        from PyQt5.QtWidgets import QMenu, QAction
        
        # 为QWebEngineView创建自定义右键菜单
        menu = QMenu(self.preview)
        
        # 添加复制操作
        copy_action = QAction("复制(&C)", self.preview)
        copy_action.triggered.connect(self.copy_from_preview)
        menu.addAction(copy_action)
        
        # 添加全选操作
        select_all_action = QAction("全选(&A)", self.preview)
        select_all_action.triggered.connect(self.select_all_preview)
        menu.addAction(select_all_action)
        
        # 执行菜单
        menu.exec_(self.preview.mapToGlobal(position))
    
    def copy_from_preview(self):
        """从预览窗口复制所选内容"""
        self.preview.page().triggerAction(QWebEnginePage.Copy)
    
    def select_all_preview(self):
        """选择预览窗口中的所有内容"""
        self.preview.page().triggerAction(QWebEnginePage.SelectAll)
    
    def sync_preview_scroll(self, value):
        """同步编辑器滚动到预览窗口"""
        # 防止循环触发
        if self.preview_scrolling:
            return
            
        self.editor_scrolling = True
        
        # 计算滚动比例
        editor_scrollbar = self.editor.verticalScrollBar()
        
        # 如果编辑器滚动条最大值为0，则不进行同步
        if editor_scrollbar.maximum() == 0:
            self.editor_scrolling = False
            return
            
        # 计算相对位置比例
        ratio = value / editor_scrollbar.maximum()
        
        # 使用JavaScript设置预览窗口的滚动位置
        js = f"window.scrollTo(0, document.body.scrollHeight * {ratio});"
        self.preview.page().runJavaScript(js)
        
        self.editor_scrolling = False
    
    def check_preview_scroll_position(self):
        """检查预览窗口滚动位置并同步到编辑器"""
        # 如果编辑器正在滚动或预览窗口没有焦点，则不执行同步
        if self.editor_scrolling or not self.preview.hasFocus():
            return
            
        # 获取预览窗口滚动位置和高度
        js = """
        (function() {
            var scrollTop = window.scrollY || document.documentElement.scrollTop;
            var scrollHeight = Math.max(
                document.body.scrollHeight,
                document.documentElement.scrollHeight
            ) - window.innerHeight;
            return { scrollTop: scrollTop, scrollHeight: scrollHeight };
        })();
        """
        self.preview.page().runJavaScript(js, self.handle_preview_scroll_position)
    
    def handle_preview_scroll_position(self, result):
        """处理从预览窗口获取的滚动位置信息"""
        # 设置标志防止循环触发
        self.preview_scrolling = True
        
        try:
            if isinstance(result, dict) and 'scrollTop' in result and 'scrollHeight' in result:
                scrollTop = result['scrollTop']
                scrollHeight = result['scrollHeight']
                
                # 如果内容高度足够滚动
                if scrollHeight > 0:
                    ratio = scrollTop / scrollHeight
                    editor_scrollbar = self.editor.verticalScrollBar()
                    
                    # 应用滚动比例到编辑器
                    editor_scrollbar.setValue(int(ratio * editor_scrollbar.maximum()))
        except Exception as e:
            print(f"同步滚动错误: {e}")
        
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
        html_enabled = self.html_enabled
        
        # 移除旧的分隔器
        old_splitter = self.splitter
        self.layout.removeWidget(old_splitter)
        
        # 创建新的分隔器
        self.splitter = QSplitter(self.current_layout)
        
        # 重新创建编辑器
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Microsoft YaHei", 11))
        self.editor.setTabStopWidth(40)
        self.editor.setLineWrapMode(QTextEdit.WidgetWidth)
        self.editor.textChanged.connect(self.on_text_changed)
        self.editor.setPlainText(content)
        
        # 设置编辑器的自定义右键菜单
        self.editor.setContextMenuPolicy(Qt.CustomContextMenu)
        self.editor.customContextMenuRequested.connect(self.show_editor_context_menu)
        
        # 重新创建预览区 - 使用QWebEngineView
        self.preview = QWebEngineView()
        self.preview.setContextMenuPolicy(Qt.CustomContextMenu)
        self.preview.customContextMenuRequested.connect(self.show_preview_context_menu)
        
        # 配置WebEngine页面
        self.preview_page = QWebEnginePage(self.preview)
        self.preview.setPage(self.preview_page)
        
        # 重新连接滚动条信号
        self.editor.verticalScrollBar().valueChanged.connect(self.sync_preview_scroll)
        
        # 重新应用Markdown语法高亮
        self.highlighter = MarkdownHighlighter(self.editor.document())
        
        # 将组件添加到分隔器
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        
        # 移除旧的HTML复选框
        old_checkbox = self.html_checkbox
        self.layout.removeWidget(old_checkbox)
        old_checkbox.deleteLater()
        
        # 重新创建HTML复选框
        self.html_checkbox = QCheckBox("启用HTML支持")
        self.html_checkbox.setToolTip("启用后可以在Markdown中嵌入HTML代码（不执行JavaScript）")
        self.html_checkbox.stateChanged.connect(self.toggle_html_support)
        self.html_checkbox.setChecked(html_enabled)
        
        # 将分隔器和新的HTML复选框添加到布局
        self.layout.addWidget(self.splitter)
        self.layout.addWidget(self.html_checkbox)
        
        # 恢复分隔器的大小比例
        new_sizes = [int(r * total_size) for r in ratio]
        self.splitter.setSizes(new_sizes)
        
        # 立即更新预览
        self.update_preview()
        
        # 恢复滚动位置
        QTimer.singleShot(100, lambda: self.editor.verticalScrollBar().setValue(editor_scroll_value))
        
        # 销毁旧的分隔器
        old_splitter.deleteLater()
        
    def get_layout_orientation(self):
        """获取布局方向"""
        return self.current_layout