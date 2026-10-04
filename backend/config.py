import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    DB_NAME = os.getenv("DB_NAME", "sellerzone")
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-change-this-jwt-secret")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    ADMIN_SECRET = os.getenv("ADMIN_SECRET", "dev-only-change-this-admin-secret")
    JWT_EXP_DAYS = 7