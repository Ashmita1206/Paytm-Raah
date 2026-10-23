import os

class Settings:
    PROJECT_NAME: str = "RAAH — Autonomous Payment Intelligence & Recovery"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./raah.db")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "")
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "t")
    RETRYGUARD_WINDOW_MINUTES: int = 15
    RETRYGUARD_SIMILARITY_PERCENT: float = 0.05
    BACKGROUND_WORKER_INTERVAL_SECONDS: int = 5

settings = Settings()
