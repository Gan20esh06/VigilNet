#!/usr/bin/env python3
"""
VigilNet Enhanced - Quick Start Guide
Run this script to set up and test the enhanced system
"""

import os
import sys
import subprocess
from pathlib import Path


def print_banner():
    print("\n" + "="*70)
    print("  VigilNet ENHANCED - Quick Start Setup")
    print("="*70 + "\n")


def check_python():
    """Check Python version."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("✗ Python 3.10+ required")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def install_dependencies():
    """Install required packages."""
    print("\nInstalling dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed")
        return True
    except Exception as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False


def create_env_file():
    """Create .env file if it doesn't exist."""
    if os.path.exists(".env"):
        print("✓ .env file exists")
        return True
    
    if not os.path.exists(".env.example"):
        print("✗ .env.example not found")
        return False
    
    print("\nCreating .env file...")
    try:
        with open(".env.example", "r") as src:
            with open(".env", "w") as dst:
                dst.write(src.read())
        print("✓ .env file created from .env.example")
        print("  ⚠️  Edit .env to add your Twilio credentials")
        return True
    except Exception as e:
        print(f"✗ Failed to create .env: {e}")
        return False


def create_directories():
    """Create required directories."""
    print("\nCreating directories...")
    directories = ["logs", "recordings", "violations", "reports", "benchmarks", "models"]
    for dir_name in directories:
        os.makedirs(dir_name, exist_ok=True)
    print(f"✓ Created directories: {', '.join(directories)}")


def check_gpu():
    """Check for GPU availability."""
    print("\nChecking GPU availability...")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✓ GPU Available: {torch.cuda.get_device_name(0)}")
            print(f"  CUDA Version: {torch.version.cuda}")
            return True
        else:
            print("ℹ GPU not available - will use CPU")
            print("  (Optional: Install CUDA for 5-15x speedup)")
            return False
    except Exception as e:
        print(f"⚠️  Could not check GPU: {e}")
        return False


def test_camera():
    """Test camera access."""
    print("\nTesting camera...")
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                h, w = frame.shape[:2]
                print(f"✓ Camera OK: {w}x{h}")
                cap.release()
                return True
        print("✗ Camera not accessible")
        cap.release()
        return False
    except Exception as e:
        print(f"✗ Camera test failed: {e}")
        return False


def test_imports():
    """Test critical imports."""
    print("\nTesting imports...")
    try:
        from ultralytics import YOLO
        print("✓ YOLO (ultralytics)")
        
        import cv2
        print("✓ OpenCV")
        
        import mediapipe
        print("✓ MediaPipe")
        
        import torch
        print("✓ PyTorch")
        
        try:
            from twilio.rest import Client
            print("✓ Twilio")
        except ImportError:
            print("⚠️  Twilio not installed (optional - install for mobile alerts)")
        
        return True
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False


def print_next_steps():
    """Print next steps."""
    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    print("""
1. Configure Twilio (optional):
   - Edit .env with your Twilio credentials
   - Get credentials from https://www.twilio.com/

2. Run the enhanced system:
   python main_enhanced.py

3. Keyboard controls during execution:
   - Q: Quit
   - R: Reset tracker
   - B: Run GPU benchmark
   - P: Print configuration

4. View reports after session:
   - JSON: reports/report_SESSION_*.json
   - CSV: reports/report_SESSION_*.csv
   - HTML: reports/report_SESSION_*.html

5. Check documentation:
   - Read ENHANCEMENTS.md for detailed guide
   - View modules/architecture.py for system design

""")
    print("="*70 + "\n")


def main():
    """Run setup."""
    print_banner()
    
    # Checks
    if not check_python():
        return False
    
    if not test_imports():
        print("\nAttempting to install dependencies...")
        if not install_dependencies():
            return False
        if not test_imports():
            return False
    
    create_directories()
    create_env_file()
    check_gpu()
    test_camera()
    
    print_next_steps()
    
    print("✓ Setup complete! Ready to run VigilNet Enhanced")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
