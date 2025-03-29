# 老司机笔记 - 轻量级Markdown笔记

做着玩的，交流学习

## 功能

- 📝 **Markdown编辑**：支持实时预览的Markdown编辑器
- 📂 **文件管理**：内置文件浏览器，方便管理笔记文件
- 🔍 **全文搜索**：支持笔记内容的快速搜索
- 📦 **便携版本**：提供单文件可执行版本
- 🔄 **导入导出**：支持笔记的导入和导出功能

## 安装指南

### 从源码运行

1. 确保已安装Python 3.8+
2. 克隆本仓库
3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
4. 运行主程序：
   ```bash
   python main.py
   ```

### 使用预构建版本

1. 从Release页面下载最新版HuuNote.exe
2. 直接双击运行即可

## 构建方法

### 标准构建

运行标准构建脚本：
```bash
python 标准构筑程序.py
```

### 单文件构建

运行一键构建脚本：
```bash
python 一键构筑程序(单文件).py
```

构建完成后，可执行文件将生成在`dist`目录下。

## 项目结构

```
HuuNote/
├── .gitattributes
├── 标准构筑程序.py
├── 环境依赖检测.py
├── 一键构筑程序(单文件).py
├── huu_note.spec
├── main.py
├── app/
│   ├── main_window.py
│   ├── editor/          # Markdown编辑器模块
│   ├── explorer/        # 文件浏览器模块
│   ├── search/          # 搜索功能模块
│   └── utils/           # 工具类模块
└── resources/           # 资源文件
```

## 依赖说明

- PyQt5 (>=5.15.4) - GUI框架
- mistune (>=2.0.4) - Markdown解析器
- markdown (>=3.3.7) - Markdown支持

完整依赖见[requirements.txt](requirements.txt)

## 许可证

本项目采用 MIT 许可证 - 详情请查看 [LICENSE](LICENSE) 文件

## 未来计划

- ☁️ 添加云端同步功能 ？
- 📱 多平台支持优化 ？
