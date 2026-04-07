import json

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = Field("se-toolkit-hackathon", alias="NAME")
    debug: bool = Field(False, alias="DEBUG")
    address: str = Field("0.0.0.0", alias="ADDRESS")
    port: int = Field(8000, alias="PORT")
    reload: bool = Field(False, alias="RELOAD")

    api_key: str = Field("my-secret-api-key", alias="LMS_API_KEY")

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"], alias="CORS_ORIGINS")

    enable_interactions: bool = Field(True, alias="BACKEND_ENABLE_INTERACTIONS")
    enable_learners: bool = Field(True, alias="BACKEND_ENABLE_LEARNERS")

    autochecker_api_url: str = Field("", alias="AUTOCHECKER_API_URL")
    autochecker_email: str = Field("", alias="AUTOCHECKER_API_LOGIN")
    autochecker_password: str = Field("", alias="AUTOCHECKER_API_PASSWORD")

    db_host: str = Field("", alias="DB_HOST")
    db_port: int = Field(5432, alias="DB_PORT")
    db_name: str = Field("", alias="DB_NAME")
    db_user: str = Field("", alias="DB_USER")
    db_password: str = Field("", alias="DB_PASSWORD")
    database_url: str = Field("", alias="DATABASE_URL")

    assistant_llm_api_url: str = Field(
        "https://openrouter.ai/api/v1",
        validation_alias=AliasChoices("ASSISTANT_LLM_API_URL", "OPENROUTER_BASE_URL"),
    )
    assistant_llm_api_key: str = Field(
        "",
        validation_alias=AliasChoices("ASSISTANT_LLM_API_KEY", "OPENROUTER_API_KEY", "LLM_API_KEY"),
    )
    assistant_llm_model: str = Field(
        "openai/gpt-4o-mini",
        validation_alias=AliasChoices("ASSISTANT_LLM_MODEL", "OPENROUTER_MODEL", "LLM_API_MODEL"),
    )
    assistant_llm_site_url: str = Field("http://localhost:5173", alias="OPENROUTER_SITE_URL")
    assistant_llm_app_name: str = Field("se-toolkit-hackathon", alias="OPENROUTER_APP_NAME")
    assistant_llm_verify_ssl: bool = Field(True, alias="ASSISTANT_LLM_VERIFY_SSL")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, list):
            return value

        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return ["http://localhost:5173"]

            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except json.JSONDecodeError:
                pass

            cleaned = raw.strip("[]")
            parts = [
                part.strip().strip('"').strip("'")
                for part in cleaned.split(",")
                if part.strip()
            ]
            return parts or ["http://localhost:5173"]

        return ["http://localhost:5173"]


settings = Settings.model_validate({})
