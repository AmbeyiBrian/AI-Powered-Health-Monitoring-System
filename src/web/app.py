"""
Flask Web Application for Health Monitoring System
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from datetime import datetime, timedelta, timezone
import os
import json
import logging
from typing import Dict, Any, List
import numpy as np

# Import our modules
from ..utils.config import config
from ..utils.helpers import (
    setup_logging, validate_health_data, calculate_health_score,
    generate_recommendations, format_timestamp, calculate_trend
)
from ..data.models import db, init_db, HealthData, Alert, create_health_data_entry, get_user_health_data
from ..data.simulator import HealthDataSimulator, UserProfile
from ..ml.anomaly_detection import create_health_anomaly_detector

# Initialize Flask app
app = Flask(__name__)

# Configure app
config_name = os.environ.get('FLASK_CONFIG', 'development')
app.config.from_object(config[config_name])

# Initialize extensions
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Load user by user_id for Flask-Login"""
    from ..data.models import User
    return User.query.filter_by(user_id=user_id).first()

# Register authentication blueprint
from ..auth.routes import auth_bp
app.register_blueprint(auth_bp)

# Setup logging
logger = setup_logging('INFO')

# Global variables for models and simulators
anomaly_detector = None
health_simulator = None


def create_app(config_name='development'):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize database
    init_db(app)
    
    return app


