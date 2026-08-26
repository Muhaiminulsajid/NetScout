"""Application configuration loaded from environment variables."""
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Core ---
    app_name: str = "NetScout"
    debug: bool = False
    secret_key: str = "rtrdftctfcrdxeszrdvhnjnmokmoijhhgvtrsewzedvbjnjhhubhubhhgyvhu"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24


    
    
    
    
    
    
    

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

    # --- Database / queues ---
    database_url: str = "postgresql+psycopg2://netscout:netscout@db:5432/netscout"
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    # --- External API keys (placeholders; features degrade gracefully) ---
    virustotal_api_key: str = "YOUR_VIRUS_TOTAL_API_KEY"
    google_safe_browsing_api_key: str = "YOUR_SAFE_BROWSING_API_KEY"
    bing_visual_search_api_key: str = "YOUR_BING_VISUAL_SEARCH_API_KEY"
    google_vision_api_key: str = "YOUR_GOOGLE_CLOUD_VISION_API_KEY"

    # --- Crawler ---
    max_crawl_depth: int = 5
    max_links_per_page: int = 40
    crawler_timeout_seconds: int = 25

    # --- Quotas (per user, per day) ---
    daily_crawl_quota: int = 50
    daily_image_search_quota: int = 25
    rate_limit_per_minute: int = 30

    # --- Uploads ---
    upload_dir: str = "/data/uploads"
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB

    class Config:
        env_file = ".env"
        extra = "ignore"


PLACEHOLDER_PREFIX = "YOUR_"


def key_configured(value: str) -> bool:
    """True when an API key looks real (not empty / not a placeholder)."""
    return bool(value) and not value.startswith(PLACEHOLDER_PREFIX)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
