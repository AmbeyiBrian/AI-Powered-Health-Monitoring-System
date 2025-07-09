"""
Basic tests for the Health Monitoring System
"""
import sys
import os
import unittest
from datetime import datetime, timezone, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from data.simulator import HealthDataSimulator, UserProfile
    from utils.helpers import validate_health_data, calculate_health_score
    from utils.config import Config
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed")


class TestHealthDataSimulator(unittest.TestCase):
    """Test the health data simulator"""
    
    def setUp(self):
        self.user_profile = UserProfile(
            user_id='test_user',
            age=30,
            gender='other',
            fitness_level='moderate',
            weight=70.0,
            height=170.0
        )
        self.simulator = HealthDataSimulator(self.user_profile)
    
    def test_generate_single_reading(self):
        """Test generating a single health reading"""
        reading = self.simulator.generate_single_reading()
        
        # Check that all required fields are present
        required_fields = ['timestamp', 'heart_rate', 'blood_oxygen', 'activity_level', 'user_id']
        for field in required_fields:
            self.assertIn(field, reading)
        
        # Check value ranges
        self.assertGreaterEqual(reading['heart_rate'], 30)
        self.assertLessEqual(reading['heart_rate'], 200)
        self.assertGreaterEqual(reading['blood_oxygen'], 70)
        self.assertLessEqual(reading['blood_oxygen'], 100)
    
    def test_generate_time_series(self):
        """Test generating time series data"""
        start_time = datetime.now(timezone.utc)
        data = self.simulator.generate_time_series(start_time, duration_hours=1, interval_minutes=10)
        
        # Should generate 6 readings (60 minutes / 10 minute intervals)
        self.assertEqual(len(data), 6)
        
        # Check that timestamps are in order
        timestamps = [reading['timestamp'] for reading in data]
        self.assertEqual(timestamps, sorted(timestamps))


class TestHelperFunctions(unittest.TestCase):
    """Test utility functions"""
    
    def test_validate_health_data_valid(self):
        """Test validation with valid data"""
        valid_data = {
            'timestamp': datetime.now(timezone.utc),
            'heart_rate': 75.0,
            'blood_oxygen': 98.0,
            'activity_level': 'moderate'
        }
        self.assertTrue(validate_health_data(valid_data))
    
    def test_validate_health_data_invalid(self):
        """Test validation with invalid data"""
        # Missing required field
        invalid_data1 = {
            'timestamp': datetime.now(timezone.utc),
            'blood_oxygen': 98.0
        }
        self.assertFalse(validate_health_data(invalid_data1))
        
        # Invalid heart rate
        invalid_data2 = {
            'timestamp': datetime.now(timezone.utc),
            'heart_rate': 300.0,  # Too high
            'blood_oxygen': 98.0
        }
        self.assertFalse(validate_health_data(invalid_data2))
    
    def test_calculate_health_score(self):
        """Test health score calculation"""
        score_data = calculate_health_score(75, 98, 'moderate')
        
        self.assertIn('score', score_data)
        self.assertIn('status', score_data)
        self.assertIn('recommendations', score_data)
        
        self.assertGreaterEqual(score_data['score'], 0)
        self.assertLessEqual(score_data['score'], 100)


class TestConfiguration(unittest.TestCase):
    """Test configuration settings"""
    
    def test_config_values(self):
        """Test that configuration has required values"""
        config = Config()
        
        # Check that essential config values exist
        self.assertIsNotNone(config.SECRET_KEY)
        self.assertIsNotNone(config.SQLALCHEMY_DATABASE_URI)
        self.assertIsInstance(config.HEART_RATE_NORMAL_MIN, int)
        self.assertIsInstance(config.BLOOD_OXYGEN_NORMAL_MIN, int)


def run_basic_tests():
    """Run basic tests without external dependencies"""
    print("Running basic health monitoring system tests...")
    
    # Test 1: User Profile Creation
    print("\nTest 1: User Profile Creation")
    try:
        user = UserProfile(
            user_id='test_001',
            age=25,
            gender='female',
            fitness_level='high',
            weight=60.0,
            height=165.0
        )
        print(f"✓ Created user profile: {user.user_id}")
    except Exception as e:
        print(f"✗ Failed to create user profile: {e}")
    
    # Test 2: Data Validation
    print("\nTest 2: Data Validation")
    try:
        valid_data = {
            'timestamp': datetime.now(timezone.utc),
            'heart_rate': 75,
            'blood_oxygen': 98
        }
        is_valid = validate_health_data(valid_data)
        print(f"✓ Data validation result: {is_valid}")
    except Exception as e:
        print(f"✗ Data validation failed: {e}")
    
    # Test 3: Health Score Calculation
    print("\nTest 3: Health Score Calculation")
    try:
        score_result = calculate_health_score(75, 98, 'moderate')
        print(f"✓ Health score: {score_result['score']}/100 ({score_result['status']})")
        print(f"  Recommendations: {len(score_result['recommendations'])} items")
    except Exception as e:
        print(f"✗ Health score calculation failed: {e}")
    
    # Test 4: Configuration
    print("\nTest 4: Configuration Loading")
    try:
        config = Config()
        print(f"✓ Config loaded - HR range: {config.HEART_RATE_NORMAL_MIN}-{config.HEART_RATE_NORMAL_MAX}")
        print(f"  Blood oxygen min: {config.BLOOD_OXYGEN_NORMAL_MIN}%")
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
    
    print("\n" + "="*50)
    print("Basic tests completed!")
    print("To run full tests with ML dependencies, install requirements.txt first.")


if __name__ == '__main__':
    # Run basic tests first
    run_basic_tests()
    
    # Try to run unittest if possible
    try:
        print("\n" + "="*50)
        print("Running unittest suite...")
        unittest.main(verbosity=2, exit=False)
    except Exception as e:
        print(f"Unittest failed (likely due to missing dependencies): {e}")
        print("Install dependencies with: pip install -r requirements.txt")
