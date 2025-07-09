"""
Utility functions for the Health Monitoring System
"""
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Any
import pandas as pd
import numpy as np
import pytz


def setup_logging(log_level: str = 'INFO', log_file: str = None) -> logging.Logger:
    """
    Set up logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('health_monitoring')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def validate_health_data(data: Dict[str, Any]) -> bool:
    """
    Validate health data format and values
    
    Args:
        data: Health data dictionary
    
    Returns:
        True if data is valid, False otherwise
    """
    required_fields = ['timestamp', 'heart_rate', 'blood_oxygen']
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            return False
    
    # Validate data types and ranges
    try:
        # Heart rate validation
        heart_rate = float(data['heart_rate'])
        if not (30 <= heart_rate <= 200):  # Reasonable physiological range
            return False
        
        # Blood oxygen validation
        blood_oxygen = float(data['blood_oxygen'])
        if not (70 <= blood_oxygen <= 100):  # Reasonable physiological range
            return False
        
        # Timestamp validation
        if isinstance(data['timestamp'], str):
            datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        elif not isinstance(data['timestamp'], datetime):
            return False
        
        return True
    
    except (ValueError, TypeError):
        return False


def calculate_health_score(heart_rate: float, blood_oxygen: float, 
                          activity_level: str = 'moderate') -> Dict[str, Any]:
    """
    Calculate an overall health score based on vital signs
    
    Args:
        heart_rate: Heart rate in BPM
        blood_oxygen: Blood oxygen saturation percentage
        activity_level: Activity level (low, moderate, high)
    
    Returns:
        Dictionary with health score and status
    """
    score = 0
    issues = []
    
    # Heart rate scoring
    if 60 <= heart_rate <= 100:
        score += 40
    elif 50 <= heart_rate < 60 or 100 < heart_rate <= 110:
        score += 25
        issues.append("Heart rate slightly outside normal range")
    else:
        score += 10
        issues.append("Heart rate significantly outside normal range")
    
    # Blood oxygen scoring
    if blood_oxygen >= 95:
        score += 40
    elif 90 <= blood_oxygen < 95:
        score += 25
        issues.append("Blood oxygen slightly low")
    else:
        score += 10
        issues.append("Blood oxygen critically low")
    
    # Activity level bonus
    activity_bonus = {'low': 5, 'moderate': 15, 'high': 20}
    score += activity_bonus.get(activity_level, 10)
    
    # Determine status
    if score >= 85:
        status = "Excellent"
    elif score >= 70:
        status = "Good"
    elif score >= 55:
        status = "Fair"
    else:
        status = "Poor"
    
    return {
        'score': score,
        'status': status,
        'issues': issues,
        'recommendations': generate_recommendations(heart_rate, blood_oxygen, activity_level)
    }


def generate_recommendations(heart_rate: float, blood_oxygen: float, 
                           activity_level: str) -> List[str]:
    """
    Generate health recommendations based on vital signs
    
    Args:
        heart_rate: Heart rate in BPM
        blood_oxygen: Blood oxygen saturation percentage
        activity_level: Activity level
    
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    # Heart rate recommendations
    if heart_rate > 100:
        recommendations.append("Consider relaxation techniques to lower heart rate")
        recommendations.append("Avoid caffeine and stimulants")
    elif heart_rate < 60 and activity_level == 'low':
        recommendations.append("Consider light exercise to improve cardiovascular health")
    
    # Blood oxygen recommendations
    if blood_oxygen < 95:
        recommendations.append("Ensure good ventilation in your environment")
        recommendations.append("Practice deep breathing exercises")
        if blood_oxygen < 90:
            recommendations.append("Consult a healthcare provider immediately")
    
    # Activity level recommendations
    if activity_level == 'low':
        recommendations.append("Increase daily physical activity")
        recommendations.append("Take regular breaks to move around")
    
    # General recommendations
    recommendations.extend([
        "Maintain regular sleep schedule",
        "Stay hydrated throughout the day",
        "Monitor your health metrics regularly"
    ])
    
    return recommendations


def format_timestamp(timestamp: datetime, user_timezone: str = 'Africa/Nairobi') -> str:
    """
    Format timestamp for consistent display in user's timezone
    
    Args:
        timestamp: Datetime object (assumed to be in UTC)
        user_timezone: User's timezone (default: Africa/Nairobi)
    
    Returns:
        Formatted timestamp string in user's local time
    """
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    
    # Convert to user's timezone
    user_tz = pytz.timezone(user_timezone)
    local_time = timestamp.astimezone(user_tz)
    
    return local_time.strftime('%Y-%m-%d %H:%M:%S %Z')


def convert_to_user_timezone(timestamp: datetime, user_timezone: str = 'Africa/Nairobi') -> datetime:
    """
    Convert UTC timestamp to user's timezone
    
    Args:
        timestamp: Datetime object (assumed to be in UTC)
        user_timezone: User's timezone
    
    Returns:
        Datetime object in user's timezone
    """
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    
    user_tz = pytz.timezone(user_timezone)
    return timestamp.astimezone(user_tz)


def get_current_time_in_timezone(user_timezone: str = 'Africa/Nairobi') -> datetime:
    """
    Get current time in user's timezone
    
    Args:
        user_timezone: User's timezone
    
    Returns:
        Current datetime in user's timezone
    """
    user_tz = pytz.timezone(user_timezone)
    return datetime.now(user_tz)


def format_relative_time(timestamp: datetime, user_timezone: str = 'Africa/Nairobi') -> str:
    """
    Format timestamp as relative time (e.g., "5 minutes ago")
    
    Args:
        timestamp: Datetime object
        user_timezone: User's timezone
    
    Returns:
        Relative time string
    """
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    
    now = get_current_time_in_timezone(user_timezone)
    user_time = convert_to_user_timezone(timestamp, user_timezone)
    
    diff = now - user_time
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"


def calculate_trend(data: List[float], window_size: int = 5) -> str:
    """
    Calculate trend direction for a series of values
    
    Args:
        data: List of numeric values
        window_size: Window size for trend calculation
    
    Returns:
        Trend direction: 'increasing', 'decreasing', or 'stable'
    """
    if len(data) < window_size:
        return 'insufficient_data'
    
    recent_data = data[-window_size:]
    trend_slope = np.polyfit(range(len(recent_data)), recent_data, 1)[0]
    
    if trend_slope > 0.5:
        return 'increasing'
    elif trend_slope < -0.5:
        return 'decreasing'
    else:
        return 'stable'


def create_sample_user_profile() -> Dict[str, Any]:
    """
    Create a sample user profile for testing
    
    Returns:
        Sample user profile dictionary
    """
    return {
        'user_id': 'sample_user_001',
        'name': 'Sample User',
        'age': 30,
        'gender': 'other',
        'height': 170,  # cm
        'weight': 70,   # kg
        'fitness_level': 'moderate',
        'medical_conditions': [],
        'created_at': datetime.now(timezone.utc),
        'preferences': {
            'alert_frequency': 'normal',
            'data_retention_days': 365,
            'share_data': False
        }
    }
