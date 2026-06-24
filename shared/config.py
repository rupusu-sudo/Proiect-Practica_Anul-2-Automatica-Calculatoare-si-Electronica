from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict  # pyrefly: ignore [missing-import]
from pydantic import Field  # pyrefly: ignore [missing-import]

class AgentSettings(BaseSettings):
    # LLM Settings
    LLM_PROVIDER: Literal["openai", "ollama"] = Field(default="openai", description="LLM provider: openai or ollama")
    OPENAI_API_KEY: str = Field(default="mock-key-for-testing", description="API key for OpenAI API")
    OPENAI_BASE_URL: str = Field(default="https://api.openai.com/v1", description="Base URL for OpenAI API compatible endpoints")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="Model name for OpenAI API")
    
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", description="Base URL for local Ollama instance")
    OLLAMA_MODEL: str = Field(default="llama3", description="Model name for Ollama provider")
    
    # Agent Host/Port Configurations
    COORDINATOR_HOST: str = Field(default="127.0.0.1")
    COORDINATOR_PORT: int = Field(default=8000)
    
    SUMMARIZER_HOST: str = Field(default="127.0.0.1")
    SUMMARIZER_PORT: int = Field(default=8001)
    
    TRANSLATOR_HOST: str = Field(default="127.0.0.1")
    TRANSLATOR_PORT: int = Field(default=8002)
    
    RESEARCHER_HOST: str = Field(default="127.0.0.1")
    RESEARCHER_PORT: int = Field(default=8003)
    
    VALIDATOR_HOST: str = Field(default="127.0.0.1")
    VALIDATOR_PORT: int = Field(default=8004)
    
    EXPORT_HOST: str = Field(default="127.0.0.1")
    EXPORT_PORT: int = Field(default=8005)
    
    # HTTP and Communication Settings
    REQUEST_TIMEOUT_SECONDS: float = Field(default=30.0)
    MAX_RETRIES: int = Field(default=3)
    BACKOFF_FACTOR: float = Field(default=1.5)
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO")

    # Load environment variables from .env file if it exists
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def coordinator_url(self) -> str:
        return f"http://{self.COORDINATOR_HOST}:{self.COORDINATOR_PORT}"

    @property
    def summarizer_url(self) -> str:
        return f"http://{self.SUMMARIZER_HOST}:{self.SUMMARIZER_PORT}"

    @property
    def translator_url(self) -> str:
        return f"http://{self.TRANSLATOR_HOST}:{self.TRANSLATOR_PORT}"

    @property
    def researcher_url(self) -> str:
        return f"http://{self.RESEARCHER_HOST}:{self.RESEARCHER_PORT}"

    @property
    def validator_url(self) -> str:
        return f"http://{self.VALIDATOR_HOST}:{self.VALIDATOR_PORT}"

    @property
    def export_url(self) -> str:
        return f"http://{self.EXPORT_HOST}:{self.EXPORT_PORT}"

settings = AgentSettings()

