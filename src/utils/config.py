"""
Configuration settings for the Health Monitoring System
"""
import os
from datetime import timedelta


class Config:
    """Base configuration class"""
    
    # Application settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///health_monitoring.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Authentication settings
    WTF_CSRF_ENABLED = True
    SESSION_PROTECTION = 'strong'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_PASSWORD_COMPLEXITY = True
    
    # Device/Sensor integration settings
    MAX_DEVICES_PER_USER = 10
    DEVICE_API_KEY_LENGTH = 32
    SENSOR_DATA_RETENTION_DAYS = 365
    
    # Health data settings
    ANOMALY_THRESHOLD = 0.1  # Percentage of data points that can be anomalies
    
    # Heart rate ranges (BPM)
    HEART_RATE_NORMAL_MIN = 60
    HEART_RATE_NORMAL_MAX = 100
    HEART_RATE_CRITICAL_LOW = 50
    HEART_RATE_CRITICAL_HIGH = 120
    
    # Blood oxygen ranges (%)
    BLOOD_OXYGEN_NORMAL_MIN = 95
    BLOOD_OXYGEN_CRITICAL_LOW = 90
    
    # Data collection intervals
    DATA_COLLECTION_INTERVAL = timedelta(minutes=1)
    ANOMALY_CHECK_INTERVAL = timedelta(minutes=5)
    
    # ML Model settings
    MODEL_RETRAIN_INTERVAL = timedelta(days=7)
    MIN_DATA_POINTS_FOR_TRAINING = 100
    
    # Alert settings
    ALERT_COOLDOWN_PERIOD = timedelta(minutes=30)
    
    # User authentication settings
    SESSION_TIMEOUT = timedelta(hours=24)
    PASSWORD_MIN_LENGTH = 8
    REQUIRE_EMAIL_VERIFICATION = False
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Sensor integration settings
    SENSOR_API_RATE_LIMIT = 100  # requests per minute per user
    SENSOR_DATA_RETENTION_DAYS = 365
    ALLOW_SENSOR_AUTO_REGISTRATION = True
    SENSOR_AUTH_TOKEN_EXPIRY = timedelta(days=30)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///health_monitoring_dev.db'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///health_monitoring_test.db'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
