from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # JWT Configuration
    jwt_secret: str = "your-super-secret-jwt-key-here-min-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_expires_delta: int = 1440  # 24 hours in minutes
    
    # Database Configuration
    database_url: str = "sqlite:///./game.db"
    
    # Game Configuration  
    withdraw_min_amount: int = 100
    entry_fee_default: int = 10
    
    # Game Mode Configurations
    game_modes: dict = {
        "classic": {
            "entry_fee": 10,
            "duration": None,  # Unlimited
            "max_players": 20
        },
        "fast": {
            "entry_fee": 15,
            "duration": 300,  # 5 minutes
            "max_players": 15
        },
        "hardcore": {
            "entry_fee": 25,
            "duration": 600,  # 10 minutes
            "max_players": 10
        }
    }
    
    # NOWPayments Configuration
    nowpayments_api_key: str = "your-nowpayments-api-key"
    nowpayments_ipn_secret: str = "your-nowpayments-ipn-secret-key"
    nowpayments_api_url: str = "https://api.nowpayments.io/v1"
    public_base_url: str = "http://localhost:8000"
    usdt_network: str = "trc20"
    
    # CORS Configuration
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()