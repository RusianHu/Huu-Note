# 老司机笔记 - 轻量级Markdown笔记 支持搭建同步服务器

 - 抛弃到处都是的臃肿笔记应用，返璞归真。

![image](https://github.com/user-attachments/assets/bdc044d3-2520-417f-86a7-05bc41972561)


- 现已支持 SVG 渲染

![image](https://github.com/user-attachments/assets/2497f797-d36f-4b9c-8453-34372a47b094)

## 功能

- 📝 **Markdown编辑**：支持实时预览的Markdown编辑器
- 🖌️ **HTML支持**：可插入安全的HTML模板（表格/折叠块/SVG等），支持智能过滤危险内容
- ↔️ **布局切换**：支持编辑器与预览窗口的垂直/水平双向布局切换
- 🔄 **同步滚动**：基于QWebEngineView的智能滚动同步机制
- 📂 **文件管理**：内置文件浏览器，方便管理笔记文件
- 🔍 **全文搜索**：支持笔记内容的快速搜索
- 📦 **便携版本**：提供单文件可执行版本
- 🔄 **导入导出**：支持笔记的导入和导出功能
- ☁️ **云端同步**：支持笔记的云端保存和跨设备同步

## 安装指南

### 下载

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/RusianHu/Huu-Note?style=for-the-badge)](https://github.com/RusianHu/Huu-Note/releases/latest)

或访问[发布页面](https://github.com/RusianHu/Huu-Note/releases)获取所有版本

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
## 依赖说明

- PyQt5 (>=5.15.4) - GUI框架
- PyQtWebEngine (>=5.15.6) - Web引擎支持
- mistune (>=2.0.4) - Markdown解析器
- markdown (>=3.3.7) - Markdown支持

完整依赖见[requirements.txt](requirements.txt)

## 云端同步使用指南

### 服务器部署
1. 确保服务器已安装PHP 7.0+环境
2. 将`server`目录上传至您的Web服务器
3. 修改`api_keys.php`中的API密钥为更安全的密钥
4. 确保服务器有写入权限，`notes_storage`目录会自动创建

### 客户端配置
1. 在Huu Note客户端中打开设置
2. 找到"云端同步"选项
3. 输入服务器地址和API密钥
4. 点击"测试连接"验证配置
5. 保存设置后即可使用云端同步功能

### 功能说明
- 自动同步：笔记修改后会自动上传到服务器
- 多设备同步：在不同设备登录同一账号可获取最新笔记
- 历史版本：服务器会保留笔记的历史版本

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
│   ├── editor/          # Markdown编辑器模块（含HTML支持）
│   ├── explorer/        # 文件浏览器模块
│   ├── search/          # 搜索功能模块
│   └── utils/           # 工具类模块
└── resources/           # 资源文件
```

## 编辑器特性

### HTML支持

- 安全过滤：自动移除JavaScript代码和危险标签
- 模板系统：支持快速插入常用HTML组件
- SVG支持：完整保留矢量图形特性

### 同步滚动

- 基于QWebEngineView的JavaScript滚动同步
- 智能内容比例映射算法
- 防抖动机制确保流畅体验

老司机笔记的Markdown编辑器实现了智能同步滚动功能：

- **双向同步**：编辑窗口和预览窗口之间保持位置同步
- **智能定位**：根据内容结构自动匹配对应位置
- **流畅体验**：无论是编辑还是预览，都能保持在相同内容区域

这一功能大幅提升了Markdown编辑的使用体验，特别是在编辑长文档时更为实用。


## 未来计划

- 📱 多平台支持

## 许可证

本项目采用 MIT 许可证 - 详情请查看 [LICENSE](LICENSE) 文件
