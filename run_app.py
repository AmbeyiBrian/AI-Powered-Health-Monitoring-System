"""
Flask application runner for Health Monitoring System
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from flask import Flask
    from src.utils.config import config
    from src.data.models import init_db
    from src.data.simulator import HealthDataSimulator, UserProfile
    from src.utils.helpers import setup_logging
    from datetime import datetime, timezone, timedelta
    import json

    # Setup logging
    logger = setup_logging('INFO')

    # Create Flask app
    app = Flask(__name__, 
                template_folder='src/web/templates',
                static_folder='src/web/static')

    # Configure app
    config_name = os.environ.get('FLASK_CONFIG', 'development')
    app.config.from_object(config[config_name])

    # Add JSON filter for templates
    def tojson_filter(obj):
        return json.dumps(obj)
    
    app.jinja_env.filters['tojson'] = tojson_filter

    # Initialize database
    with app.app_context():
        init_db(app)
        logger.info("Database initialized")

    # Import routes after app configuration
    from src.web.app import *

    if __name__ == '__main__':
        print("🚀 Starting AI-Powered Health Monitoring System")
        print("=" * 60)
        print(f"Server will start at: http://localhost:5000")
        print(f"Configuration: {config_name}")
        print("=" * 60)
        print("Available endpoints:")
        print("  GET  /                    - Main dashboard")
        print("  GET  /api/health_data     - Get health data")
        print("  POST /api/health_data     - Add health data")
        print("  POST /api/simulate_data   - Generate sample data")
        print("  POST /api/train_model     - Train AI model")
        print("  GET  /api/alerts          - Get alerts")
        print("=" * 60)
        print("Quick start:")
        print("1. Open http://localhost:5000 in your browser")
        print("2. Click 'Generate Data' to create sample health data")
        print("3. Click 'Train AI Model' to enable anomaly detection")
        print("4. View your health dashboard with real-time monitoring")
        print("=" * 60)
        
        app.run(debug=True, host='0.0.0.0', port=5000)

except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure all dependencies are installed:")
    print("pip install -r requirements.txt")
except Exception as e:
    print(f"❌ Application Error: {e}")
    import traceback
    traceback.print_exc()
