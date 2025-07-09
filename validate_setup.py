"""
Quick validation script for the Health Monitoring System
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("🏥 AI-Powered Health Monitoring System")
    print("=" * 60)
    
    # Test 1: Basic imports
    try:
        from src.utils.config import config
        from src.utils.helpers import validate_health_data, calculate_health_score
        print("✓ Core utilities imported successfully")
    except Exception as e:
        print(f"❌ Core utilities import failed: {e}")
        return False
    
    # Test 2: Data simulation
    try:
        from src.data.simulator import HealthDataSimulator, UserProfile
        
        user = UserProfile(
            user_id='test_user',
            age=30,
            gender='other',
            fitness_level='moderate',
            weight=70.0,
            height=170.0
        )
        
        simulator = HealthDataSimulator(user)
        sample_data = simulator.generate_single_reading()
        
        print("✓ Data simulation working")
        print(f"  Sample: HR={sample_data['heart_rate']:.1f} BPM, SpO2={sample_data['blood_oxygen']:.1f}%")
        
    except Exception as e:
        print(f"❌ Data simulation failed: {e}")
        return False
    
    # Test 3: Health scoring
    try:
        health_score = calculate_health_score(75, 98, 'moderate')
        print("✓ Health scoring working")
        print(f"  Score: {health_score['score']}/100 ({health_score['status']})")
        
    except Exception as e:
        print(f"❌ Health scoring failed: {e}")
        return False
    
    # Test 4: Database models
    try:
        from src.data.models import User, HealthData, Alert
        print("✓ Database models imported successfully")
        
    except Exception as e:
        print(f"❌ Database models failed: {e}")
        return False
    
    # Test 5: Configuration
    try:
        dev_config = config['development']()
        print("✓ Configuration loaded successfully")
        print(f"  Database: {dev_config.SQLALCHEMY_DATABASE_URI}")
        
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("\nThe Health Monitoring System is ready to use!")
    print("\nTo start the web application:")
    print("1. Run: python run_app.py")
    print("2. Open: http://localhost:5000")
    print("3. Generate some sample data")
    print("4. Train the AI model")
    print("5. Monitor your health dashboard!")
    print("=" * 60)
    
    # Show project structure
    print("\n📁 Project Structure:")
    print("├── src/")
    print("│   ├── data/          # Data models, simulation, preprocessing")
    print("│   ├── ml/            # Machine learning models")
    print("│   ├── web/           # Flask web application")
    print("│   └── utils/         # Utilities and configuration")
    print("├── tests/             # Test files")
    print("├── requirements.txt   # Python dependencies")
    print("├── run_app.py        # Application runner")
    print("└── demo.py           # Demo script")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Setup validation failed. Please check the errors above.")
        sys.exit(1)
