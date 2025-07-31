"""Configuration centralisée pour Phoenix Letters."""
import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

class ConfigurationError(Exception):
    """Exception levée quand une variable d'environnement requise est manquante."""
    pass

@dataclass(frozen=True)
class Settings:
    """Configuration application."""
    
    # API Configuration
    google_api_key: Optional[str] = None
    france_travail_client_id: Optional[str] = None
    france_travail_client_secret: Optional[str] = None
    
    # Security Configuration
    max_file_size: int = 5 * 1024 * 1024  # 5MB
    allowed_file_types: tuple = ('.pdf', '.txt')
    session_timeout: int = 3600  # 1 hour
    
    # Performance Configuration
    cache_ttl: int = 300  # 5 minutes
    max_concurrent_requests: int = 10
    
    # Feature Flags
    enable_mirror_match: bool = True
    enable_smart_coach: bool = True
    enable_trajectory_builder: bool = True
    
    # Authentication Configuration
    auth_enabled: bool = False
    jwt_secret_key: Optional[str] = None
    jwt_refresh_secret: Optional[str] = None
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 30
    
    # Supabase Configuration
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    
    def __post_init__(self):
        load_dotenv(find_dotenv(), override=True)  # Force reload
        object.__setattr__(self, 'google_api_key', self._get_required_env("GOOGLE_API_KEY"))
        object.__setattr__(self, 'france_travail_client_id', os.getenv('FRANCETRAVAIL_CLIENT_ID'))
        object.__setattr__(self, 'france_travail_client_secret', os.getenv('FRANCETRAVAIL_CLIENT_SECRET'))
        
        # Authentication configuration
        object.__setattr__(self, 'auth_enabled', os.getenv('AUTH_ENABLED', 'false').lower() == 'true')
        object.__setattr__(self, 'jwt_secret_key', os.getenv('JWT_SECRET_KEY'))
        object.__setattr__(self, 'jwt_refresh_secret', os.getenv('JWT_REFRESH_SECRET'))
        print(f"DEBUG: JWT_SECRET_KEY loaded: {self.jwt_secret_key}")
        
        # JWT expiration times
        jwt_access_expire = os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES')
        if jwt_access_expire:
            object.__setattr__(self, 'jwt_access_token_expire_minutes', int(jwt_access_expire))
        
        jwt_refresh_expire = os.getenv('JWT_REFRESH_TOKEN_EXPIRE_DAYS')
        if jwt_refresh_expire:
            object.__setattr__(self, 'jwt_refresh_token_expire_days', int(jwt_refresh_expire))
        
        # Supabase configuration
        object.__setattr__(self, 'supabase_url', self._get_required_env('SUPABASE_URL'))
        object.__setattr__(self, 'supabase_key', self._get_required_env('SUPABASE_KEY'))

    def _get_required_env(self, key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise ConfigurationError(f"Required environment variable {key} is missing")
        return value

