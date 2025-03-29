from PyQt5.QtCore import QRegExp, Qt
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter

class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.highlighting_rules = []
        
        # 标题 # 开头
        header_format = QTextCharFormat()
        header_format.setForeground(QColor("#0077AA"))
        header_format.setFontWeight(QFont.Bold)
        for i in range(1, 7):
            pattern = QRegExp(f"^{'#' * i}\\s.*$")
            self.highlighting_rules.append((pattern, header_format))
        
        # 粗体 **文字**
        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Bold)
        bold_format.setForeground(QColor("#303030"))
        pattern = QRegExp("\\*\\*.*\\*\\*")
        pattern.setMinimal(True)
        self.highlighting_rules.append((pattern, bold_format))
        
        # 斜体 *文字*
        italic_format = QTextCharFormat()
        italic_format.setFontItalic(True)
        italic_format.setForeground(QColor("#303030"))
        pattern = QRegExp("\\*.*\\*")
        pattern.setMinimal(True)
        self.highlighting_rules.append((pattern, italic_format))
        
        # 链接 [文字](链接)
        link_format = QTextCharFormat()
        link_format.setForeground(QColor("#0077AA"))
        link_format.setUnderlineStyle(QTextCharFormat.SingleUnderline)
        pattern = QRegExp("\\[.*\\]\\(.*\\)")
        pattern.setMinimal(True)
        self.highlighting_rules.append((pattern, link_format))
        
        # 行内代码 `代码`
        inline_code_format = QTextCharFormat()
        inline_code_format.setForeground(QColor("#D0384D"))
        inline_code_format.setBackground(QColor("#F0F0F0"))
        pattern = QRegExp("`.*`")
        pattern.setMinimal(True)
        self.highlighting_rules.append((pattern, inline_code_format))
        
        # 代码块 ```代码```
        code_block_format = QTextCharFormat()
        code_block_format.setForeground(QColor("#D0384D"))
        code_block_format.setBackground(QColor("#F0F0F0"))
        pattern = QRegExp("```.*```")
        pattern.setMinimal(True)
        self.highlighting_rules.append((pattern, code_block_format))
        
        # 引用 > 文字
        quote_format = QTextCharFormat()
        quote_format.setForeground(QColor("#777777"))
        pattern = QRegExp("^>.*$")
        self.highlighting_rules.append((pattern, quote_format))
        
        # 列表项 - 文字 或 * 文字
        list_format = QTextCharFormat()
        list_format.setForeground(QColor("#8B4726"))
        pattern = QRegExp("^[-*+]\\s.*$")
        self.highlighting_rules.append((pattern, list_format))
        
        # 数字列表项 1. 文字
        numbered_list_format = QTextCharFormat()
        numbered_list_format.setForeground(QColor("#8B4726"))
        pattern = QRegExp("^\\d+\\.\\s.*$")
        self.highlighting_rules.append((pattern, numbered_list_format))
    
    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)