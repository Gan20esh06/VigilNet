"""
VigilNet Configuration Module

Centralized configuration for all system parameters.
"""

import os
import json
from typing import Dict, Any

# ────── ENVIRONMENT VARIABLES ──────────
# Set these in .env file or system environment

# Twilio Configuration (for mobile alerts)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE = os.getenv('TWILIO_PHONE', '')
ALERT_PHONE = os.getenv('ALERT_PHONE', '')

# GPU Configuration
USE_GPU = os.getenv('USE_GPU', 'true').lower() == 'true'
GPU_MEMORY_FRACTION = float(os.getenv('GPU_MEMORY_FRACTION', '0.8'))

# Audio Configuration
AUDIO_THRESHOLD = float(os.getenv('AUDIO_THRESHOLD', '0.008'))
AUDIO_DEVICE_INDEX = int(os.getenv('AUDIO_DEVICE_INDEX', '2'))

# Detection Configuration
PERSON_CONFIDENCE = float(os.getenv('PERSON_CONFIDENCE', '0.60'))
OBJECT_CONFIDENCE = float(os.getenv('OBJECT_CONFIDENCE', '0.75'))

# ────── SYSTEM CONFIGURATION ──────────

# Model Configuration
MODELS = {
    'person_detection': 'yolov8s.pt',  # Can use 'yolov8n.pt' for faster/lighter
    'object_detection': 'yolov8s.pt',
    'ensemble_model': None  # Optional: 'yolov8n.pt' for ensemble detection
}

# Detection Classes
DETECTION_CLASSES = {
    'person': 0,           # COCO class ID for person
    'cell phone': 67,      # COCO class ID for cell phone
    'laptop': 63,          # COCO class ID for laptop
    'book': 73             # COCO class ID for book
}

# Risk Scoring Weights
RISK_WEIGHTS = {
    'gaze': 0.40,          # Head pose/gaze attention (40%)
    'objects': 0.40,       # Suspicious objects (40%)
    'audio': 0.20          # Audio anomalies (20%)
}

# Confidence Thresholds (Dynamic, can be overridden)
CONFIDENCE_THRESHOLDS = {
    'person': 0.60,
    'cell phone': 0.80,
    'laptop': 0.75,
    'book': 0.70,
    'default': 0.65
}

# Violation Detection Thresholds
VIOLATION_THRESHOLDS = {
    'risk_score_high': 70,     # High risk
    'risk_score_medium': 40,   # Medium risk
    'consistency_frames': 5,   # Frames for consistency check
    'consistency_ratio': 0.80  # 80% of frames must show violation
}

# Alert Configuration
ALERT_CONFIG = {
    'enabled': True,
    'use_local_fallback': True,  # If Twilio unavailable
    'cooldown_seconds': 30,      # Minimum time between same-type alerts
    'enable_whatsapp': True,     # Send WhatsApp in addition to SMS
    'batch_report_enabled': True,
    'batch_report_interval': 3600  # Seconds (1 hour)
}

# Recording Configuration
RECORDING_CONFIG = {
    'enabled': True,
    'format': 'XVID',          # Video codec
    'fps': 10,                 # Frames per second
    'frame_width': 1280,       # Auto-detected, can override
    'frame_height': 720        # Auto-detected, can override
}

# Reporting Configuration
REPORTING_CONFIG = {
    'output_dir': 'reports',
    'generate_json': True,
    'generate_csv': True,
    'generate_html': True,
    'embed_images': True,
    'retention_days': 90       # Keep reports for 90 days
}

# GPU Benchmarking Configuration
BENCHMARK_CONFIG = {
    'enabled': False,          # Set to True to run benchmarks
    'num_frames': 100,
    'save_report': True,
    'compare_devices': True    # CPU vs GPU comparison
}

# Directories
DIRECTORIES = {
    'logs': 'logs',
    'recordings': 'recordings',
    'violations': 'violations',
    'reports': 'reports',
    'benchmarks': 'benchmarks',
    'models': 'models'
}

# Logging Configuration
LOG_CONFIG = {
    'console_verbose': True,
    'file_logging': True,
    'log_file': 'logs/system.log',
    'log_level': 'INFO'  # DEBUG, INFO, WARNING, ERROR
}

# UI/Display Configuration
DISPLAY_CONFIG = {
    'show_fps': True,
    'show_risk_scores': True,
    'show_confidence': True,
    'desk_zone_percent': 0.60,  # Zone line at 60% from top
    'font_scale': 0.5,
    'thickness': 2
}

# Audio Configuration Details
AUDIO_CONFIG = {
    'chunk': 2048,
    'format': 'paFloat32',
    'channels': 1,
    'rate': 16000,
    'device_index': AUDIO_DEVICE_INDEX,
    'threshold': AUDIO_THRESHOLD,
    'cooldown_frames': 60
}

# Session Configuration
SESSION_CONFIG = {
    'auto_session_id': True,    # Generate from timestamp
    'max_session_duration_hours': 4,
    'auto_report_on_end': True,
    'send_batch_alerts_on_end': True
}


def get_config() -> Dict[str, Any]:
    """Get complete configuration dictionary."""
    return {
        'models': MODELS,
        'detection_classes': DETECTION_CLASSES,
        'risk_weights': RISK_WEIGHTS,
        'confidence_thresholds': CONFIDENCE_THRESHOLDS,
        'violation_thresholds': VIOLATION_THRESHOLDS,
        'alert_config': ALERT_CONFIG,
        'recording_config': RECORDING_CONFIG,
        'reporting_config': REPORTING_CONFIG,
        'benchmark_config': BENCHMARK_CONFIG,
        'directories': DIRECTORIES,
        'log_config': LOG_CONFIG,
        'display_config': DISPLAY_CONFIG,
        'audio_config': AUDIO_CONFIG,
        'session_config': SESSION_CONFIG,
        'gpu_enabled': USE_GPU
    }


def load_config_from_file(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Failed to load config from {config_path}: {e}")
        print("Using default configuration")
        return get_config()


def save_config_to_file(config_path: str = 'config.json'):
    """Save current configuration to JSON file."""
    try:
        config = get_config()
        os.makedirs(os.path.dirname(config_path) if os.path.dirname(config_path) else '.', exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✓ Configuration saved to {config_path}")
    except Exception as e:
        print(f"✗ Failed to save configuration: {e}")


def print_config():
    """Print configuration to console."""
    config = get_config()
    print("\n" + "="*70)
    print("VigilNet CONFIGURATION")
    print("="*70)
    print(json.dumps(config, indent=2))
    print("="*70 + "\n")


if __name__ == "__main__":
    print_config()