@app.route('/')
@app.route('/dashboard')
def dashboard():
    """Main dashboard page - redirects to login if not authenticated"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    # Redirect to user-specific dashboard
    return redirect(url_for('user_dashboard', user_id=current_user.user_id))


@app.route('/dashboard/<user_id>')
@login_required
def user_dashboard(user_id):
    """User-specific dashboard page"""
    try:
        # Import here to avoid circular imports
        from ..data.models import User
        
        # Security check: users can only view their own dashboard
        if current_user.user_id != user_id:
            return redirect(url_for('user_dashboard', user_id=current_user.user_id))
        
        user = User.query.filter_by(user_id=user_id).first()
        if not user:
            return render_template('error.html', message="User not found")
        
        # Get recent health data
        recent_data = get_user_health_data(user_id, limit=100)
        
        # Get current health status
        current_status = get_current_health_status(user_id)
        
        # Get recent alerts
        recent_alerts = Alert.query.filter_by(user_id=user_id)\
                                 .order_by(Alert.created_at.desc())\
                                 .limit(5).all()
        
        # Calculate health trends
        trends = calculate_health_trends(recent_data)
        
        # Prepare chart data
        chart_data = prepare_chart_data(recent_data, user.timezone or 'Africa/Nairobi')
        
        return render_template('dashboard.html',
                             user=user,
                             current_status=current_status,
                             recent_alerts=recent_alerts,
                             trends=trends,
                             chart_data=chart_data)
    
    except Exception as e:
        logger.error(f"Error in dashboard: {str(e)}")
        return render_template('error.html', message="Error loading dashboard")


@app.route('/api/health_data', methods=['GET'])
def get_health_data():
    """API endpoint to get health data"""
    try:
        user_id = request.args.get('user_id', 'sample_user_001')
        limit = int(request.args.get('limit', 100))
        
        # Get user's timezone
        from ..data.models import User
        user = User.query.filter_by(user_id=user_id).first()
        user_timezone = user.timezone if user else 'Africa/Nairobi'
        
        health_data = get_user_health_data(user_id, limit)
        
        # Convert to JSON with timezone-aware timestamps
        data = [record.to_dict_with_timezone(user_timezone) for record in health_data]
        
        return jsonify({
            'status': 'success',
            'data': convert_numpy_types(data),
            'count': len(data),
            'user_timezone': user_timezone
        })
    
    except Exception as e:
        logger.error(f"Error getting health data: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/health_data', methods=['POST'])
def add_health_data():
    """API endpoint to add new health data"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not validate_health_data(data):
            return jsonify({'status': 'error', 'message': 'Invalid health data'}), 400
        
        user_id = data.get('user_id', 'sample_user_001')
        
        # Create health data entry
        health_entry = create_health_data_entry(user_id, data)
        
        # Calculate health score
        health_score_data = calculate_health_score(
            data['heart_rate'], 
            data['blood_oxygen'], 
            data.get('activity_level', 'moderate')
        )
        
        # Update health entry with score
        health_entry.health_score = health_score_data['score']
        db.session.commit()
        
        # Check for anomalies
        check_for_anomalies(health_entry)
        
        return jsonify({
            'status': 'success',
            'message': 'Health data added successfully',
            'health_score': convert_numpy_types(health_score_data)
        })
    
    except Exception as e:
        logger.error(f"Error adding health data: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/simulate_data', methods=['POST'])
@login_required
def simulate_health_data():
    """API endpoint to simulate health data"""
    try:
        # Import here to avoid circular imports
        from ..data.models import User
        
        data = request.get_json()
        # Always use current user's ID for security
        user_id = current_user.user_id
        
        hours = int(data.get('hours', 1))
        
        # Get user profile
        user = User.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        # Create user profile for simulator
        user_profile = UserProfile(
            user_id=user_id,
            age=user.age or 30,
            gender=user.gender or 'other',
            fitness_level=user.fitness_level or 'moderate',
            weight=user.weight or 70.0,
            height=user.height or 170.0
        )
        
        # Create simulator and generate data
        simulator = HealthDataSimulator(user_profile)
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        simulated_data = simulator.generate_time_series(
            start_time, 
            duration_hours=hours, 
            interval_minutes=5
        )
        
        # Save to database
        saved_count = 0
        for entry in simulated_data:
            try:
                create_health_data_entry(user_id, entry)
                saved_count += 1
            except Exception as e:
                logger.warning(f"Error saving simulated data entry: {str(e)}")
        
        return jsonify({
            'status': 'success',
            'message': f'Generated and saved {saved_count} health data entries',
            'generated_count': convert_numpy_types(len(simulated_data)),
            'saved_count': convert_numpy_types(saved_count)
        })
    
    except Exception as e:
        logger.error(f"Error simulating health data: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/train_model', methods=['POST'])
def train_anomaly_model():
    """API endpoint to train anomaly detection model"""
    global anomaly_detector
    
    try:
        data = request.get_json()
        # Always use current user's ID for security
        user_id = current_user.user_id
        model_type = data.get('model_type', 'isolation_forest')
        
        # Get training data
        health_data = get_user_health_data(user_id, limit=1000)
        
        if len(health_data) < 50:
            return jsonify({
                'status': 'error', 
                'message': 'Insufficient data for training (minimum 50 records required)'
            }), 400
        
        # Convert to DataFrame
        import pandas as pd
        df_data = [record.to_dict() for record in health_data]
        df = pd.DataFrame(df_data)
        
        # Create and train anomaly detector
        anomaly_detector = create_health_anomaly_detector(method=model_type)
        training_results = anomaly_detector.train(df)
        
        # Update existing records with anomaly predictions
        predictions = anomaly_detector.predict(df)
        for i, record in enumerate(health_data):
            record.is_anomaly = (predictions[i] == 0)
            record.anomaly_score = float(anomaly_detector.predict_proba(df.iloc[i:i+1])[0])
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Model trained successfully',
            'training_results': convert_numpy_types(training_results)
        })
    
    except Exception as e:
        logger.error(f"Error training model: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/alerts')
def get_alerts():
    """API endpoint to get user alerts"""
    try:
        user_id = request.args.get('user_id', 'sample_user_001')
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        query = Alert.query.filter_by(user_id=user_id)
        if unread_only:
            query = query.filter_by(is_read=False)
        
        alerts = query.order_by(Alert.created_at.desc()).all()
        
        return jsonify({
            'status': 'success',
            'alerts': [alert.to_dict() for alert in alerts],
            'count': len(alerts)
        })
    
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


def get_current_health_status(user_id: str) -> Dict[str, Any]:
    """Get current health status for a user"""
    try:
        # Get most recent health data
        latest_data = HealthData.query.filter_by(user_id=user_id)\
                                    .order_by(HealthData.timestamp.desc())\
                                    .first()
        
        if not latest_data:
            return {
                'status': 'No data available',
                'heart_rate': 0,
                'blood_oxygen': 0,
                'health_score': 0,
                'last_updated': None
            }
        
        # Calculate health score if not available
        if latest_data.health_score is None:
            health_score_data = calculate_health_score(
                latest_data.heart_rate,
                latest_data.blood_oxygen,
                latest_data.activity_level or 'moderate'
            )
            latest_data.health_score = health_score_data['score']
            db.session.commit()
        
        return {
            'status': 'Normal' if not latest_data.is_anomaly else 'Anomaly Detected',
            'heart_rate': latest_data.heart_rate,
            'blood_oxygen': latest_data.blood_oxygen,
            'activity_level': latest_data.activity_level,
            'health_score': latest_data.health_score,
            'last_updated': format_timestamp(latest_data.timestamp, current_user.timezone or 'Africa/Nairobi'),
            'is_anomaly': latest_data.is_anomaly
        }
    
    except Exception as e:
        logger.error(f"Error getting current health status: {str(e)}")
        return {'status': 'Error', 'message': str(e)}


def calculate_health_trends(health_data: List[HealthData]) -> Dict[str, str]:
    """Calculate health trends from recent data"""
    if len(health_data) < 5:
        return {'heart_rate': 'insufficient_data', 'blood_oxygen': 'insufficient_data'}
    
    # Extract values
    heart_rates = [record.heart_rate for record in health_data]
    blood_oxygen = [record.blood_oxygen for record in health_data]
    
    # Calculate trends
    hr_trend = calculate_trend(heart_rates)
    bo_trend = calculate_trend(blood_oxygen)
    
    return {
        'heart_rate': hr_trend,
        'blood_oxygen': bo_trend
    }


def prepare_chart_data(health_data: List[HealthData], user_timezone: str = 'Africa/Nairobi') -> Dict[str, Any]:
    """Prepare data for charts"""
    if not health_data:
        return {'labels': [], 'heart_rate': [], 'blood_oxygen': []}
    
    # Sort by timestamp
    sorted_data = sorted(health_data, key=lambda x: x.timestamp)
    
    # Take last 24 hours of data
    labels = [format_timestamp(record.timestamp, user_timezone) for record in sorted_data[-24:]]
    heart_rates = [record.heart_rate for record in sorted_data[-24:]]
    blood_oxygen = [record.blood_oxygen for record in sorted_data[-24:]]
    
    return {
        'labels': labels,
        'heart_rate': heart_rates,
        'blood_oxygen': blood_oxygen
    }


def check_for_anomalies(health_entry: HealthData):
    """Check for anomalies in health data and create alerts"""
    global anomaly_detector
    
    try:
        # Simple rule-based anomaly detection if ML model not available
        if anomaly_detector is None:
            is_anomaly = False
            alert_messages = []
            
            # Heart rate checks
            if health_entry.heart_rate > 120:
                is_anomaly = True
                alert_messages.append(f"High heart rate detected: {health_entry.heart_rate} BPM")
            elif health_entry.heart_rate < 50:
                is_anomaly = True
                alert_messages.append(f"Low heart rate detected: {health_entry.heart_rate} BPM")
            
            # Blood oxygen checks
            if health_entry.blood_oxygen < 90:
                is_anomaly = True
                alert_messages.append(f"Low blood oxygen detected: {health_entry.blood_oxygen}%")
            
            # Update health entry
            health_entry.is_anomaly = is_anomaly
            
            # Create alert if anomaly detected
            if is_anomaly:
                alert_data = {
                    'alert_type': 'anomaly',
                    'severity': 'high' if health_entry.blood_oxygen < 90 else 'medium',
                    'title': 'Health Anomaly Detected',
                    'message': '; '.join(alert_messages),
                    'health_data_id': health_entry.id,
                    'recommendations': json.dumps(generate_recommendations(
                        health_entry.heart_rate,
                        health_entry.blood_oxygen,
                        health_entry.activity_level or 'moderate'
                    ))
                }
                
                from ..data.models import create_alert
                create_alert(health_entry.user_id, alert_data)
        
        else:
            # Use ML model for anomaly detection
            import pandas as pd
            df = pd.DataFrame([health_entry.to_dict()])
            
            prediction = anomaly_detector.predict(df)[0]
            anomaly_score = anomaly_detector.predict_proba(df)[0]
            
            health_entry.is_anomaly = (prediction == 0)
            health_entry.anomaly_score = float(anomaly_score)
            
            # Create alert if anomaly detected
            if prediction == 0:
                alert_data = {
                    'alert_type': 'anomaly',
                    'severity': 'high' if anomaly_score < 0.3 else 'medium',
                    'title': 'AI Anomaly Detection Alert',
                    'message': f'Anomaly detected in health data (score: {anomaly_score:.2f})',
                    'health_data_id': health_entry.id
                }
                
                from ..data.models import create_alert
                create_alert(health_entry.user_id, alert_data)
        
        db.session.commit()
        
    except Exception as e:
        logger.error(f"Error checking for anomalies: {str(e)}")


@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', message="Page not found"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', message="Internal server error"), 500


@app.route('/login-success')
@login_required
def login_success():
    """Simple login success page for testing"""
    return f"<h1>Login Successful!</h1><p>Welcome {current_user.name}!</p><p>User ID: {current_user.user_id}</p><a href='/dashboard'>Go to Dashboard</a>"


def convert_numpy_types(obj):
    """Convert NumPy types to Python native types for JSON serialization"""
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj


if __name__ == '__main__':
    with app.app_context():
        init_db(app)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
