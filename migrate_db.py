#!/usr/bin/env python3
"""
Database migration script to add authentication tables
"""
import sys
import os
import shutil
import secrets
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.web.app import app
from src.data.models import db, User, SensorDevice
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Create new authentication tables and migrate existing data"""
    with app.app_context():
        # Get database paths
        db_path = 'health_monitoring.db'
        dev_db_path = 'health_monitoring_dev.db'
        backup_path = f'health_monitoring_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        
        # Remove any existing database files to start completely fresh
        for db_file in [db_path, dev_db_path]:
            if os.path.exists(db_file):
                logger.info(f"Backing up existing database {db_file} to {backup_path}")
                if not os.path.exists(backup_path):  # Only backup the first one found
                    shutil.copy2(db_file, backup_path)
                logger.info(f"Removing old database file: {db_file}")
                os.remove(db_file)
        
        # Drop all existing tables to ensure clean slate
        logger.info("Dropping all existing tables...")
        db.drop_all()
        
        # Create all tables with new schema
        logger.info("Creating new database with authentication tables...")
        db.create_all()
        
        # Create sample user account
        logger.info("Creating sample user account...")
        try:
            sample_user = User(
                user_id='sample_user_001',
                username='testuser',
                email='demo@healthmonitor.com',
                name='Demo User',
                age=30,
                height=175.0,
                weight=70.0,
                fitness_level='moderate',
                timezone='Africa/Nairobi'
            )
            sample_user.set_password('demo123')  # Change this in production!
            
            db.session.add(sample_user)
            db.session.flush()  # Get the ID without committing
            
            logger.info(f"Sample user created:")
            logger.info(f"  Username: testuser")
            logger.info(f"  Email: demo@healthmonitor.com")
            logger.info(f"  Password: demo123")
            logger.info(f"  User ID: {sample_user.user_id}")
            
            # Create a sample device
            sample_device = SensorDevice(
                user_id=sample_user.user_id,
                device_name='Demo Smartwatch',
                device_type='smartwatch',
                device_model='Apple Watch Series 9',
                api_key=secrets.token_urlsafe(32),
                is_active=True
            )
            
            db.session.add(sample_device)
            db.session.commit()
            
            logger.info(f"Sample device created: {sample_device.device_name}")
            logger.info(f"  API Key: {sample_device.api_key}")
            
        except Exception as e:
            logger.error(f"Error creating sample user: {str(e)}")
            db.session.rollback()
        
        logger.info("Database migration completed successfully!")

if __name__ == "__main__":
    migrate_database()
