"""
Demo script for the Health Monitoring System
This script demonstrates the core functionality without requiring all dependencies
"""
import sys
import os
from datetime import datetime, timedelta, timezone
import random
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Try to import our modules
try:
    from utils.config import Config
    from utils.helpers import validate_health_data, calculate_health_score, generate_recommendations
    print("✓ Successfully imported utility modules")
except ImportError as e:
    print(f"✗ Could not import utilities: {e}")
    sys.exit(1)

def simulate_basic_health_data():
    """Simple simulation without external dependencies"""
    print("\n" + "="*50)
    print("HEALTH DATA SIMULATION DEMO")
    print("="*50)
    
    # Generate sample health readings
    readings = []
    base_time = datetime.now(timezone.utc)
    
    for i in range(10):
        # Simulate realistic health data
        heart_rate = random.uniform(60, 100) + random.gauss(0, 5)
        blood_oxygen = random.uniform(95, 99) + random.gauss(0, 1)
        
        # Occasionally add anomalies
        if random.random() < 0.2:  # 20% chance of anomaly
            if random.random() < 0.5:
                heart_rate += random.uniform(20, 40)  # High heart rate
            else:
                blood_oxygen -= random.uniform(5, 10)  # Low oxygen
        
        reading = {
            'timestamp': base_time + timedelta(minutes=i*5),
            'heart_rate': round(heart_rate, 1),
            'blood_oxygen': round(blood_oxygen, 1),
            'activity_level': random.choice(['low', 'moderate', 'high']),
            'user_id': 'demo_user_001'
        }
        
        readings.append(reading)
    
    return readings

def analyze_health_data(readings):
    """Analyze the generated health data"""
    print(f"\nAnalyzing {len(readings)} health readings...")
    print("-" * 40)
    
    anomalies = []
    normal_readings = []
    
    for i, reading in enumerate(readings):
        print(f"Reading {i+1}:")
        print(f"  Time: {reading['timestamp'].strftime('%H:%M')}")
        print(f"  Heart Rate: {reading['heart_rate']} BPM")
        print(f"  Blood Oxygen: {reading['blood_oxygen']}%")
        print(f"  Activity: {reading['activity_level']}")
        
        # Validate data
        if validate_health_data(reading):
            print("  ✓ Data valid")
            
            # Calculate health score
            score_data = calculate_health_score(
                reading['heart_rate'], 
                reading['blood_oxygen'], 
                reading['activity_level']
            )
            
            print(f"  Health Score: {score_data['score']}/100 ({score_data['status']})")
            
            # Check for anomalies
            if reading['heart_rate'] > 120 or reading['blood_oxygen'] < 90:
                anomalies.append({
                    'reading_index': i+1,
                    'timestamp': reading['timestamp'],
                    'heart_rate': reading['heart_rate'],
                    'blood_oxygen': reading['blood_oxygen'],
                    'issues': score_data['issues']
                })
                print("  ⚠️  ANOMALY DETECTED!")
            else:
                normal_readings.append(reading)
                print("  ✓ Normal reading")
        else:
            print("  ✗ Invalid data")
        
        print()
    
    return anomalies, normal_readings

def generate_health_report(readings, anomalies, normal_readings):
    """Generate a health report"""
    print("\n" + "="*50)
    print("HEALTH ANALYSIS REPORT")
    print("="*50)
    
    print(f"Total Readings: {len(readings)}")
    print(f"Normal Readings: {len(normal_readings)}")
    print(f"Anomalies Detected: {len(anomalies)}")
    print(f"Anomaly Rate: {len(anomalies)/len(readings)*100:.1f}%")
    
    if readings:
        hr_values = [r['heart_rate'] for r in readings]
        bo_values = [r['blood_oxygen'] for r in readings]
        
        print(f"\nHeart Rate Statistics:")
        print(f"  Average: {sum(hr_values)/len(hr_values):.1f} BPM")
        print(f"  Range: {min(hr_values):.1f} - {max(hr_values):.1f} BPM")
        
        print(f"\nBlood Oxygen Statistics:")
        print(f"  Average: {sum(bo_values)/len(bo_values):.1f}%")
        print(f"  Range: {min(bo_values):.1f} - {max(bo_values):.1f}%")
    
    if anomalies:
        print(f"\nAnomalies Detected:")
        for anomaly in anomalies:
            print(f"  Reading {anomaly['reading_index']} at {anomaly['timestamp'].strftime('%H:%M')}")
            print(f"    Heart Rate: {anomaly['heart_rate']} BPM")
            print(f"    Blood Oxygen: {anomaly['blood_oxygen']}%")
            if anomaly['issues']:
                print(f"    Issues: {', '.join(anomaly['issues'])}")
    
    # Generate recommendations
    if anomalies:
        print(f"\nRecommendations:")
        sample_reading = readings[-1]  # Use last reading
        recommendations = generate_recommendations(
            sample_reading['heart_rate'],
            sample_reading['blood_oxygen'],
            sample_reading['activity_level']
        )
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")

def test_configuration():
    """Test configuration loading"""
    print("\n" + "="*50)
    print("CONFIGURATION TEST")
    print("="*50)
    
    try:
        config = Config()
        print("✓ Configuration loaded successfully")
        print(f"  Heart Rate Normal Range: {config.HEART_RATE_NORMAL_MIN}-{config.HEART_RATE_NORMAL_MAX} BPM")
        print(f"  Blood Oxygen Normal Min: {config.BLOOD_OXYGEN_NORMAL_MIN}%")
        print(f"  Anomaly Threshold: {config.ANOMALY_THRESHOLD}")
        print(f"  Database URI: {config.SQLALCHEMY_DATABASE_URI}")
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def main():
    """Main demo function"""
    print("AI-Powered Health Monitoring System - Demo")
    print("="*50)
    
    # Test configuration
    if not test_configuration():
        return
    
    # Generate sample data
    print("\nGenerating sample health data...")
    readings = simulate_basic_health_data()
    
    # Analyze data
    anomalies, normal_readings = analyze_health_data(readings)
    
    # Generate report
    generate_health_report(readings, anomalies, normal_readings)
    
    print("\n" + "="*50)
    print("DEMO COMPLETED SUCCESSFULLY!")
    print("="*50)
    print("\nThis demo showed:")
    print("✓ Health data simulation")
    print("✓ Data validation")
    print("✓ Health score calculation")
    print("✓ Anomaly detection")
    print("✓ Health recommendations")
    print("✓ Report generation")
    
    print("\nNext Steps:")
    print("1. Install full dependencies: pip install -r requirements.txt")
    print("2. Run the web application: python src/web/app.py")
    print("3. Open browser to: http://localhost:5000")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()
