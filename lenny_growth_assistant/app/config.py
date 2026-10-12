from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "The Lenny Growth Assistant"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://postgres:Krup%4021@localhost:5432/lenny_assistant"
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-haiku-latest"
    retrieval_top_k: int = 5
    min_retrieval_score: float = 0.08
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
