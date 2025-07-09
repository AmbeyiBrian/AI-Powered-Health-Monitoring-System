"""
User authentication models and utilities
"""
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from datetime import datetime, timezone
from ..data.models import db

bcrypt = Bcrypt()

class User(UserMixin, db.Model):
    """Enhanced User model with authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    
    # Profile information
    age = db.Column(db.Integer)
    height = db.Column(db.Float)  # in cm
    weight = db.Column(db.Float)  # in kg
    fitness_level = db.Column(db.String(20), default='moderate')  # low, moderate, high
    medical_conditions = db.Column(db.Text)
    timezone = db.Column(db.String(50), default='Africa/Nairobi')  # User's timezone
    
    # Authentication tracking
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    
    # Sensor configuration
    sensor_devices = db.relationship('SensorDevice', backref='owner', lazy=True, cascade='all, delete-orphan')
    health_data = db.relationship('HealthData', backref='user_profile', lazy=True, cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='user_profile', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Verify password"""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.now(timezone.utc)
        db.session.commit()
    
    def is_authenticated(self):
        """Required by Flask-Login"""
        return True
    
    def is_anonymous(self):
        """Required by Flask-Login"""
        return False
    
    def get_id(self):
        """Required by Flask-Login - return user_id instead of id"""
        return self.user_id
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'user_id': self.user_id,
            'email': self.email,
            'name': self.name,
            'age': self.age,
            'height': self.height,
            'weight': self.weight,
            'fitness_level': self.fitness_level,
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class SensorDevice(db.Model):
    """Model for tracking user's sensor devices"""
    __tablename__ = 'sensor_devices'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    device_name = db.Column(db.String(100), nullable=False)
    device_type = db.Column(db.String(50), nullable=False)  # smartwatch, fitness_tracker, medical_device
    manufacturer = db.Column(db.String(50))
    model = db.Column(db.String(50))
    
    # Authentication for device
    api_key = db.Column(db.String(128), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # User association
    user_id = db.Column(db.String(50), db.ForeignKey('users.user_id'), nullable=False)
    
    # Device metadata
    registered_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_sync = db.Column(db.DateTime)
    firmware_version = db.Column(db.String(20))
    
    # Data collection settings
    collection_interval = db.Column(db.Integer, default=60)  # seconds
    enabled_metrics = db.Column(db.JSON)  # ['heart_rate', 'blood_oxygen', 'activity']
    
    def generate_api_key(self):
        """Generate a new API key for this device"""
        import secrets
        self.api_key = secrets.token_urlsafe(32)
        return self.api_key
    
    def update_last_sync(self):
        """Update last sync timestamp"""
        self.last_sync = datetime.now(timezone.utc)
    
    def to_dict(self):
        """Convert device to dictionary"""
        return {
            'device_id': self.device_id,
            'device_name': self.device_name,
            'device_type': self.device_type,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'is_active': self.is_active,
            'registered_at': self.registered_at.isoformat() if self.registered_at else None,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'firmware_version': self.firmware_version,
            'collection_interval': self.collection_interval,
            'enabled_metrics': self.enabled_metrics
        }


def create_user(email, password, name, **kwargs):
    """Create a new user account"""
    import uuid
    
    # Check if user already exists
    if User.query.filter_by(email=email).first():
        raise ValueError("User with this email already exists")
    
    # Generate unique user_id
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    while User.query.filter_by(user_id=user_id).first():
        user_id = f"user_{uuid.uuid4().hex[:8]}"
    
    # Create new user
    user = User(
        user_id=user_id,
        email=email,
        name=name,
        **kwargs
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    return user


def authenticate_user(email, password):
    """Authenticate user login"""
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        user.failed_login_attempts = 0
        user.update_last_login()
        return user
    elif user:
        user.failed_login_attempts += 1
        db.session.commit()
    
    return None


def register_sensor_device(user_id, device_name, device_type, **kwargs):
    """Register a new sensor device for a user"""
    import uuid
    
    # Generate unique device_id
    device_id = f"{device_type}_{uuid.uuid4().hex[:8]}"
    while SensorDevice.query.filter_by(device_id=device_id).first():
        device_id = f"{device_type}_{uuid.uuid4().hex[:8]}"
    
    # Create device
    device = SensorDevice(
        device_id=device_id,
        device_name=device_name,
        device_type=device_type,
        user_id=user_id,
        **kwargs
    )
    device.generate_api_key()
    
    db.session.add(device)
    db.session.commit()
    
    return device
