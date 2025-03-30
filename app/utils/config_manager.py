import os
import json

class ConfigManager:
    """
    统一配置管理类
    整合应用设置和同步配置到一个文件中
    """
    _instance = None
    
    def __new__(cls):
        # 单例模式实现
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # 配置文件路径
        self.config_dir = os.path.expanduser("~/markdown_notes")
        self.config_file = os.path.join(self.config_dir, ".huu_note_config.json")
        
        # 加载配置
        self.config = self.load_config()
        self._initialized = True
    
    def load_config(self):
        """加载配置文件"""
        # 默认配置
        default_config = {
            # 应用设置部分
            "app_settings": {
                "notes_directory": os.path.expanduser("~/markdown_notes"),
                "font_family": "Microsoft YaHei",
                "font_size": 11,
                "theme": "default",
                "auto_save": True,
                "auto_save_interval": 60,  # 秒
                "editor_layout": "horizontal"  # 默认左右布局
            },
            # 同步配置部分
            "sync_settings": {
                "server_url": "https://yanshanlaosiji.top/HuuNote/HuuNoteServer.php",
                "api_key": "",
                "enabled": False,
                "last_sync_time": 0,
                "file_mapping": {}  # 本地文件路径到云端路径的映射
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as file:
                    loaded_config = json.load(file)
                    # 移除备注字段（如果存在）
                    if "__comment__" in loaded_config:
                        del loaded_config["__comment__"]
                    
                    # 合并配置（保持结构）
                    if "app_settings" in loaded_config:
                        default_config["app_settings"].update(loaded_config["app_settings"])
                    if "sync_settings" in loaded_config:
                        default_config["sync_settings"].update(loaded_config["sync_settings"])
            except Exception as e:
                print(f"加载配置失败: {str(e)}")
                
        return default_config
    
    def save_config(self):
        """保存配置到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # 添加配置文件备注
            config_with_comment = self.config.copy()
            config_with_comment["__comment__"] = "此文件为老司机笔记配置文件，包含应用设置和同步配置。建议使用应用内功能修改而非手动编辑。"
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as file:
                json.dump(config_with_comment, file, indent=4, ensure_ascii=False)
                
            return True
        except Exception as e:
            print(f"保存配置失败: {str(e)}")
            return False
    
    def get_app_setting(self, key, default=None):
        """获取应用设置值"""
        return self.config["app_settings"].get(key, default)
    
    def set_app_setting(self, key, value):
        """设置应用设置值"""
        self.config["app_settings"][key] = value
        self.save_config()
    
    def get_sync_setting(self, key, default=None):
        """获取同步设置值"""
        return self.config["sync_settings"].get(key, default)
    
    def set_sync_setting(self, key, value):
        """设置同步设置值"""
        self.config["sync_settings"][key] = value
        self.save_config()
    
    def is_sync_enabled(self):
        """检查同步是否已启用"""
        enabled = self.get_sync_setting("enabled", False)
        # 将可能的字符串值转换为布尔值
        if isinstance(enabled, str):
            return enabled.lower() == 'true'
        return bool(enabled) and bool(self.get_sync_setting("api_key", ""))
    
    def get_file_mapping(self, local_path):
        """获取本地文件对应的云端路径"""
        mappings = self.get_sync_setting("file_mapping", {})
        return mappings.get(local_path)
    
    def set_file_mapping(self, local_path, cloud_path):
        """设置本地文件与云端文件的映射关系"""
        mappings = self.get_sync_setting("file_mapping", {})
        mappings[local_path] = cloud_path
        self.set_sync_setting("file_mapping", mappings)
    
    def remove_file_mapping(self, local_path):
        """删除文件映射"""
        mappings = self.get_sync_setting("file_mapping", {})
        if local_path in mappings:
            del mappings[local_path]
            self.set_sync_setting("file_mapping", mappings)
    
    def update_last_sync_time(self):
        """更新最后同步时间"""
        import time
        self.set_sync_setting("last_sync_time", int(time.time()))