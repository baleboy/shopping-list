from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_dir: Path = Path("data")
    api_key: str = ""
    anthropic_api_key: str = ""
    github_webhook_secret: str = ""

    model_config = {"env_prefix": "SHOPPING_"}


settings = Settings()
