import uuid
from pathlib import Path

import oss2

from config import settings


# 初始化 OSS 资源（模块级单例）
_auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
_bucket = oss2.Bucket(_auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)

# 签名 URL 默认有效时长（秒）
_DEFAULT_EXPIRES = 3600 * 24 * 7  # 7 天


def upload_image(
    file_data: bytes,
    filename: str | None = None,
    prefix: str = "images",
    expires: int = _DEFAULT_EXPIRES,
) -> str:
    """上传图片到阿里云 OSS，返回带签名的临时访问 URL。

    Args:
        file_data: 图片的二进制数据
        filename: 原始文件名（用于保留扩展名），为空则自动生成
        prefix: OSS 对象 key 的前缀目录
        expires: 签名 URL 有效时长（秒），默认 7 天

    Returns:
        带签名的公网访问 URL
    """
    # 生成唯一 object key
    ext = Path(filename).suffix if filename else ".png"
    object_key = f"{prefix}/{uuid.uuid4().hex}{ext}"

    _bucket.put_object(object_key, file_data)

    return _bucket.sign_url("GET", object_key, expires)


def upload_local_image(local_path: str, prefix: str = "images") -> str:
    """将本地图片文件上传到阿里云 OSS。

    Args:
        local_path: 本地图片路径
        prefix: OSS 对象 key 的前缀目录

    Returns:
        图片的公网访问 URL
    """
    with open(local_path, "rb") as f:
        file_data = f.read()
    return upload_image(file_data, filename=Path(local_path).name, prefix=prefix)
