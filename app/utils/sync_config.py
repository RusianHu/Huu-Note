import os
from app.utils.config_manager import ConfigManager

class SyncConfig:
    """
    同步配置管理类
    现在使用统一的配置管理器来处理同步配置
    """
    def __init__(self):
        # 使用统一的配置管理器
        self.config_manager = ConfigManager()
        # 添加config属性，用于兼容性
        self.config = self.load_config()
        
    def load_config(self):
        """兼容性方法，返回同步配置部分"""
        return {
            "server_url": self.get("server_url"),
            "api_key": self.get("api_key"),
            "enabled": self.is_sync_enabled(),
            "last_sync_time": self.get("last_sync_time", 0),
            "file_mapping": self.get("file_mapping", {})
        }
    
    def get(self, key, default=None):
        """获取配置值"""
        return self.config_manager.get_sync_setting(key, default)
    
    def set(self, key, value):
        """设置配置值"""
        self.config_manager.set_sync_setting(key, value)
        # 更新内部配置字典
        self.config = self.load_config()
        
    def is_sync_enabled(self):
        """检查同步是否已启用"""
        return self.config_manager.is_sync_enabled()
        
    def get_file_mapping(self, local_path):
        """获取本地文件对应的云端路径"""
        return self.config_manager.get_file_mapping(local_path)
        
    def set_file_mapping(self, local_path, cloud_path):
        """设置本地文件与云端文件的映射关系"""
        self.config_manager.set_file_mapping(local_path, cloud_path)
        # 更新内部配置字典
        self.config = self.load_config()
        
    def remove_file_mapping(self, local_path):
        """删除文件映射"""
        self.config_manager.remove_file_mapping(local_path)
        # 更新内部配置字典
        self.config = self.load_config()
            
    def update_last_sync_time(self):
        """更新最后同步时间"""
        self.config_manager.update_last_sync_time()
        # 更新内部配置字典
        self.config = self.load_config()
        
    def save_config(self):
        """兼容性方法，保存配置"""
        # 实际保存操作已在 set 方法中完成
        pass
        
    @property
    def settings(self):
        """
        提供对应用设置的访问
        解决 'SyncConfig' object has no attribute 'settings' 错误
        """
        return {
            "notes_directory": self.config_manager.get_app_setting("notes_directory", 
                                                                os.path.expanduser("~/markdown_notes"))
        }