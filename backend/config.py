from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    """应用配置"""

    # MinerU 配置 - 使用绝对路径
    MINERU_OUTPUT_DIR: str = str(Path(__file__).parent / "temp" / "mineru_output")

    # 大模型配置
    DASHSCOPE_API_KEY: str
    MODEL_NAME: str = "qwen-vl-plus"  # 多模态模型，支持图片理解

    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # 文件上传配置 - 使用绝对路径
    MAX_FILE_SIZE: int = 10485760  # 10MB
    UPLOAD_DIR: str = str(Path(__file__).parent / "temp" / "uploads")

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def cors_origins_list(self) -> List[str]:
        """将 CORS_ORIGINS 字符串转换为列表"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
