from  pydantic_settings import BaseSettings  , SettingsConfigDict

class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

# Email
    smtp_server: str
    smtp_port: int
    email_sender: str
    email_password: str

    # Twilio
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_whatsapp_number: str

    # Alerts
    alert_threshold: int
    daily_check_hour: int

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"   # 🔥 THIS fixes your Alembic crash
    )
        
settings = Settings() 