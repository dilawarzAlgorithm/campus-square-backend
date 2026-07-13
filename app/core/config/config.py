from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    admin_id: str
    admin_password: str
    supabase_url: str
    supabase_key: str

    community_mail_id: str = ""

    def get_community_credentials(self) -> dict:
        if not self.community_mail_id: return {}
        return dict(item.split(":") for item in self.community_mail_id.split(",") if ":" in item)

    class Config:
        env_file = ".env"

settings = Settings()