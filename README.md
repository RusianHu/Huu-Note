# 老司机笔记 - 轻量级Markdown笔记

做着玩的，交流学习

![image](https://github.com/user-attachments/assets/d854a4c5-08b1-4b78-87f6-f3c5b7afabef)


## 功能

- 📝 **Markdown编辑**：支持实时预览的Markdown编辑器
- 📂 **文件管理**：内置文件浏览器，方便管理笔记文件
- 🔍 **全文搜索**：支持笔记内容的快速搜索
- 📦 **便携版本**：提供单文件可执行版本
- 🔄 **导入导出**：支持笔记的导入和导出功能
- ☁️ **云端同步**：支持笔记的云端保存和跨设备同步

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

## 未来计划

- 📱 多平台支持优化
