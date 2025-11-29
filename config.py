"""
Central configuration for VideoTranscript Pro.

This module defines configuration classes suitable for:
- local development
- testing
- production / public deployment

Environment selection is driven by APP_ENV or FLASK_ENV:
  APP_ENV=production  -> ProductionConfig
  APP_ENV=testing     -> TestingConfig
  APP_ENV=development -> DevelopmentConfig (default)
"""

import os
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    """Base configuration shared across all environments."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY")  # must be set in real deployments
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # External APIs
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # Supabase
    SUPABASE_URL = os.getenv("REACT_APP_SUPABASE_URL") or os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY = os.getenv("REACT_APP_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

    # Paths
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Security
    SESSION_COOKIE_SECURE = False  # overridden in production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = False


class TestingConfig(BaseConfig):
    DEBUG = False
    TESTING = True


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False

    # Harden cookies in production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Strict"


def get_config_name() -> str:
    """Return the config name based on environment variables."""
    return os.getenv("APP_ENV") or os.getenv("FLASK_ENV") or "development"


def get_config() -> type[BaseConfig]:
    """Return the appropriate config class for the current environment."""
    name = get_config_name().lower()
    if name in {"prod", "production"}:
        return ProductionConfig
    if name in {"test", "testing"}:
        return TestingConfig
    # default
    return DevelopmentConfig


# Convenient alias for app factories
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

