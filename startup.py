#!/usr/bin/env python3
"""
Startup script for the Health Monitoring System
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("✗ Failed to install dependencies")
        sys.exit(1)

def run_tests():
    """Run basic tests"""
    print("Running basic tests...")
    try:
        subprocess.run([sys.executable, "tests/test_basic.py"], check=True)
        print("✓ Basic tests passed")
    except subprocess.CalledProcessError:
        print("✗ Some tests failed")

def setup_environment():
    """Set up environment variables"""
    os.environ['PYTHONPATH'] = os.path.abspath('.')
    os.environ['FLASK_APP'] = 'src.web.app:app'
    os.environ['FLASK_ENV'] = 'development'

def run_app():
    """Run the Flask application"""
    print("Starting Health Monitoring System...")
    print("Open your browser to: http://localhost:5000")
    print("Press Ctrl+C to stop the application")
    
    try:
        # Change to the project directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Run the application
        subprocess.run([sys.executable, "src/web/app.py"])
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        print(f"Error running application: {e}")
        sys.exit(1)

def generate_sample_data():
    """Generate sample data for testing"""
    print("Generating sample data...")
    # This would be implemented to create sample data
    print("Sample data generation would be implemented here")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Health Monitoring System Startup Script')
    parser.add_argument('--install-deps', action='store_true', help='Install dependencies')
    parser.add_argument('--test', action='store_true', help='Run tests')
    parser.add_argument('--run', action='store_true', help='Run the application')
    parser.add_argument('--setup', action='store_true', help='Full setup (install deps, test, run)')
    parser.add_argument('--generate-data', action='store_true', help='Generate sample data')
    
    args = parser.parse_args()
    
    # Check Python version
    check_python_version()
    
    # Set up environment
    setup_environment()
    
    if args.install_deps or args.setup:
        install_dependencies()
    
    if args.test or args.setup:
        run_tests()
    
    if args.generate_data:
        generate_sample_data()
    
    if args.run or args.setup:
        run_app()
    
    if not any(vars(args).values()):
        print("Health Monitoring System Startup Script")
        print("======================================")
        print()
        print("Usage:")
        print("  python startup.py --setup         # Full setup and run")
        print("  python startup.py --install-deps  # Install dependencies only")
        print("  python startup.py --test          # Run tests only")
        print("  python startup.py --run           # Run application only")
        print("  python startup.py --generate-data # Generate sample data")
        print()
        print("For first time setup, use: python startup.py --setup")

if __name__ == '__main__':
    main()
