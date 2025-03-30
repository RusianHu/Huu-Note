import os
import json
from app.utils.settings import Settings

class SyncConfig:
    """
    同步配置管理类
    管理与云端同步相关的配置信息
    """
    def __init__(self):
        self.settings = Settings()
        self.config_file = os.path.join(
            self.settings.get("notes_directory"),
            ".sync_config.json"
        )
        self.config = self.load_config()
        
    def load_config(self):
        """加载同步配置"""
        default_config = {
            "server_url": "https://yanshanlaosiji.top/HuuNote/HuuNoteServer.php",
            "api_key": "",
            "enabled": False,
            "last_sync_time": 0,
            "file_mapping": {}  # 本地文件路径到云端路径的映射
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as file:
                    loaded_config = json.load(file)
                    # 移除备注字段（如果存在）
                    if "__comment__" in loaded_config:
                        del loaded_config["__comment__"]
                    # 合并默认配置和加载的配置
                    default_config.update(loaded_config)
            except Exception as e:
                print(f"加载同步配置失败: {str(e)}")
                
        return default_config
    
    def save_config(self):
        """保存同步配置"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # 添加配置文件备注
            config_with_comment = self.config.copy()
            config_with_comment["__comment__"] = "此文件为老司机笔记同步配置文件，请勿手动修改。如需更改同步设置，请使用应用内的 同步设置 功能。"
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as file:
                json.dump(config_with_comment, file, indent=4, ensure_ascii=False)
                
            return True
        except Exception as e:
            print(f"保存同步配置失败: {str(e)}")
            return False
    
    def get(self, key, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """设置配置值"""
        self.config[key] = value
        self.save_config()
        
    def is_sync_enabled(self):
        """检查同步是否已启用"""
        # 修复：确保返回布尔值而不是字符串
        enabled = self.config.get("enabled", False)
        # 将可能的字符串值转换为布尔值
        if isinstance(enabled, str):
            return enabled.lower() == 'true'
        return bool(enabled) and bool(self.config.get("api_key", ""))
        
    def get_file_mapping(self, local_path):
        """获取本地文件对应的云端路径"""
        mappings = self.config.get("file_mapping", {})
        return mappings.get(local_path)
        
    def set_file_mapping(self, local_path, cloud_path):
        """设置本地文件与云端文件的映射关系"""
        if "file_mapping" not in self.config:
            self.config["file_mapping"] = {}
        self.config["file_mapping"][local_path] = cloud_path
        self.save_config()
        
    def remove_file_mapping(self, local_path):
        """删除文件映射"""
        if local_path in self.config.get("file_mapping", {}):
            del self.config["file_mapping"][local_path]
            self.save_config()
            
    def update_last_sync_time(self):
        """更新最后同步时间"""
        import time
        self.config["last_sync_time"] = int(time.time())
        self.save_config()